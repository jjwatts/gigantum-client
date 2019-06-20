from typing import Optional, List

from gtmcore.dispatcher.dispatcher import Dispatcher, JobKey, JobStatus
from gtmcore.dataset.io import PushObject


class BackgroundDownloadJob:
    """Class to help track background file download jobs"""
    def __init__(self, dispatcher: Dispatcher, keys: list, job_key: JobKey) -> None:
        self.dispatcher = dispatcher
        self.keys = keys
        self.job_key = job_key

        self._job_status: Optional[JobStatus] = None

    @property
    def is_running(self) -> bool:
        """Boolean indicating if the job has been scheduled and is running"""
        if not self._job_status:
            return False

        if self._job_status.status in ["started", "queued"]:
            return True
        else:
            return False

    @property
    def is_failed(self) -> bool:
        """Boolean indicating if the job has failed"""
        if not self._job_status:
            return False

        if self._job_status.status == "failed":
            return True
        else:
            return False

    @property
    def is_complete(self) -> bool:
        """Boolean indicating if the job has completed"""
        if not self._job_status:
            return False

        if self._job_status.status == "finished":
            return True
        else:
            return False

    @property
    def completed_bytes(self) -> int:
        """Integer indicating how many bytes this job has completed"""
        if not self._job_status:
            return 0

        if self._job_status.meta.get('completed_bytes'):
            return int(self._job_status.meta['completed_bytes'])
        else:
            return 0

    def get_failed_keys(self) -> List[str]:
        """Get the failed keys from the underlying call to `pull_objects`"""
        failure_keys: List[str] = list()
        if self._job_status:
            if 'failure_keys' in self._job_status.meta:
                fail_str = self._job_status.meta['failure_keys']
                if len(fail_str) > 0:
                    failure_keys = fail_str.split(',')

        return failure_keys

    def refresh_status(self) -> bool:
        """Method to query the dispatcher for the job's state. If the job failed, self.failure_count will increment.
        The method also returns self.is_complete after the status update is complete

        Returns:
            bool
        """
        if self.job_key:
            self._job_status = self.dispatcher.query_task(self.job_key)

        return self.is_complete


class BackgroundUploadJob:
    """Class to help track background file upload jobs"""
    def __init__(self, dispatcher: Dispatcher, objs: List[PushObject], job_key: JobKey) -> None:
        self.dispatcher = dispatcher
        self.objs = objs
        self.job_key = job_key

        self._job_status: Optional[JobStatus] = None

    @property
    def is_running(self) -> bool:
        """Boolean indicating if the job has been scheduled and is running"""
        if not self._job_status:
            return False

        if self._job_status.status in ["started", "queued"]:
            return True
        else:
            return False

    @property
    def is_failed(self) -> bool:
        """Boolean indicating if the job has failed"""
        if not self._job_status:
            return False

        if self._job_status.status == "failed":
            return True
        else:
            return False

    @property
    def is_complete(self) -> bool:
        """Boolean indicating if the job has completed"""
        if not self._job_status:
            return False

        if self._job_status.status == "finished":
            return True
        else:
            return False

    @property
    def completed_bytes(self) -> int:
        """Integer indicating how many bytes this job has completed"""
        if not self._job_status:
            return 0

        if self._job_status.meta.get('completed_bytes'):
            return int(self._job_status.meta['completed_bytes'])
        else:
            return 0

    def get_failed_objects(self) -> List[PushObject]:
        """Get the failed objects from the underlying call to `pull_objects`"""
        failed_objs: List[PushObject] = list()
        if self._job_status:
            if 'failures' in self._job_status.meta:
                fail_str = self._job_status.meta['failures']
                if len(fail_str) > 0:
                    failure_data = fail_str.split(',')
                    for fd in failure_data:
                        obj_path, dataset_path, revision = fd.split("|")
                        failed_objs.append(PushObject(object_path=obj_path,
                                                      dataset_path=dataset_path,
                                                      revision=revision))

        return failed_objs

    def refresh_status(self) -> bool:
        """Method to query the dispatcher for the job's state. If the job failed, self.failure_count will increment.
        The method also returns self.is_complete after the status update is complete

        Returns:
            bool
        """
        if self.job_key:
            self._job_status = self.dispatcher.query_task(self.job_key)

        return self.is_complete
