import os

from gtmcore.mitmproxy.mitmproxy import CURRENT_MITMPROXY_TAG
from typing import (Dict, List, Optional)
import time
import re
import io
import json
import pandas

from mitmproxy import io as mitmio
from mitmproxy.exceptions import FlowReadException

from PIL import Image
import zlib
import base64

import redis

from gtmcore.activity.processors.processor import ExecutionData
from gtmcore.configuration import get_docker_client
from gtmcore.activity.monitors.devenv import DevEnvMonitor
from gtmcore.activity.monitors.activity import ActivityMonitor

from gtmcore.activity.processors.core import GenericFileChangeProcessor, ActivityShowBasicProcessor
from gtmcore.activity import ActivityType
from gtmcore.activity.processors.rserver import (RStudioServerCodeProcessor,
                                                 RStudioServerPlaintextProcessor,
                                                 RStudioServerImageExtractorProcessor)
from gtmcore.dispatcher import Dispatcher, jobs
from gtmcore.logging import LMLogger

logger = LMLogger.get_logger()


class RServerMonitor(DevEnvMonitor):
    """Class to monitor RStudio-Server for the need to start Activity Monitor Instances"""

    def __init__(self, log_file_dir="/mnt/share/mitmproxy") -> None:
        """Set the directory of logfiles"""
        self.log_file_dir = log_file_dir

    @staticmethod
    def get_dev_env_name() -> List[str]:
        """Method to return a list of names of the development environments that this class interfaces with.
        Should be the value used in the `name` attribute of the Dev Env Environment Component"""
        return ["rstudio"]

    def get_log_file_ids(self) -> List[str]:
        """Return a list of the current mitm dump files in the shared directory.

            Returns: List of strs with proxy id.
        """
        retlist = []
        for fname in os.listdir(self.log_file_dir):
            m = re.match(r"([\w]+).rserver.dump", fname)
            if m:
                retlist.append(m[1])
        return retlist

    def get_running_proxies(self) -> List[str]:
        """Return a list of the running gmitmproxy

            Returns: List of strs with proxy id.
        """
        client = get_docker_client()
        clist = client.containers.list(filters={'ancestor': 'gigantum/mitmproxy_proxy:' + CURRENT_MITMPROXY_TAG})
        retlist = []
        for cont in clist:
            # container name is gmitmproxy.<uuid-style key>
            _, container_key = cont.name.split('.')
            retlist.append(container_key)
        return retlist

    def get_activity_monitors(self, key: str, redis_conn: redis.Redis) -> List[str]:
        """Return a list of the current activity monitors

            Returns: List of strs with proxy id.
        """
        # Get list of active Activity Monitor Instances from redis
        activity_monitors = redis_conn.keys('{}:activity_monitor:*'.format(key))
        activity_monitors = [x.decode('utf-8') for x in activity_monitors]
        retlist = []
        try:
            for am in activity_monitors:
                logfid = redis_conn.hget(am, "logfile_id").decode()
                if logfid:
                    retlist.append(logfid)
        # decode throws error on unset values.  not sure how to check RB
        except Exception as e:
            pass
        return retlist

    def run(self, key: str, database=1) -> None:
        """Method called in a periodically scheduled async worker that should check the dev env and manage Activity
        Monitor Instances as needed Args:
            key(str): The unique string used as the key in redis to track this DevEnvMonitor instance
        """
        redis_conn = redis.Redis(db=database)

        # Get a list of running activity monitors
        activity_monitors = self.get_activity_monitors(key, redis_conn)

        # Get author info
        # RB this is not populated until a labbook is started why running?
        author_name = redis_conn.hget(key, "author_name").decode()
        author_email = redis_conn.hget(key, "author_email").decode()

        # Get a list of active mitm_monitors from docker
        running_proxies = self.get_running_proxies()

        # Get a list of log files
        log_file_ids = self.get_log_file_ids()

        # check for exited instances
        for am in activity_monitors:
            if am not in running_proxies:
                # Kernel isn't running anymore. Clean up by setting run flag to `False` so worker exits
                activity_monitor_key = f'{key}:activity_monitor:{am}'
                redis_conn.hset(activity_monitor_key, 'run', False)
                logger.info(f"Detected exited RStudio Server project. Stopping monitoring for {activity_monitor_key}")

        for logfid in log_file_ids:
            # yes logfile, no mitmkernel -> exited kernel delete file
            if logfid not in running_proxies:
                logger.info(f"Detected defunct RStudio-Server log. Deleting log {logfid}")
                os.remove(f"/mnt/share/mitmproxy/{logfid}.rserver.dump")

            elif logfid not in activity_monitors:
                # Monitor rserver
                activity_monitor_key = f'{key}:activity_monitor:{logfid}'

                # Start new Activity Monitor
                _, user, owner, labbook_name, dev_env_name = key.split(':')

                args = {"module_name": "gtmcore.activity.monitors.monitor_rserver",
                        "class_name": "RStudioServerMonitor",
                        "user": user,
                        "owner": owner,
                        "labbook_name": labbook_name,
                        "monitor_key": activity_monitor_key,
                        "author_name": author_name,
                        "author_email": author_email,
                        # TODO DC: logfid *could* go in here... but probably a bigger refactor is needed
                        # Also captured in https://github.com/gigantum/gigantum-client/issues/434
                        "session_metadata": None}

                d = Dispatcher()
                process_id = d.dispatch_task(jobs.start_and_run_activity_monitor, kwargs=args, persist=True)
                logger.info(f"Started RStudio Server Notebook Activity Monitor: Process {process_id}")

                # Update redis
                redis_conn.hset(activity_monitor_key, "dev_env_monitor", key)
                redis_conn.hset(activity_monitor_key, "process_id", process_id)
                redis_conn.hset(activity_monitor_key, "logfile_id", logfid)
                redis_conn.hset(activity_monitor_key, "run", True)


class RStudioServerMonitor(ActivityMonitor):
    """Class to monitor an rstudio server for activity to be processed."""

    def __init__(self, user: str, owner: str, labbook_name: str, monitor_key: str, config_file: str = None,
                 author_name: Optional[str] = None, author_email: Optional[str] = None) -> None:
        """Constructor requires info to load the lab book

        Args:
            user(str): current logged in user
            owner(str): owner of the lab book
            labbook_name(str): name of the lab book
            monitor_key(str): Unique key for the activity monitor in redis
            author_name(str): Name of the user starting this activity monitor
            author_email(str): Email of the user starting this activity monitor
        """
        # Call super constructor
        ActivityMonitor.__init__(self, user, owner, labbook_name, monitor_key, config_file,
                                 author_name=author_name, author_email=author_email)

        # For now, register processors by default
        self.register_processors()

        # Let's call them cells as if they were Jupyter
        self.current_cell = ExecutionData()
        self.cell_data: List[ExecutionData] = list()

        # variables that track the context of messages in the log
        #   am I in the console, or the notebook?
        #   what chunk is being executed?
        #   in what notebook?
        self.is_console = False
        self.is_notebook = False
        self.chunk_id = None
        self.nbname = None

    def register_processors(self) -> None:
        """Method to register processors

        Returns:
            None
        """
        self.add_processor(RStudioServerCodeProcessor())
        self.add_processor(GenericFileChangeProcessor())
        self.add_processor(RStudioServerPlaintextProcessor())
        self.add_processor(RStudioServerImageExtractorProcessor())
        self.add_processor(ActivityShowBasicProcessor())

    def start(self, metadata: Dict[str, str], database: int = 1) -> None:
        """Method called in a periodically scheduled async worker that should check the dev env and manage Activity
        Monitor Instances as needed

        Args:
            metadata(dict): A dictionary of data to start the activity monitor
            database(int): The database ID to use

        Returns:
            None
        """
        # Get connection to the DB
        redis_conn = redis.Redis(db=database)

        # TODO DC: Dean asks why we need to use a regex here.
        m = re.match(r".*:activity_monitor:(\w+)$", self.monitor_key)
        if m is not None:
            filename = f"/mnt/share/mitmproxy/{m.group(1)}.rserver.dump"
        else:
            logger.error(f"No active monitor matching {self.monitor_key}")

        # TODO RB will need to open in write mode later to sparsify parts of the file that have already been read
        # https://github.com/gigantum/gigantum-client/issues/434
        # open the log file
        mitmlog = open(filename, "rb")
        if not mitmlog:
            logger.info(f"Failed to open RStudio log {self.monitor_key}")
            return

        try:
            while True:
                # TODO DC Loop until idle, then aggregate activity records
                # https://github.com/gigantum/gigantum-client/issues/434

                still_running = redis_conn.hget(self.monitor_key, "run")
                # Check if you should exit
                #  sometimes this runs after key has been deleted.  None is shutdown too.
                if not still_running or still_running.decode() == "False":
                    logger.info(f"Received Activity Monitor Shutdown Message for {self.monitor_key}")
                    break

                # Read activity and return an aggregated activity record
                self.process_activity(mitmlog)

                # aggregate four second of records together
                time.sleep(4)

        except Exception as e:
            logger.error(f"Error in RStudio Server Activity Monitor: {e}")
        finally:
            # Delete the kernel monitor key so the dev env monitor will spin up a new process
            # You may lose some activity if this happens, but the next action will sweep up changes
            logger.info(f"Shutting down RStudio monitor {self.monitor_key}")
            redis_conn.delete(self.monitor_key)

    def store_record(self) -> None:
        """Store R input/output/code to ActivityRecord

        Args:
            None
        Returns:
            None
        """
        if len(self.cell_data) > 0:
            t_start = time.time()

            # Process collected data and create an activity record
            if self.is_console:
                codepath = "console"
            else:
                codepath = self.nbname if self.nbname else "Unknown notebook"

            activity_record = self.process(ActivityType.CODE, list(reversed(self.cell_data)),
                                           {'path': codepath})

            # Commit changes to the related Notebook file
            commit = self.commit_labbook()

            # Create note record
            activity_commit = self.store_activity_record(commit, activity_record)

            logger.info(f"Created auto-generated activity record {activity_commit} in {time.time() - t_start} seconds")

        # Reset for next execution
        self.current_cell = ExecutionData()
        self.cell_data = list()
        self.is_notebook = False
        self.is_console = False

    def parse_record(self, jdict: Dict) -> None:
        """Extract code and data from the record.

        Args:
            record: dictionary parsed from mitmlog

        Returns:
            None
        """
        try:
            # No result ignore
            if jdict['result'] == []:
                return
        except KeyError:
            return

        try:
            # execution of new notebook cell
            if jdict['result'][0]['type'] == 'chunk_exec_state_changed':
                # switch from console to notebook. store record
                if self.is_console:
                    if not self.current_cell.code == []:
                        self.cell_data.append(self.current_cell)
                        self.store_record()
                elif self.is_notebook and not self.current_cell.code == []:
                    self.cell_data.append(self.current_cell)
                    self.current_cell = ExecutionData()
                    self.chunk_id = None

                self.is_notebook = True
                self.is_console = False
                # Reset current_cell attribute for next execution
                self.current_cell.tags.append('notebook')
        except:
            pass

        # if console input
        try:
            # execution of console code.  you get this every line.
            if jdict['result'][0]['type'] == 'console_write_prompt':
                try:
                    # switch to console. store record
                    if self.is_notebook:
                        if not self.current_cell.code == []:
                            self.cell_data.append(self.current_cell)
                            self.store_record()
                        self.current_cell.tags.append('console')

                    # add a tag is this is first line of console code
                    elif not self.is_console:
                        self.current_cell.tags.append('console')

                except Exception as e:
                    logger.info(f"Error {e}")
                    pass

                self.is_console = True
                self.is_notebook = False
        except:
            pass

        try:
            # parse the entries in this message
            for entry in jdict['result']:
                if entry['type'] == 'chunk_output':
                    for ekey in entry['data'].keys():
                        if ekey == 'chunk_outputs':
                            for oput in entry['data']['chunk_outputs']:
                                if oput['output_metadata']:
                                    if oput['output_metadata']['classes'] == 'data.frame':
                                        try:
                                            column_names = [x['label'][0] for x in oput['output_val']['columns']]
                                            df = pandas.DataFrame.from_dict(oput['output_val']['data'])
                                            df.columns = column_names
                                            if df.shape[0] <= 50:
                                                self.current_cell.result.append({'data': {'text/plain': str(df)},
                                                                                 'tags': 'data.frame'})
                                            else:
                                                output_text = str(df.head(20)) + \
                                                              f"\n.....,..and {df.shape[0] - 20} more rows"
                                                logger.info(output_text)
                                                self.current_cell.result.append({'data': {'text/plain': output_text},
                                                                                 'tags': 'data.frame'})
                                        except:
                                            self.current_cell.result.append(
                                                {'data': {'text/plain': json.dumps(oput['output_val'])},
                                                 'tags': 'data.frame'})

                        if ekey == 'chunk_output':
                            oput = entry['data']['chunk_output']
                            om = oput.get('output_metadata')
                            if om:
                                omc = om.get('classes')
                                if omc and 'data.frame' in omc:
                                    # take a stab at parsing the data frame
                                    try:
                                        column_names = [x['label'][0] for x in oput['output_val']['columns']]
                                        df = pandas.DataFrame.from_dict(oput['output_val']['data'])
                                        df.columns = column_names
                                        if df.shape[0] <= 50:
                                            self.current_cell.result.append({'data': {'text/plain': str(df)},
                                                                             'tags': 'data.frame'})
                                        else:
                                            output_text = str(df.head(20)) + \
                                                          f"\n.....,..and {df.shape[0] - 20} more rows"
                                            logger.info(output_text)
                                            self.current_cell.result.append({'data': {'text/plain': output_text},
                                                                             'tags': 'data.frame'})
                                    # can't parse. output something
                                    except:
                                        self.current_cell.result.append(
                                            {'data': {'text/plain': json.dumps(oput['output_val'])},
                                             'tags': 'data.frame'})
                                else:
                                    logger.error(f"XXX RB output no matching metadata")
                            else:
                                logger.error("XXX RBERROR unknown chunk_output")

                # get notebook code
                if self.is_notebook and entry['type'] == 'notebook_range_executed':

                    # new cell advance cell
                    if self.chunk_id == None or self.chunk_id != entry['data']['chunk_id']:
                        if self.current_cell.code != []:
                            self.cell_data.append(self.current_cell)
                        self.current_cell = ExecutionData()
                        self.chunk_id = entry['data']['chunk_id']
                        self.current_cell.tags.append('notebook')

                    # take code in current cell
                    self.current_cell.code.append({'code': entry['data']['code']})

                # console code
                if self.is_console and entry['type'] == 'console_write_input':
                    # remove trailing whitespace -- specificially \n
                    if entry['data']['text'] != "\n" or self.current_cell.code != []:
                        self.current_cell.code.append({'code': entry['data']['text'].rstrip()})

                # this happens in both notebooks and console
                #   ignore if no context (that's the R origination message
                if entry['type'] == 'console_output' and (self.is_console or self.is_notebook):
                    self.current_cell.result.append({'data': {'text/plain': entry['data']['text']}})

        except KeyError as ke:
            logger.error(f"Key error in parse_record {ke}")
        except Exception as e:
            logger.error(f"Unknown exception in parse_record {e}")

    def _is_error(self, result: Dict) -> bool:
        """Check if there's an error in the message"""
        for entry in result:
            if entry['type'] == 'console_error':
                return True
        else:
            return False

    def process_activity(self, mitmlog):
        """Collect tail of the activity log and turn into an activity record.

        Args:
            mitmlog(file): open file object

        Returns:
            ar(): activity record
        """
        # get an fstream generator object
        fstream = mitmio.FlowReader(mitmlog).stream()

        # no context yet.  not a notebook or console
        self.is_console = False
        self.is_notebook = False

        try:
            while True:

                try:
                    f = next(fstream)
                except StopIteration:
                    break
                except FlowReadException as e:
                    logger.info("MITM Flow file corrupted: {}. Exiting.".format(e))
                    break

                try:
                    st = f.get_state()

                    is_png = False
                    is_gzip = False
                    is_json = False

                    # Check response types for images and json
                    for h in st['response']['headers']:

                        # png images
                        if h[0] == b'Content-Type':
                            if h[1] == b'image/png':
                                is_png = True

                        # json
                        if h[0] == b'Content-Type':
                            if h[1] == b'application/json':
                                is_json = True

                        if h[0] == b'Content-Encoding':
                            if h[1] == b'gzip':
                                is_gzip = True
                            else:
                                encoding = h[1]

                    # process images
                    if is_png:
                        if is_gzip:
                            # These are from notebooks
                            m = re.match(r"/chunk_output/(([\w]+)/)+([\w]+.png)", st['request']['path'].decode())
                            if m:
                                img_data = zlib.decompress(st['response']['content'], 16 + zlib.MAX_WBITS)
                                img = Image.open(io.BytesIO(img_data))
                                eimg_data = base64.b64encode(img_data)
                                self.current_cell.result.append({'data': {'image/png': eimg_data}})

                            # These are from scripts.
                            m = re.match(r"/graphics/(?:[^[\\/:\"*?<>|]+])*([\w-]+).png",
                                         st['request']['path'].decode())
                            if m:
                                img_data = zlib.decompress(st['response']['content'], 16 + zlib.MAX_WBITS)
                                img = Image.open(io.BytesIO(img_data))
                                eimg_data = base64.b64encode(img_data)
                                self.current_cell.result.append({'data': {'image/png': eimg_data}})
                        else:
                            logger.error(f"RSERVER Found image/png that was not gzip encoded.")

                    if is_json:
                        # get the filename
                        m = re.match(r"/rpc/refresh_chunk_output.*", st['request']['path'].decode())
                        if m:
                            # potentially a new notebook. store data
                            if not self.current_cell.code == []:
                                self.cell_data.append(self.current_cell)
                                self.store_record()

                            # strict=False allows control codes, as used in tidyverse output
                            # TODO DC: Check that removal of .decode() doesn't cause trouble
                            jdata = json.loads(st['request']['content'], strict=False)
                            fullname = jdata['params'][0]

                            # pull out the name relative to the "code" directory
                            m1 = re.match(r".*/code/(.*)$", fullname)
                            if m1:
                                self.nbname = m1.group(1)
                            else:
                                m2 = re.match(r"/mnt/labbook/(.*)$", fullname)
                                if m2:
                                    self.nbname = m2.group(1)
                                else:
                                    self.nbname = fullname

                        # code or output event
                        m = re.match(r"/events/get_events", st['request']['path'].decode())
                        if m:
                            if is_gzip:
                                jdata = zlib.decompress(st['response']['content'], 16 + zlib.MAX_WBITS)
                            else:
                                jdata = st['response']['content']
                            # get text/code fields out of dictionary
                            # strict=False allows control codes, as used in tidyverse output
                            self.parse_record(json.loads(jdata, strict=False))

                except json.JSONDecodeError as je:
                    logger.info(f"Ignoring JSON Decoder Error in process_activity {je}.")
                    continue
                except Exception as e:
                    logger.info(f"Ignoring unknown error in process_activity {e}.")
                    continue

        finally:
            # Flush cell data IFF anything happened
            if self.current_cell.code != []:
                self.cell_data.append(self.current_cell)
            self.store_record()
            self.current_cell = ExecutionData()
            self.cell_data = list()
            self.chunk_id = None
