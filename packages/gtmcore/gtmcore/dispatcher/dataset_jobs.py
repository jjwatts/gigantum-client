import copy
import os
import time
from typing import Optional

from humanfriendly import format_size
from rq import get_current_job

from gtmcore.dataset import Manifest
from gtmcore.dataset.manifest.job import generate_bg_hash_job_list
from gtmcore.dispatcher import Dispatcher
from gtmcore.dispatcher.jobs import hash_dataset_files
from gtmcore.gitlib import GitAuthor
from gtmcore.inventory.inventory import InventoryManager
from gtmcore.logging import LMLogger


def complete_dataset_upload_transaction(logged_in_username: str, logged_in_email: str,
                                        dataset_owner: str, dataset_name: str, dispatcher, config_file: str = None) -> None:
    """Method to import a dataset from a zip file

    Args:
        logged_in_username: username for the currently logged in user
        logged_in_email: email for the currently logged in user
        dataset_owner: Owner of the labbook if this dataset is linked
        dataset_name: Name of the labbook if this dataset is linked
        dispatcher: Reference to the dispatcher CLASS
        config_file: config file (used for test mocking)

    Returns:
        None
    """
    logger = LMLogger.get_logger()
    dispatcher_obj = dispatcher()

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
