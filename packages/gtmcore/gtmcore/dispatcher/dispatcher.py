# Copyright (c) 2017 FlashX, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from enum import Enum
from datetime import datetime
from typing import (Any, Callable, cast, Dict, List, Optional, Tuple)
import signal
import time
import os

import redis
import rq
import rq_scheduler

from gtmcore.logging import LMLogger
from gtmcore.exceptions import GigantumException

logger = LMLogger.get_logger()


class JobKey(object):
    """ Represents a key for a background job in Redis. """
    def __init__(self, key: str) -> None:
        try:
            self._validate(key)
        except AssertionError as e:
            logger.error(e)
            raise
        self._key_str: str = key

    def __str__(self) -> str:
        return self._key_str

    def __repr__(self):
        return self._key_str

    def __eq__(self, other: object) -> bool:
        return type(other) == type(self) and str(self) == str(other)

    def _validate(self, key):
        assert key, f"Key '{key}' cannot be None or empty"
        assert isinstance(key, str), f"`key` must be str, not {type(key)}"
        assert len(key.split(':')) == 3, "Key must be in format of `rq:job:<uuid>`"

    @property
    def key_str(self):
        return self._key_str


class DispatcherException(GigantumException):
    pass


class JobStatus(object):
    """ Represents a background job known to the backend processing system. Represents the state of the background
        job at a particular point in time. Does not re-query to fetch fresher information (Because Jobs may be cleaned
        up in the backend and information may be lost) """
    def __init__(self, redis_dict: Dict[str, object]) -> None:
        # Because this captures the state of the Job at a given point in time, it should
        # carry the timestamp of this snapshot.
        self.timestamp = datetime.now()
        self.job_key: JobKey = JobKey(cast(str, redis_dict['_key']))
        self.status: Optional[str] = cast(str, redis_dict.get('status'))
        self.result: Optional[object] = cast(str, redis_dict.get('result'))
        self.description: Optional[str] = cast(str, redis_dict.get('description'))
        self.meta: Dict[str, str] = cast(Dict[str, str], redis_dict.get('meta') or {})
        self.exc_info: Optional[str] = cast(str, redis_dict.get('exc_info'))
        self.started_at: Optional[datetime] = cast(datetime, redis_dict.get('started_at'))
        self.finished_at: Optional[datetime] = cast(datetime, redis_dict.get('ended_at'))

    def __str__(self) -> str:
        return f'<BackgroundJob {str(self.job_key)}>'

    def __eq__(self, other: object) -> bool:
        return type(other) == type(self) and str(self) == str(other)

    @property
    def failure_message(self) -> Optional[str]:
        if self.exc_info:
            lines = [l for l in self.exc_info.split(os.linesep) if l]
            return None if len(lines) == 0 else lines[-1]
        else:
            return None


class GigantumQueues(Enum):
    # Represents the default queue for all non-intense jobs. This queue may be bursted.
    default_queue = "gigantum-default-queue"

    # Represents the queue for Docker build tasks. This queue is most strictly controlled.
    # (i.e., just one or a few workers for it)
    build_queue = "gigantum-build-queue"

    # Queue for anything interacting with the remote. Not the most computationally/IO-intense
    # operations, but still should be capped out.
    publish_queue = "gigantum-publish-queue"


JOB_QUEUE_MAP = {
    # Docker builds are the most intense operations, so it has its own queue
    "build_labbook_image": GigantumQueues.build_queue,

    # The publish queue is for anything interacting with the Git remote
    # it is less intense than a Docker build, bit still should be limited
    "download_dataset_files": GigantumQueues.publish_queue,
    "import_labbook_from_remote": GigantumQueues.publish_queue,
    "sync_repository": GigantumQueues.publish_queue,
    "publish_repository": GigantumQueues.publish_queue
}


class Dispatcher(object):
    """Class to serve as an interface to the background job processing service.
    """

    def __init__(self) -> None:
        self._redis_conn = redis.Redis()
        self._scheduler = rq_scheduler.Scheduler(queue_name=GigantumQueues.default_queue.value,
                                                 connection=self._redis_conn)

    def _get_queue(self, method_name: str) -> rq.Queue:
        # Return the appropriate Queue instance for the given method.
        queue_name = JOB_QUEUE_MAP.get(method_name) or GigantumQueues.default_queue
        return rq.Queue(queue_name.value, connection=self._redis_conn)

    @property
    def all_jobs(self) -> List[JobStatus]:
        """Return a list of dicts containing information about all jobs in the backend. """
        redis_keys = self._redis_conn.keys("rq:job:*")
        redis_keys = [x for x in redis_keys if "dependents" not in x.decode()]

        # Ignore type checking on the following line cause we filter out None-results.
        return [self.query_task(JobKey(q.decode())) for q in redis_keys if q]  # type: ignore

    @property
    def failed_jobs(self) -> List[JobStatus]:
        """Return all explicity-failed jobs. """
        return [job for job in self.all_jobs if job.status == 'failed']

    @property
    def finished_jobs(self) -> List[JobStatus]:
        """Return a list of all jobs that are considered "complete" (i.e., no error). """
        return [job for job in self.all_jobs if job.status == 'finished']

    def get_jobs_for_labbook(self, labbook_key: str) -> List[JobStatus]:
        """Return all background job keys pertaining to the given labbook, as indexed by its root_directory. """
        def is_match(job):
            return job.meta and job.meta.get('labbook') == labbook_key

        labbook_jobs = [job for job in self.all_jobs if is_match(job)]
        if not labbook_jobs:
            logger.debug(f"No background jobs found for labbook `{labbook_key}`")

        return labbook_jobs

    def query_task(self, job_key: JobKey) -> Optional[JobStatus]:
        """Return a JobStatus containing all info pertaining to background job.

        Args:
            job_key(JobKey): JobKey containing redis key of job.

        Returns:
            JobStatus
        """
        logger.debug("Querying for task {}".format(job_key))

        # The job_dict is returned from redis is contains strictly binary data, to be more usable
        # it needs to be parsed and loaded as proper data types. The decoded data is stored in the
        # `decoded_dict`.
        job_dict = self._redis_conn.hgetall(job_key.key_str)
        if not job_dict:
            logger.warning(f"Query to task {job_key} not found in Redis")
            return None

        # Fetch the RQ job. There needs to be a little processing done on it first.
        rq_job = rq.job.Job.fetch(job_key.key_str.split(':')[-1],
                                  connection=redis.Redis())

        # Build the properly decoded dict, which will be returned.
        decoded_dict = {}
        for k in job_dict.keys():
            try:
                decoded_dict[k.decode('utf-8')] = getattr(rq_job, k.decode())
            except AttributeError as e:
                logger.debug(e)

        decoded_dict.update({'_key': job_key.key_str})
        return JobStatus(decoded_dict)

    def unschedule_task(self, job_key: JobKey) -> bool:
        """Cancel a scheduled task. Note, this does NOT cancel "dispatched" tasks, only ones created
           via `schedule_task`.

        Args:
            job_key(str): ID of the task that was returned via `schedule_task`.

        Returns:
            bool: True if task scheduled successfully, False if task not found.
        """

        # Encode job_id as byes from regular string, strip off the "rq:job" prefix.
        enc_job_id = job_key.key_str.split(':')[-1].encode()

        if enc_job_id in self._scheduler:
            logger.info("Job (encoded id=`{}`) found in scheduler, cancelling".format(enc_job_id))
            self._scheduler.cancel(enc_job_id)
            logger.info("Unscheduled job (encoded id=`{}`)".format(enc_job_id))
            return True
        else:
            logger.warning("Job (encoded id=`{}`) NOT FOUND in scheduler, nothing to cancel".format(enc_job_id))
            return False

    def schedule_task(self, method_reference: Callable, args: Optional[Tuple[Any]] = None,
                      kwargs: Optional[Dict[str, Any]] = None,
                      scheduled_time: Optional[datetime] = None, repeat: Optional[int] = 0,
                      interval: Optional[int] = None) -> JobKey:
        """Schedule at task to run at a particular time in the future, and/or with certain recurrence.

        Args:
            method_reference(Callable): The method in dispatcher.jobs to run
            args(list): Arguments to method_reference
            kwargs(dict): Keyword Argument to method_reference
            scheduled_time(datetime.datetime): UTC timestamp of time to run this task, None indicates now
            repeat(int): Number of times to re-run the task (None indicates repeat forever)
            interval(int): Seconds between invocations of the task (None indicates no recurrence)

        Returns:
            str: unique key of dispatched task
        """
        job_args = args or tuple()
        job_kwargs = kwargs or {}
        rq_job_ref = self._scheduler.schedule(scheduled_time=scheduled_time or datetime.utcnow(),
                                              func=method_reference,
                                              args=job_args,
                                              kwargs=job_kwargs,
                                              interval=interval,
                                              repeat=repeat)

        logger.info(f"Scheduled job `{method_reference.__name__}`, job={str(rq_job_ref)}")

        # job_ref.key is in bytes.. should be decode()-ed to form a python string.
        return JobKey(rq_job_ref.key.decode())

    def dispatch_task(self, method_reference: Callable, args: Tuple[Any, ...] = None, kwargs: Dict[str, Any] = None,
                      metadata: Dict[str, Any] = None, persist: bool = False, dependent_job: JobKey = None) -> JobKey:
        """Dispatch new task to run in background, which runs as soon as it can.

        Note: If the dependent_job task is populated, then this task will NOT run until the dependent_job
        finished **successfully**. If the dependent_job fails, this task will NOT run.

        Args:
            method_reference(Callable): The method in dispatcher.jobs to run
            args(list): Arguments to method_reference
            kwargs(dict): Keyword Argument to method_reference
            metadata(dict): Optional dict of metadata
            persist(bool): Never timeout if True, otherwise abort after 2 hours.
            dependent_job(JobKey): The JobKey of the job this task depends on.

        Returns:
            str: unique key of dispatched task
        """

        if not callable(method_reference):
            raise ValueError("method_reference must be callable")

        if not args:
            args = ()

        if not kwargs:
            kwargs = {}

        if not metadata:
            metadata = {}

        if persist:
            # Currently, one month.
            timeout = '730h'
        else:
            timeout = '2h'

        queue = self._get_queue(method_reference.__name__)
        logger.info(
            f"Dispatching {'persistent' if persist else 'ephemeral'} "
            f"task `{method_reference.__name__}` to queue {queue}")

        try:
            dep_job_str = dependent_job.key_str.split(':')[-1] if dependent_job else None
            rq_job_ref = queue.enqueue(method_reference, args=args, kwargs=kwargs, timeout=timeout,
                                       depends_on=dep_job_str, meta=metadata)
        except Exception as e:
            logger.error("Cannot enqueue job `{}`: {}".format(method_reference.__name__, e))
            raise

        rq_job_key_str = rq_job_ref.key.decode()
        logger.info(
            "Dispatched job `{}` to queue '{}', job={}".format(method_reference.__name__,
                                                               queue.name,
                                                               rq_job_key_str))
        try:
            assert rq_job_key_str
            jk = JobKey(rq_job_key_str)
        except Exception as e:
            logger.exception(e)
            raise

        return jk

    def abort_task(self, job_key: JobKey) -> None:
        """ Terminate an actively-running task. This does NOT kill the worker.

        Note: Only certain tasks (ones that write pid to metadata) are
        cancellable.

        See discussion on: https://github.com/rq/rq/issues/684

        Args:
            job_key: Job key of task to cancel

        Returns:
            None

        """
        task = self.query_task(job_key)
        if not task:
            logger.warning(f"No job found by {job_key}")
            return

        pid = task.meta.get('pid')
        if pid is None:
            raise DispatcherException(f"Cannot abort task {job_key}: pid not found")

        logger.info(f"Cancelling task {job_key} (pid {pid})")
        os.kill(int(pid), signal.SIGTERM)
        time.sleep(0.1)

        try:
            # Code 0 used to check if pid exists.
            os.kill(int(pid), 0)
            raise DispatcherException(f"Job pid {pid} still exists.")
        except OSError:
            # This indicates the process with the given pid was not found
            # This is what we expect to happen.
            pass

