import asyncio
from gtmcore.dataset import Dataset
from gtmcore.dataset.storage.backend import StorageBackend
from typing import Optional, List, Dict, Callable, Tuple
import requests
import time
import shutil
import os

from gtmcore.dataset.io import PushResult, PushObject, PullResult, PullObject
from gtmcore.logging import LMLogger

logger = LMLogger.get_logger()


class GigantumObjectStore(StorageBackend):

    def _backend_metadata(self) -> dict:
        """Method to specify Storage Backend metadata for each implementation. This is used to render the UI

        Simply implement this method in a child class. Note, 'icon' should be the name of the icon file saved in the
        thumbnails directory. It should be a 128x128 px PNG image.

        Returns:
            dict
        """
        return {"storage_type": "gigantum_object_v1",
                "name": "Gigantum Cloud",
                "description": "Scalable Dataset storage provided by your Gigantum account",
                "tags": ["gigantum"],
                "icon": "gigantum_object_storage.png",
                "url": "https://docs.gigantum.com",
                "is_managed": True,
                "readme": """Gigantum Cloud Datasets are backed by a scalable object storage service that is linked to
your Gigantum account and credentials. It provides efficient storage at the file level and works seamlessly with the 
Client.

This dataset type is fully managed. That means as you modify data, each version will be tracked independently. Syncing
to Gigantum Cloud will count towards your storage quota and include all versions of files.
"""}

    def _required_configuration(self) -> Dict[str, str]:
        """A private method to return a list of keys that must be set for a backend to be fully configured

        The format is a dict of keys and descriptions. E.g.

        {
          "server": "The host name for the remote server",
          "username": "The current logged in username"

        }

        There are 3 keys that are always automatically populated:
           - username: the gigantum username for the logged in user
           - gigantum_bearer_token: the gigantum bearer token for the current session
           - gigantum_id_token: the gigantum id token for the current session

        Returns:

        """
        # No additional config required beyond defaults
        return dict()

    @staticmethod
    def _get_service_endpoint(dataset: Dataset) -> str:
        """

        Args:
            dataset:

        Returns:

        """
        default_remote = dataset.client_config.config['git']['default_remote']
        obj_service = None
        for remote in dataset.client_config.config['git']['remotes']:
            if default_remote == remote:
                obj_service = dataset.client_config.config['git']['remotes'][remote]['object_service']
                break

        if not obj_service:
            raise ValueError('Object Service endpoint not configured.')

        return f"https://{obj_service}"

    def _get_request_headers(self) -> dict:
        """Method to generate the request headers, including authorization information

        Returns:

        """
        return {'Authorization': f"Bearer {self.configuration.get('gigantum_bearer_token')}",
                'Identity': self.configuration.get("gigantum_id_token"),
                'Accept': 'application/json'}

    def _gen_push_url(self, dataset: Dataset, object_id: str) -> Tuple[str, str]:
        """

        Args:
            dataset:
            object_id:

        Returns:

        """
        url = f"{self._get_service_endpoint(dataset)}/{dataset.namespace}/{dataset.name}/{object_id}"

        presigned_url: Optional[str] = None
        encryption_key: Optional[str] = None
        for ii in range(4):
            # Get signed url with backoff
            response = requests.put(url, headers=self._get_request_headers(), timeout=20)
            if response.status_code == 200:
                presigned_url = response.json().get("presigned_url")
                encryption_key = response.json().get("key_id")
                break
            logger.warning(f"Failed to get signed URL for PUT at {url}. Retrying in {2**ii} seconds")
            time.sleep(2**ii)

        if not presigned_url or not encryption_key:
            raise IOError(f"Failed to get signed URL for PUT at {url}")

        return presigned_url, encryption_key

    def _gen_pull_url(self, dataset: Dataset, object_id: str) -> str:
        """

        Args:
            dataset:
            object_id:

        Returns:

        """
        url = f"{self._get_service_endpoint(dataset)}/{dataset.namespace}/{dataset.name}/{object_id}"

        presigned_url = None
        for ii in range(4):
            # Get signed url with backoff
            response = requests.get(url, headers=self._get_request_headers(), timeout=20)
            if response.status_code == 200:
                presigned_url = response.json().get("presigned_url")
                break
            logger.warning(f"Failed to get signed URL for GET at {url}. Retrying in {2**ii} seconds")
            time.sleep(2**ii)

        if not presigned_url:
            raise IOError(f"Failed to get signed URL for GET at {url}")

        return presigned_url

    def prepare_push(self, dataset, objects: List[PushObject], status_update_fn: Callable) -> None:
        """Gigantum Object Service only requires that the user's tokens have been set

        Args:
            dataset: The current dataset instance
            objects: A list of PushObjects to be pushed
            status_update_fn: A function to update status during pushing

        Returns:
            None
        """
        if 'username' not in self.configuration.keys():
            raise ValueError("Username must be set to push objects to Gigantum Cloud")

        if 'gigantum_bearer_token' not in self.configuration.keys():
            raise ValueError("User must have valid session to push objects to Gigantum Cloud")

        if 'gigantum_id_token' not in self.configuration.keys():
            raise ValueError("User must have valid session to push objects to Gigantum Cloud")

        status_update_fn(f"Ready to push objects to {dataset.namespace}/{dataset.name}")

    def push_objects(self, dataset: Dataset, objects: List[PushObject], status_update_fn: Callable) -> PushResult:
        """

        Args:
            dataset:
            objects:
            status_update_fn:

        Returns:

        """
        successes = list()
        failures = list()
        message = "Successfully pushed all objects"
        for cnt, obj in enumerate(objects):
            try:
                status_update_fn(f"Pushing {cnt + 1} of {len(objects)} objects")

                # Get Signed URL
                _, obj_id = obj.object_path.rsplit('/', 1)
                url, encryption_key = self._gen_push_url(dataset, obj_id)

                # Put File
                with open(obj.object_path, 'rb') as data:

                    response = requests.put(url,
                                            data=data,
                                            headers={'x-amz-server-side-encryption': 'aws:kms',
                                                     'x-amz-server-side-encryption-aws-kms-key-id': encryption_key})

                    if response.status_code != 200:
                        raise IOError(f"Failed to push object. Backend returned {response.status_code}")

            except Exception as err:
                logger.exception(err)
                status_update_fn(f"Failed to push object {cnt + 1}. Continuing...")
                message = "Some objects failed to push. Check results."
                failures.append(obj)
                continue
            successes.append(obj)

        return PushResult(success=successes, failure=failures, message=message)

    def finalize_push(self, dataset, status_update_fn: Callable) -> None:
        status_update_fn(f"Done pushing objects to {dataset.namespace}/{dataset.name}")

    def prepare_pull(self, dataset, objects: List[PullObject], status_update_fn: Callable) -> None:
        """Gigantum Object Service only requires that the user's tokens have been set

        Args:
            dataset: The current dataset instance
            objects: A list of PushObjects to be pulled
            status_update_fn: A function to update status during pushing

        Returns:
            None
        """
        if 'username' not in self.configuration.keys():
            raise ValueError("Username must be set to push objects to Gigantum Cloud")

        if 'gigantum_bearer_token' not in self.configuration.keys():
            raise ValueError("User must have valid session to push objects to Gigantum Cloud")

        if 'gigantum_id_token' not in self.configuration.keys():
            raise ValueError("User must have valid session to push objects to Gigantum Cloud")

        status_update_fn(f"Ready to pull objects from {dataset.namespace}/{dataset.name}")

    def pull_objects(self, dataset: Dataset, objects: List[PullObject], status_update_fn: Callable) -> PullResult:
        """

        Args:
            dataset:
            objects:
            status_update_fn:

        Returns:

        """
        successes = list()
        failures = list()
        message = "Successfully pulled all objects"
        for cnt, obj in enumerate(objects):
            try:
                # Get Signed URL
                obj_dir, obj_id = obj.object_path.rsplit('/', 1)
                url = self._gen_pull_url(dataset, obj_id)

                os.makedirs(obj_dir, exist_ok=True)  # type: ignore

                # Pull File
                r = requests.get(url, stream=True)

                if r.status_code != 200:
                    raise IOError(f"Failed to download object. Status code: {r.status_code}")

                with open(obj.object_path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)

                status_update_fn(f"Pulled {cnt+1} of {len(objects)} objects")

            except Exception as err:
                logger.exception(err)
                status_update_fn(f"Failed to pull object {cnt + 1} of {len(objects)}. Continuing...")
                message = "Some objects failed to pull. Check results."
                failures.append(obj)
                continue
            successes.append(obj)

        return PullResult(success=successes, failure=failures, message=message)

    def finalize_pull(self, dataset, status_update_fn: Callable) -> None:
        status_update_fn(f"Done pulling objects from {dataset.namespace}/{dataset.name}")
