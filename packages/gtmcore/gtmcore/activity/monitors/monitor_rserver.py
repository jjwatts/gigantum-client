import time
import gzip

import base64
import json
import pandas
import re
import redis
from docker.errors import NotFound
from mitmproxy import io as mitmio
from mitmproxy.exceptions import FlowReadException
from typing import (Dict, List, Optional)

from gtmcore.activity import ActivityType
from gtmcore.activity.monitors.activity import ActivityMonitor
from gtmcore.activity.monitors.devenv import DevEnvMonitor
from gtmcore.activity.processors.core import GenericFileChangeProcessor, ActivityShowBasicProcessor, \
    ActivityDetailLimitProcessor
from gtmcore.activity.processors.processor import ExecutionData
from gtmcore.activity.processors.rserver import (RStudioServerCodeProcessor,
                                                 RStudioServerPlaintextProcessor,
                                                 RStudioServerImageExtractorProcessor)
from gtmcore.activity.services import stop_dev_env_monitors
from gtmcore.configuration import get_docker_client
from gtmcore.dispatcher import Dispatcher, jobs
from gtmcore.logging import LMLogger
from gtmcore.mitmproxy.mitmproxy import MITMProxyOperations

logger = LMLogger.get_logger()


def format_output(output: Dict):
    """Produce suitable JSON output for storing an R data frame in an Activity Record

    Args:
        output: the representation of a dataframe returned by
    """
    om = output.get('output_metadata')
    if om:
        omc = om.get('classes')
        # We currently don't deal with any complex outputs apart from data.frame
        # We'll log other metadata types below
        if omc and 'data.frame' in omc:
            try:
                column_names = [x['label'][0] for x in output['output_val']['columns']]
                df = pandas.DataFrame.from_dict(output['output_val']['data'])
                df.columns = column_names
                if df.shape[0] <= 50:
                    return {'data': {'text/plain': str(df)},
                            'tags': 'data.frame'}
                else:
                    output_text = str(df.head(20)) + \
                                  f"\n.....,..and {df.shape[0] - 20} more rows"
                    return {'data': {'text/plain': output_text},
                            'tags': 'data.frame'}

            # This bare except is left in-place because there are number of ways the above could fail,
            # but it's hard to imagine any big surprises, and this default behavior is completely reasonable.
            except:
                return {'data': {'text/plain': json.dumps(output['output_val'])},
                        'tags': 'data.frame'}
        else:
            logger.error(f"monitor_rserver: RStudio output with unknown metadata: {om}")
            # TODO DC Probably we can return a better JSON object
            return None
    else:
        logger.error(f"monitor_rserver: No metadata for chunk_output: {output}")
        return None


class RServerMonitor(DevEnvMonitor):
    """Class to monitor RStudio-Server for the need to start Activity Monitor Instances"""

    @staticmethod
    def get_dev_env_name() -> List[str]:
        """Method to return a list of names of the development environments that this class interfaces with.
        Should be the value used in the `name` attribute of the Dev Env Environment Component"""
        return ["rstudio"]

    def get_activity_monitor_lb_names(self, dev_env_monitor_key: str, redis_conn: redis.Redis) -> List[str]:
        """Return a list of the current activity monitors

        Currently only used in testing.

            Returns: List of strs with name of proxied labbook.
        """
        # Get list of active Activity Monitor Instances from redis
        # dev_env_monitor_key should specify rstudio at this point, and there should only be one key
        activity_monitor_keys = redis_conn.keys('{}:activity_monitor:*'.format(dev_env_monitor_key))
        activity_monitor_keys = [x.decode('utf-8') for x in activity_monitor_keys]
        retlist = []
        try:
            for am in activity_monitor_keys:
                logfid = redis_conn.hget(am, "logfile_id").decode()
                if logfid:
                    retlist.append(logfid)
        # decode throws error on unset values.  not sure how to check RB
        except Exception as e:
            logger.error(f'Unhandled exception in get_activity_monitor_lb_names: {e}')
            raise
        return retlist

    def run(self, dev_env_monitor_key: str, database: int = 1) -> None:
        """Method called in a periodically scheduled async worker that should check the dev env and manage Activity
        Monitor Instances as needed

        Args:
            dev_env_monitor_key: The unique string used as the key in redis to track this DevEnvMonitor instance
            database: The redis database number for dev env monitors to use
        """
        redis_conn = redis.Redis(db=database)
        activity_monitor_key = f'{dev_env_monitor_key}:activity_monitor'

        retval = redis_conn.hget(dev_env_monitor_key, 'container_name')
        if retval:
            labbook_container_name = retval.decode()
        else:
            # This shouldn't happen, but just in case
            logger.error(f'No container name for DevTool Monitor {dev_env_monitor_key}, stopping')
            # This should clean up everything this monitor is managing
            # labbook name is just for logging purposes, so we supply 'unknown'
            stop_dev_env_monitors(dev_env_monitor_key, redis_conn, 'unknown')
            return

        # For now, we directly query docker, this could be cleaned up in #453
        client = get_docker_client()
        try:
            dev_env_container_status = client.containers.get(labbook_container_name).status
        except NotFound:
            dev_env_container_status = 'not found'

        # Clean up and return labbook container names for running proxies
        running_proxy_lb_names = MITMProxyOperations.get_running_proxies()

        # As part of #453, we should re-start the proxy if the dev tool is still running
        if labbook_container_name not in running_proxy_lb_names:
            # MITM proxy isn't running anymore.
            logger.info(f"Detected exited RStudio proxy {labbook_container_name}. Stopping monitoring for {activity_monitor_key}")
            logger.info(f"Running proxies: {running_proxy_lb_names}")
            # This should clean up everything it's managing
            stop_dev_env_monitors(dev_env_monitor_key, redis_conn, labbook_container_name)
        elif dev_env_container_status != "running":
            # RStudio container isn't running anymore. Clean up by setting run flag to `False` so worker exits
            logger.info(f"Detected exited RStudio Project {labbook_container_name}. Stopping monitoring for {activity_monitor_key}")
            logger.info(f"Running proxies: {running_proxy_lb_names}")
            # This should clean up everything it's managing
            stop_dev_env_monitors(dev_env_monitor_key, redis_conn, labbook_container_name)
            # I don't believe we yet have a way to fit MITM proxy cleanup into the abstract dev env monitor machinery
            # Could be addressed in #453
            MITMProxyOperations.stop_mitm_proxy(labbook_container_name)
        else:
            am_running = redis_conn.hget(activity_monitor_key, 'run')
            if not am_running or am_running.decode() == 'False':
                # Get author info
                # RB this is not populated until a labbook is started why running?
                author_name = redis_conn.hget(dev_env_monitor_key, "author_name").decode()
                author_email = redis_conn.hget(dev_env_monitor_key, "author_email").decode()
                # Start new Activity Monitor
                _, user, owner, labbook_name, dev_env_name = dev_env_monitor_key.split(':')

                args = {"module_name": "gtmcore.activity.monitors.monitor_rserver",
                        "class_name": "RStudioServerMonitor",
                        "user": user,
                        "owner": owner,
                        "labbook_name": labbook_name,
                        "monitor_key": activity_monitor_key,
                        "author_name": author_name,
                        "author_email": author_email,
                        "session_metadata": None}

                d = Dispatcher()
                process_id = d.dispatch_task(jobs.start_and_run_activity_monitor, kwargs=args, persist=True)
                logger.info(f"Started RStudio Server Notebook Activity Monitor: Process {process_id}")

                # Update redis
                redis_conn.hset(activity_monitor_key, "process_id", process_id)
                redis_conn.hset(activity_monitor_key, "run", True)
                redis_conn.hset(activity_monitor_key, "logfile_path",
                                MITMProxyOperations.get_mitmlogfile_path(labbook_container_name))


class RStudioExchange:
    """Data-oriented class to simplify dealing with RStudio messages decoded from the MITM log

    Attributes are stored in a way that is ready for activity records. bytes get decoded, and images get
    base64-encoded.

    Parsing may throw a json.JSONDecodeError.
    """

    def __init__(self, mitm_message: mitmio.flow.Flow):
        raw_message = mitm_message.get_state()

        self.path = raw_message['request']['path'].decode()
        self.request_headers = {k.decode(): v.decode() for k, v in raw_message['request']['headers']}

        # strict=False allows control codes, as used in tidyverse output
        # Not sure if necessary for requests
        self.request = json.loads(raw_message['request']['content'].decode(), strict=False)

        self.response_headers = {k.decode(): v.decode() for k, v in raw_message['response']['headers']}
        self.response_type = self.response_headers.get('Content-Type')

        # This could get fairly resource intensive if our records get large,
        # but for now we keep things simple - all parsing happens in this class, and we can optimize later
        response = raw_message['response']['content']
        if self.response_headers.get('Content-Encoding') == 'gzip':
            response = gzip.decompress(response)
        if self.response_type == 'application/json':
            # strict=False allows control codes, as used in tidyverse output
            response = json.loads(response.decode(), strict=False)
        elif self.response_type == 'img/png':
            # if we actually wanted to work with the image, could do so like this:
            # img = Image.open(io.BytesIO(response))
            response = base64.b64encode(response)
        self.response = response


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
        # This will attempt to mirror what the RStudio backend knows for each doc_id
        self.doc_properties: Dict[str, Dict] = {}

    def register_processors(self) -> None:
        """Method to register processors

        Returns:
            None
        """
        self.add_processor(RStudioServerCodeProcessor())
        self.add_processor(GenericFileChangeProcessor())
        self.add_processor(RStudioServerPlaintextProcessor())
        self.add_processor(RStudioServerImageExtractorProcessor())
        self.add_processor(ActivityDetailLimitProcessor())
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

        logfile_path = redis_conn.hget(self.monitor_key, "logfile_path")

        mitmlog = open(logfile_path, "rb")
        if not mitmlog:
            logger.info(f"Failed to open RStudio log {logfile_path}")
            return

        try:
            while True:
                still_running = redis_conn.hget(self.monitor_key, "run")
                # Check if you should exit
                # sometimes this runs after key has been deleted.  None is shutdown too.
                if not still_running or still_running.decode() == "False":
                    logger.info(f"Received Activity Monitor Shutdown Message for {self.monitor_key}")
                    redis_conn.delete(self.monitor_key)
                    break

                previous_cells = len(self.cell_data)

                # Read activity and update aggregated "cell" data
                self.process_activity(mitmlog)

                # We are processing every second, then aggregating activity records when idle
                if previous_cells == len(self.cell_data) and self.current_cell.is_empty():
                    # there are no new cells in the last second, and no cells are in-process
                    self.store_record()

                # Check for new records every second
                time.sleep(1)

        except Exception as e:
            logger.error(f"Fatal error in RStudio Server Activity Monitor: {e}")
            raise
        finally:
            # Delete the kernel monitor key so the dev env monitor will spin up a new process
            # You may lose some activity if this happens, but the next action will sweep up changes
            logger.info(f"Shutting down RStudio monitor {self.monitor_key}")
            redis_conn.delete(self.monitor_key)
            # At this point, there is no chance we'll get anything else out of unmonitored files!
            MITMProxyOperations.clean_logfiles()

    def store_record(self) -> None:
        """Store R input/output/code to ActivityRecord / git commit

        store_record() should be called after moving any data in self.current_cell to
        self.cell_data. Any data remaining in self.current_cell will be removed.

        Args:
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

    def _parse_json_record(self, json_record: Dict) -> None:
        """Extract code and data from the record.

        When context switches between console <-> notebook, we store a record for
        the previous execution and start a new record.

        Args:
            json_record: dictionary parsed from mitmlog
        """
        result = json_record.get('result')
        # No result ignore
        if not result:
            return

        # execution of new notebook cell
        if result[0]['type'] == 'chunk_exec_state_changed':
            if self.is_console:
                # switch from console to notebook. store record
                if self.current_cell.code:
                    self.cell_data.append(self.current_cell)
                    self.store_record()
            elif self.is_notebook and self.current_cell.code:
                self.cell_data.append(self.current_cell)
                self.current_cell = ExecutionData()
                self.chunk_id = None

            self.is_notebook = True
            self.is_console = False
            # Reset current_cell attribute for next execution
            self.current_cell.tags.append('notebook')

        # execution of console code.  you get a message for every line.
        if result[0]['type'] == 'console_write_prompt':
            if self.is_notebook:
                # switch to console. store record
                if self.current_cell.code:
                    self.cell_data.append(self.current_cell)
                    self.store_record()
                self.current_cell.tags.append('console')

            # add a tag is this is first line of console code
            elif not self.is_console:
                self.current_cell.tags.append('console')

            self.is_console = True
            self.is_notebook = False

        # parse the entries in this message
        for edata, etype in [(entry.get('data'), entry.get('type')) for entry in result]:
            if etype == 'chunk_output':
                outputs = edata.get('chunk_outputs')
                if outputs:
                    for oput in outputs:
                        result = format_output(oput)
                        if result:
                            self.current_cell.result.append(result)

                oput = edata.get('chunk_output')
                if oput:
                    result = format_output(oput)
                    if result:
                        self.current_cell.result.append(result)

            # get notebook code
            if self.is_notebook and etype == 'notebook_range_executed':

                # new cell advance cell
                if self.chunk_id is None or self.chunk_id != edata['chunk_id']:
                    if self.current_cell.code:
                        self.cell_data.append(self.current_cell)
                    self.current_cell = ExecutionData()
                    self.chunk_id = edata['chunk_id']
                    self.current_cell.tags.append('notebook')

                # take code in current cell
                self.current_cell.code.append({'code': edata['code']})

            # console code
            if self.is_console and etype == 'console_write_input':
                # remove trailing whitespace -- specificially \n
                if edata['text'] != "\n" or self.current_cell.code != []:
                    self.current_cell.code.append({'code': edata['text'].rstrip()})

            # this happens in both notebooks and console
            #   ignore if no context (that's the R origination message
            if etype == 'console_output' and (self.is_console or self.is_notebook):
                self.current_cell.result.append({'data': {'text/plain': edata['text']}})

    def _is_error(self, result: Dict) -> bool:
        """Check if there's an error in the message"""
        for entry in result:
            if entry['type'] == 'console_error':
                return True
        else:
            return False

    def _handle_image(self, exchange: RStudioExchange):
        # The first are from documents (XXX DC and probably not notebooks), the second are from scripts.
        if re.match(r"/chunk_output/(([\w]+)/)+([\w]+.png)", exchange.path) or \
           re.match(r"/graphics/(?:[^[\\/:\"*?<>|]+])*([\w-]+).png", exchange.path):
            self.current_cell.result.append({'data': {'image/png': exchange.response}})

    def _parse_json(self, exchange: RStudioExchange) -> None:
        """Parse the JSON response information from RStudio - keeping track of code, output, and metadata

        Note that there are two different document types! "Notebooks" and an older "Document" type"""
        # For ANY file, the first time we get a user-facing id is when the front end gives a tempName
        if exchange.path == '/rpc/modify_document_properties':
            doc_id, properties = exchange.response['params']
            if 'tempName' in properties:
                self.doc_properties.setdefault(doc_id, {})['name'] = properties['tempName']

        # Later, a filename may be assigned by the front end
        # Haven't yet traced through what happens on save-as or loading a file instead of new -> save
        if exchange.path == '/rpc/save_document_diff':
            params = exchange.response['params']
            fname = params[1]
            if fname:
                doc_id = params[0]
                self.doc_properties.setdefault(doc_id, {})['name'] = fname

        # This is called after a recently opened document?
        # TODO DC Why did randal use regex below, not just string match?
        m = re.match(r"/rpc/refresh_chunk_output.*", exchange.path)
        if m:
            # A new chunk, so potentially a new notebook.
            if self.current_cell.code:
                self.cell_data.append(self.current_cell)
                # RB was always storing a record here
                # with new logic, running cells in two notebooks within a second seems unlikely
                # self.store_record()

            fullname = exchange.request['params'][0]

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
        if exchange.path == "/events/get_events":
            # get text/code fields out of dictionary
            self._parse_json_record(exchange.response)

    def process_activity(self, mitmlog):
        """Collect tail of the activity log and turn into an activity record.

        Args:
            mitmlog(file): open file object

        Returns:
            ar(): activity record
        """
        # get an fstream generator object
        fstream = iter(mitmio.FlowReader(mitmlog).stream())

        # no context yet.  not a notebook or console
        self.is_console = False
        self.is_notebook = False

        while True:
            try:
                mitm_message = next(fstream)
            except StopIteration:
                break
            except FlowReadException as e:
                logger.info("MITM Flow file corrupted: {}. Exiting.".format(e))
                break

            try:
                rstudio_exchange = RStudioExchange(mitm_message)
            except json.JSONDecodeError as je:
                logger.info(f"Ignoring JSON Decoder Error for Rstudio message {je}.")
                continue

            # process images
            if rstudio_exchange.response_type == 'image/png':
                # For some reason, Randal only wanted to parse gzip'd images
                # I guess non-zipped images should not occur
                if self.response_headers.get('Content-Encoding') == 'gzip':
                    self._handle_image(rstudio_exchange)
                else:
                    logger.error(f"RSERVER Found image/png that was not gzip encoded.")

            if rstudio_exchange.response_type == 'application/json':
                self._parse_json(rstudio_exchange)

        # Flush cell data IFF anything happened
        if self.current_cell.code:
            self.cell_data.append(self.current_cell)
        self.store_record()
        self.current_cell = ExecutionData()
        self.cell_data = list()
        self.chunk_id = None
