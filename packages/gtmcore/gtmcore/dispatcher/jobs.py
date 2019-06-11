import importlib
import json
import os
import time
from typing import Callable, Optional, List, NamedTuple
import sys
import shutil
import copy
from humanfriendly import format_size

from rq import get_current_job

from gtmcore.activity.monitors.devenv import DevEnvMonitorManager
from gtmcore.labbook import LabBook

from gtmcore.inventory.inventory import InventoryManager, InventoryException
from gtmcore.inventory.branching import MergeConflict
from gtmcore.inventory import Repository

from gtmcore.logging import LMLogger
from gtmcore.workflows import ZipExporter, LabbookWorkflow, DatasetWorkflow, MergeOverride
from gtmcore.container.core import (build_docker_image as build_image,
                                     start_labbook_container as start_container,
                                     stop_labbook_container as stop_container)

from gtmcore.dataset.manifest import Manifest
from gtmcore.dataset.manifest.job import generate_bg_hash_job_list
from gtmcore.dataset.io.manager import IOManager
from gtmcore.gitlib.git import GitAuthor
from gtmcore.dispatcher.dispatcher import Dispatcher


# PLEASE NOTE -- No global variables!
#
# None of the following methods can use global variables.
# ANY use of globals will cause the following methods to fail.


def publish_repository(repository: Repository, username: str, access_token: str,
                       remote: Optional[str] = None, public: bool = False, id_token: str = None) -> None:
    p = os.getpid()
    logger = LMLogger.get_logger()
    logger.info(f"(Job {p}) Starting publish_repository({str(repository)})")

    def update_meta(msg):
        job = get_current_job()
        if not job:
            return
        if 'feedback' not in job.meta:
            job.meta['feedback'] = msg
        else:
            job.meta['feedback'] = job.meta['feedback'] + f'\n{msg}'
        job.save_meta()

    try:
        with repository.lock():
            if isinstance(repository, LabBook):
                wf = LabbookWorkflow(repository)
            else:
                wf = DatasetWorkflow(repository) # type: ignore
            wf.publish(username=username, access_token=access_token, remote=remote or "origin",
                       public=public, feedback_callback=update_meta, id_token=id_token)
    except Exception as e:
        logger.exception(f"(Job {p}) Error on publish_repository: {e}")
        raise Exception("Could not publish - try to log out and log in again.")


def sync_repository(repository: Repository, username: str, override: MergeOverride,
                    remote: str = "origin", access_token: str = None,
                    pull_only: bool = False, id_token: str = None) -> int:
    p = os.getpid()
    logger = LMLogger.get_logger()
    logger.info(f"(Job {p}) Starting sync_repository({str(repository)})")

    def update_meta(msg):
        job = get_current_job()
        if not job:
            return
        if msg is None or (not msg.strip()):
            return

        if 'feedback' not in job.meta:
            job.meta['feedback'] = msg.strip()
        else:
            job.meta['feedback'] = job.meta['feedback'] + f'\n{msg.strip()}'
        job.save_meta()

    try:
        with repository.lock():
            if isinstance(repository, LabBook):
                wf = LabbookWorkflow(repository)
            else:
                wf = DatasetWorkflow(repository) # type: ignore
            cnt = wf.sync(username=username, remote=remote, override=override,
                          feedback_callback=update_meta, access_token=access_token,
                          id_token=id_token, pull_only=pull_only)
        logger.info(f"(Job {p} Completed sync_repository with cnt={cnt}")
        return cnt
    except MergeConflict as me:
        logger.exception(f"(Job {p}) Merge conflict: {me}")
        raise
    except Exception as e:
        logger.exception(f"(Job {p}) Error on sync_repository: {e}")
        raise Exception("Could not sync - try to log out and log in again.")


def import_labbook_from_remote(remote_url: str, username: str, config_file: str = None) -> str:
    """Return the root directory of the newly imported Project"""
    p = os.getpid()
    logger = LMLogger.get_logger()
    logger.info(f"(Job {p}) Starting import_labbook_from_remote({remote_url}, {username})")

    def update_meta(msg):
        job = get_current_job()
        if not job:
            return
        if 'feedback' not in job.meta:
            job.meta['feedback'] = msg
        else:
            job.meta['feedback'] = job.meta['feedback'] + f'\n{msg}'
        job.save_meta()

    try:
        toks = remote_url.split("/")
        if len(toks) > 1:
            proj_path = f'{toks[-2]}/{toks[-1].replace(".git", "")}'
        else:
            proj_path = remote_url
        update_meta(f"Importing Project from {proj_path!r}...")
        wf = LabbookWorkflow.import_from_remote(remote_url, username, config_file)
        update_meta(f"Imported Project {wf.labbook.name}!")
        return wf.labbook.root_dir
    except Exception as e:
        update_meta(f"Could not import Project from {remote_url}.")
        logger.exception(f"(Job {p}) Error on import_labbook_from_remote: {e}")
        raise


def export_labbook_as_zip(labbook_path: str, lb_export_directory: str) -> str:
    """Return path to archive file of exported labbook. """
    p = os.getpid()
    logger = LMLogger.get_logger()
    logger.info(f"(Job {p}) Starting export_labbook_as_zip({labbook_path})")

    try:
        lb = InventoryManager().load_labbook_from_directory(labbook_path)
        with lb.lock():
            path = ZipExporter.export_labbook(lb.root_dir, lb_export_directory)
        return path
    except Exception as e:
        logger.exception(f"(Job {p}) Error on export_labbook_as_zip: {e}")
        raise


def export_dataset_as_zip(dataset_path: str, ds_export_directory: str) -> str:
    """Return path to archive file of exported dataset. """
    p = os.getpid()
    logger = LMLogger.get_logger()
    logger.info(f"(Job {p}) Starting export_dataset_as_zip({dataset_path})")

    try:
        ds = InventoryManager().load_dataset_from_directory(dataset_path)
        with ds.lock():
            path = ZipExporter.export_dataset(ds.root_dir, ds_export_directory)
        return path
    except Exception as e:
        logger.exception(f"(Job {p}) Error on export_dataset_as_zip: {e}")
        raise


def import_labboook_from_zip(archive_path: str, username: str, owner: str,
                             config_file: Optional[str] = None) -> str:
    """Method to import a labbook from a zip file

    Args:
        archive_path(str): Path to the uploaded zip
        username(str): Username
        owner(str): Owner username
        config_file(str): Optional path to a labmanager config file

    Returns:
        str: directory path of imported labbook
    """

    def update_meta(msg):
        job = get_current_job()
        if not job:
            return
        job.meta['feedback'] = msg
        job.save_meta()

    p = os.getpid()
    logger = LMLogger.get_logger()
    logger.info(f"(Job {p}) Starting import_labbook_from_zip(archive_path={archive_path},"
                f"username={username}, owner={owner}, config_file={config_file})")

    try:
        lb = ZipExporter.import_labbook(archive_path, username, owner,
                                        config_file=config_file,
                                        update_meta=update_meta)
        return lb.root_dir
    except Exception as e:
        logger.exception(f"(Job {p}) Error on import_labbook_from_zip({archive_path}): {e}")
        raise
    finally:
        if os.path.exists(archive_path):
            os.remove(archive_path)


def import_dataset_from_zip(archive_path: str, username: str, owner: str,
                            config_file: Optional[str] = None) -> str:
    """Method to import a dataset from a zip file

    Args:
        archive_path(str): Path to the uploaded zip
        username(str): Username
        owner(str): Owner username
        config_file(str): Optional path to a labmanager config file

    Returns:
        str: directory path of imported labbook
    """

    def update_meta(msg):
        job = get_current_job()
        if not job:
            return
        job.meta['feedback'] = msg
        job.save_meta()

    p = os.getpid()
    logger = LMLogger.get_logger()
    logger.info(f"(Job {p}) Starting import_dataset_from_zip(archive_path={archive_path},"
                f"username={username}, owner={owner}, config_file={config_file})")

    try:
        lb = ZipExporter.import_dataset(archive_path, username, owner,
                                        config_file=config_file,
                                        update_meta=update_meta)
        return lb.root_dir
    except Exception as e:
        logger.exception(f"(Job {p}) Error on import_dataset_from_zip({archive_path}): {e}")
        raise
    finally:
        if os.path.exists(archive_path):
            os.remove(archive_path)


def build_labbook_image(path: str, username: str,
                        tag: Optional[str] = None, nocache: bool = False) -> str:
    """Return a docker image ID of given LabBook.

    Args:
        path: Pass-through arg to labbook root.
        username: Username of active user.
        tag: Pass-through arg to tag of docker image.
        nocache(bool): Pass-through arg to docker build.

    Returns:
        Docker image ID
    """

    logger = LMLogger.get_logger()
    logger.info(f"Starting build_labbook_image({path}, {username}, {tag}, {nocache}) in pid {os.getpid()}")

    try:
        job = get_current_job()
        if job:
            job.meta['pid'] = os.getpid()
            job.save_meta()

        def save_metadata_callback(line: str) -> None:
            try:
                if not line:
                    return
                job.meta['feedback'] = (job.meta.get('feedback') or '') + line + '\n'
                job.save_meta()
            except Exception as e:
                logger.error(e)

        image_id = build_image(path, override_image_tag=tag, nocache=nocache, username=username,
                               feedback_callback=save_metadata_callback)

        logger.info(f"Completed build_labbook_image in pid {os.getpid()}: {image_id}")
        return image_id
    except Exception as e:
        logger.error(f"Error on build_labbook_image in pid {os.getpid()}: {e}")
        raise


def run_dev_env_monitor(dev_env_name, key) -> int:
    """Run method to check if new Activity Monitors for a given dev env need to be started/stopped

        Args:
            dev_env_name(str): Name of the dev env to monitor
            key(str): The unique string used as the key in redis to track this DevEnvMonitor instance

    Returns:
        0 to indicate no failure
    """

    logger = LMLogger.get_logger()
    logger.debug("Checking Dev Env `{}` for activity monitors in PID {}".format(dev_env_name, os.getpid()))

    try:
        demm = DevEnvMonitorManager()
        dev_env = demm.get_monitor_instance(dev_env_name)
        if not dev_env:
            raise ValueError('dev_env is None')
        dev_env.run(key)
        return 0
    except Exception as e:
        logger.error("Error on run_dev_env_monitor in pid {}: {}".format(os.getpid(), e))
        raise e


def start_and_run_activity_monitor(module_name, class_name, user, owner, labbook_name, monitor_key, author_name,
                                   author_email, session_metadata):
    """Run method to run the activity monitor. It is a long running job.

        Args:


    Returns:
        0 to indicate no failure
    """
    logger = LMLogger.get_logger()
    logger.info("Starting Activity Monitor `{}` in PID {}".format(class_name, os.getpid()))

    try:
        # Import the monitor class
        m = importlib.import_module(module_name)
        # get the class
        monitor_cls = getattr(m, class_name)

        # Instantiate monitor class
        monitor = monitor_cls(user, owner, labbook_name, monitor_key,
                              author_name=author_name, author_email=author_email)

        # Start the monitor
        monitor.start(session_metadata)

        return 0
    except Exception as e:
        logger.error("Error on start_and_run_activity_monitor in pid {}: {}".format(os.getpid(), e))
        raise e


def index_labbook_filesystem():
    """To be implemented later. """
    raise NotImplemented


def test_exit_success():
    """Used only for testing -- vacuous method to always succeed and return 0. """
    return 0


def test_exit_fail():
    """Used only for testing -- always throws an exception"""
    raise Exception("Intentional Exception from job `test_exit_fail`")


def test_sleep(n):
    """Used only for testing -- example method with argument. """
    logger = LMLogger.get_logger()
    logger.info("Starting test_sleep({}) in pid {}".format(n, os.getpid()))

    try:
        job = get_current_job()
        job.meta['sample'] = 'test_sleep metadata'
        job.meta['pid'] = int(os.getpid())
        job.save_meta()

        time.sleep(n)
        logger.info("Completed test_sleep in pid {}".format(os.getpid()))
        return 0
    except Exception as e:
        logger.error("Error on test_sleep in pid {}: {}".format(os.getpid(), e))
        raise


def test_incr(path):
    logger = LMLogger.get_logger()
    logger.info("Starting test_incr({}) in pid {}".format(path, os.getpid()))

    try:
        amt = 1
        if not os.path.exists(path):
            logger.info("Creating {}".format(path))
            with open(path, 'w') as fp:
                json.dump({'amt': amt}, fp)
        else:
            logger.info("Loading {}".format(path))
            with open(path, 'r') as fp:
                amt_dict = json.load(fp)
            logger.info("Amt = {}")
            with open(path, 'w') as fp:
                amt_dict['amt'] = amt_dict['amt'] + 1
                json.dump(amt_dict, fp)
            logger.info("Set amt = {} in {}".format(amt_dict['amt'], path))
    except Exception as e:
        logger.error("Error on test_incr in pid {}: {}".format(os.getpid(), e))
        raise


def download_dataset_files(logged_in_username: str, access_token: str, id_token: str,
                           dataset_owner: str, dataset_name: str,
                           labbook_owner: Optional[str] = None, labbook_name: Optional[str] = None,
                           all_keys: Optional[bool] = False, keys: Optional[List[str]] = None):
    """Method to import a dataset from a zip file

    Args:
        logged_in_username: username for the currently logged in user
        access_token: bearer token
        id_token: identity token
        dataset_owner: Owner of the dataset containing the files to download
        dataset_name: Name of the dataset containing the files to download
        labbook_owner: Owner of the labbook if this dataset is linked
        labbook_name: Name of the labbook if this dataset is linked
        all_keys: Boolean indicating if all remaining files should be downloaded
        keys: List if file keys to download

    Returns:
        str: directory path of imported labbook
    """
    def update_meta(msg):
        job = get_current_job()
        if not job:
            return
        if 'feedback' not in job.meta:
            job.meta['feedback'] = msg
        else:
            job.meta['feedback'] = job.meta['feedback'] + f'\n{msg}'
        job.save_meta()

    logger = LMLogger.get_logger()

    try:
        p = os.getpid()
        logger.info(f"(Job {p}) Starting download_dataset_files(logged_in_username={logged_in_username},"
                    f"dataset_owner={dataset_owner}, dataset_name={dataset_name}, labbook_owner={labbook_owner},"
                    f" labbook_name={labbook_name}, all_keys={all_keys}, keys={keys}")

        im = InventoryManager()

        if labbook_owner is not None and labbook_name is not None:
            # This is a linked dataset, load repo from the Project
            lb = im.load_labbook(logged_in_username, labbook_owner, labbook_name)
            dataset_dir = os.path.join(lb.root_dir, '.gigantum', 'datasets', dataset_owner, dataset_name)
            ds = im.load_dataset_from_directory(dataset_dir)
        else:
            # this is a normal dataset. Load repo from working dir
            ds = im.load_dataset(logged_in_username, dataset_owner, dataset_name)

        ds.namespace = dataset_owner
        ds.backend.set_default_configuration(logged_in_username, access_token, id_token)
        m = Manifest(ds, logged_in_username)
        iom = IOManager(ds, m)

        if all_keys:
            result = iom.pull_all(status_update_fn=update_meta)
        elif keys:
            result = iom.pull_objects(keys=keys, status_update_fn=update_meta)
        else:
            raise ValueError("Must provide a list of keys or set all_keys=True")

        # Save the Relay node IDs to the job metadata so the UI can re-fetch as needed
        job = get_current_job()
        if job:
            job.meta['success_keys'] = [x.dataset_path for x in result.success]
            job.meta['failure_keys'] = [x.dataset_path for x in result.failure]
            job.save_meta()

        if len(result.failure) > 0:
            # If any downloads failed, exit non-zero to the UI knows there was an error
            sys.exit(-1)

    except Exception as err:
        logger.exception(err)
        raise


def clean_dataset_file_cache(logged_in_username: str, dataset_owner: str, dataset_name: str,
                             cache_location: str, config_file: str = None) -> None:
    """Method to import a dataset from a zip file

    Args:
        logged_in_username: username for the currently logged in user
        dataset_owner: Owner of the labbook if this dataset is linked
        dataset_name: Name of the labbook if this dataset is linked
        cache_location: Absolute path to the file cache (inside the container) for this dataset
        config_file:

    Returns:
        None
    """
    logger = LMLogger.get_logger()

    p = os.getpid()
    try:
        logger.info(f"(Job {p}) Starting clean_dataset_file_cache(logged_in_username={logged_in_username},"
                    f"dataset_owner={dataset_owner}, dataset_name={dataset_name}")

        im = InventoryManager(config_file=config_file)

        # Check for dataset
        try:
            im.load_dataset(logged_in_username, dataset_owner, dataset_name)
            logger.info(f"{logged_in_username}/{dataset_owner}/{dataset_name} still exists. Skipping file cache clean.")
            return
        except InventoryException:
            # Dataset not found, move along
            pass

        # Check for submodule references
        for lb in im.list_labbooks(logged_in_username):
            submodules = lb.git.list_submodules()
            for submodule in submodules:
                submodule_dataset_owner, submodule_dataset_name = submodule['name'].split("&")
                if submodule_dataset_owner == dataset_owner and submodule_dataset_name == dataset_name:
                    logger.info(f"{logged_in_username}/{dataset_owner}/{dataset_name} still referenced by {str(lb)}."
                                f" Skipping file cache clean.")
                    return

        # If you get here the dataset no longer exists and is not used by any projects, clear files
        shutil.rmtree(cache_location)

    except Exception as err:
        logger.error(f"(Job {p}) Error in clean_dataset_file_cache job")
        logger.exception(err)
        raise


def hash_dataset_files(logged_in_username: str, dataset_owner: str, dataset_name: str,
                       file_list: List, config_file: str = None) -> None:
    """

    Args:
        logged_in_username: username for the currently logged in user
        dataset_owner: Owner of the labbook if this dataset is linked
        dataset_name: Name of the labbook if this dataset is linked
        file_list: List of files to be hashed
        config_file: Optional config file to use

    Returns:
        None
    """
    logger = LMLogger.get_logger()

    p = os.getpid()
    try:
        logger.info(f"(Job {p}) Starting hash_dataset_files(logged_in_username={logged_in_username},"
                    f"dataset_owner={dataset_owner}, dataset_name={dataset_name}")

        ds = InventoryManager(config_file=config_file).load_dataset(logged_in_username, dataset_owner, dataset_name)
        manifest = Manifest(ds, logged_in_username)

        hash_result, fast_hash_result = manifest.hash_files(file_list)

        job = get_current_job()
        if job:
            job.meta['hash_result'] = ",".join(['None' if v is None else v for v in hash_result])
            job.meta['fast_hash_result'] = ",".join(['None' if v is None else v for v in fast_hash_result])
            job.save_meta()

    except Exception as err:
        logger.error(f"(Job {p}) Error in clean_dataset_file_cache job")
        logger.exception(err)
        raise


def complete_dataset_upload_transaction(logged_in_username: str, logged_in_email: str,
                                        dataset_owner: str, dataset_name: str, config_file: str = None) -> None:
    """Method to import a dataset from a zip file

    Args:
        logged_in_username: username for the currently logged in user
        logged_in_email: email for the currently logged in user
        dataset_owner: Owner of the labbook if this dataset is linked
        dataset_name: Name of the labbook if this dataset is linked
        config_file: config file (used for test mocking)

    Returns:
        None
    """
    logger = LMLogger.get_logger()

    def update_feedback(msg: str, has_failures: Optional[bool] = None, failure_detail: Optional[str] = None,
                        percent_complete: Optional[float] = None):
        """Method to update the job's metadata and provide feedback to the UI"""
        current_job = get_current_job()
        if not current_job:
            return
        if has_failures:
            current_job.meta['has_failures'] = has_failures
        if failure_detail:
            current_job.meta['failure_detail'] = failure_detail
        if percent_complete:
            current_job.meta['percent_complete'] = percent_complete

        current_job.meta['feedback'] = msg
        current_job.save_meta()

    def schedule_bg_hash_job():
        """Method to check if a bg job should get scheduled and do so"""
        num_cores = manifest.get_num_hashing_cpus()
        if sum([x.is_running for x in job_list]) < num_cores:
            for j in job_list:
                if j.is_failed is True and j.failure_count < 3:
                    # Re-schedule failed job
                    job_kwargs['file_list'] = j.file_list
                    job_key = dispatcher_obj.dispatch_task(hash_dataset_files,
                                                           kwargs=job_kwargs,
                                                           metadata=job_metadata)
                    j.job_key = job_key
                    update_feedback(f"Restarted failed file hashing job. Re-processing"
                                    f" {format_size(j.total_bytes)}...")
                    logger.info(f"(Job {p}) Restarted file hash job for"
                                f" {logged_in_username}/{dataset_owner}/{dataset_name}")
                    break

                if j.is_complete is False and j.is_running is False:
                    # Schedule new job
                    job_kwargs['file_list'] = j.file_list
                    job_key = dispatcher_obj.dispatch_task(hash_dataset_files,
                                                           kwargs=job_kwargs,
                                                           metadata=job_metadata)
                    j.job_key = job_key
                    logger.info(f"(Job {p}) Scheduled file hash job for"
                                f" {logged_in_username}/{dataset_owner}/{dataset_name}")
                    break

    p = os.getpid()
    try:
        logger.info(f"(Job {p}) Starting complete_dataset_upload_transaction(logged_in_username={logged_in_username},"
                    f"dataset_owner={dataset_owner}, dataset_name={dataset_name}")

        author = GitAuthor(name=logged_in_username, email=logged_in_email)
        dispatcher_obj = Dispatcher()
        ds = InventoryManager(config_file=config_file).load_dataset(logged_in_username, dataset_owner, dataset_name,
                                                                    author=author)
        manifest = Manifest(ds, logged_in_username)

        with ds.lock():
            # Detect changes
            status = manifest.status()

            # Collect filenames that need to be hashed
            filenames = copy.deepcopy(status.modified)
            filenames.extend(status.created)

            # If there are new/updated files, spread work across cores while providing reasonable feedback
            if filenames:
                job_list = generate_bg_hash_job_list(filenames, manifest, dispatcher_obj)
                total_bytes = sum([x.total_bytes for x in job_list])

                job_kwargs = {
                    'logged_in_username': logged_in_username,
                    'dataset_owner': dataset_owner,
                    'dataset_name': dataset_name,
                    'file_list': list(),
                    'config_file': config_file,
                }
                job_metadata = {'dataset': f"{logged_in_username}|{dataset_owner}|{dataset_name}",
                                'method': 'hash_dataset_files'}

                update_feedback(f"Please wait while file contents are analyzed. "
                                f"Processing {format_size(total_bytes)}...", has_failures=False)
                logger.info(f"(Job {p}) Starting file hash processing for"
                            f" {logged_in_username}/{dataset_owner}/{dataset_name} with {len(job_list)} jobs")

                while True:
                    # Check if you need to schedule jobs and schedule up to 1 job per iteration
                    schedule_bg_hash_job()

                    # Refresh all job statuses and update status feedback
                    completed_job_status = [x.refresh_status() for x in job_list]
                    completed_bytes = sum([s.total_bytes for s, c in zip(job_list, completed_job_status) if c is True])
                    update_feedback(f"Please wait while file contents are analyzed. "
                                    f"{format_size(completed_bytes)} of {format_size(total_bytes)} complete...",
                                    percent_complete=(float(completed_bytes)/float(total_bytes)) * 100)

                    # Check if you are done
                    completed_or_failed = sum([(x.is_complete or (x.failure_count >= 3)) for x in job_list])
                    if completed_or_failed == len(job_list):
                        break

                    # Update once per second
                    time.sleep(1)

                # Manually complete update process for updated/created files
                failed_files = list()
                for job in job_list:
                    if job.is_complete:
                        for f, h, fh in zip(job.file_list, job.get_hash_result(), job.get_fast_hash_result()):
                            if not fh or not h:
                                failed_files.append(f)
                                continue

                            _, file_bytes, mtime = fh.split("||")
                            manifest._manifest_io.add_or_update(f, h, mtime, file_bytes)
                    else:
                        failed_files.extend(job.file_list)

                # Message for hard failures
                if failed_files:
                    detail_msg = f"The following files failed to hash. Try re-uploading the files again:\n"
                    detail_file_list = " \n".join(failed_files)
                    detail_msg = f"{detail_msg}{detail_file_list}"
                    update_feedback(f"An error occurred while processing some files. Check details and re-upload.",
                                    has_failures=True, failure_detail=detail_msg)

            if status.deleted:
                manifest.hasher.delete_fast_hashes(status.deleted)
                for relative_path in status.deleted:
                    manifest._manifest_io.remove(relative_path)

            manifest._manifest_io.persist()

            # Complete sweep operation
            manifest.sweep_all_changes(status=status, upload=True)

    except Exception as err:
        logger.error(f"(Job {p}) Error in clean_dataset_file_cache job")
        logger.exception(err)
        raise
