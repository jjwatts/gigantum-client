from gtmcore.dataset import Dataset
from gtmcore.dataset.storage.backend import UnmanagedStorageBackend
from typing import List, Dict, Callable, Optional
import os
import json

from gtmcore.dataset.io import PullResult, PullObject
from gtmcore.logging import LMLogger
from gtmcore.configuration import Configuration
from gtmcore.dataset.manifest.manifest import Manifest, StatusResult

import boto3
import botocore
from botocore.client import Config
from botocore import UNSIGNED

logger = LMLogger.get_logger()


class PublicS3Bucket(UnmanagedStorageBackend):

    def _backend_metadata(self) -> dict:
        """Method to specify Storage Backend metadata for each implementation. This is used to render the UI

        Simply implement this method in a child class. Note, 'icon' should be the name of the icon file saved in the
        thumbnails directory. It should be a 128x128 px PNG image.

        Returns:
            dict
        """
        return {"storage_type": "public_s3_bucket",
                "name": "Public S3 Bucket",
                "description": "A type to use data stored in a public S3 bucket",
                "tags": ["unmanaged", "s3", "aws"],
                "icon": "s3.png",
                "url": "https://docs.gigantum.com",
                "readme": """This dataset type simply loads data from a public S3 bucket. It supports automatic 
synchronization with S3 so you don't need to manually enter any information other than the bucket name. 

Due to the possibility of storing lots of data, when updating you can optionally keep all data locally or not. Because
 all files must be hashed when adding to the dataset, they all need to be downloaded by the creator. Once added
 to the dataset, partial downloads of the data is supported. To learn more, check out the docs here:
 [https://docs.gigantum.com](https://docs.gigantum.com)
"""}

    def _required_configuration(self) -> List[Dict[str, str]]:
        """A private method to return a list of parameters that must be set for a backend to be fully configured

        The format is a list of dictionaries, e.g.:

        [
          {
            "parameter": "server",
            "description": "URL of the remote server",
            "type": "str"
          },
          {
            "parameter": "username",
            "description": "The current logged in username",
            "type": "str"
          }
        ]

        "type" must be either `str` or `bool`

        There are 3 parameters that are always automatically populated:
           - username: the gigantum username for the logged in user
           - gigantum_bearer_token: the gigantum bearer token for the current session
           - gigantum_id_token: the gigantum id token for the current session
        """
        return [{'parameter': "Bucket Name",
                 'description': "Name of the public S3 Bucket",
                 'type': "str"
                 },
                {'parameter': "Prefix",
                 'description': "Optional prefix inside the bucket (e.g. `prefix1/sub3/`)",
                 'type': "str"
                 }
                ]

    def _get_s3_config(self):
        """Method to get the bucket configuration"""
        bucket = self.configuration.get("Bucket Name")
        if not bucket:
            raise ValueError("Bucket Name required to confirm configuration")

        if not self.configuration.get("Prefix"):
            prefix = ""
        else:
            prefix = self.configuration.get("Prefix")

        return bucket, prefix

    def _get_client(self):
        return boto3.client('s3', config=Config(signature_version=UNSIGNED))

    def confirm_configuration(self, dataset) -> Optional[str]:
        """Method to verify a configuration and optionally allow the user to confirm before proceeding

        Should return the desired confirmation message if there is one. If no confirmation is required/possible,
        return None

        """
        bucket, prefix = self._get_s3_config()
        client = self._get_client()

        # Confirm bucket exists and is public
        try:
            client.head_bucket(Bucket=bucket)
        except botocore.client.ClientError:
            raise ValueError(f"Access denied to {bucket}. Double check Bucket Name")

        # List number of files and total size
        paginator = client.get_paginator('list_objects_v2')
        response_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

        num_bytes = 0
        num_objects = 0
        for x in response_iterator:
            for item in x.get("Contents"):
                num_bytes += int(item.get('Size'))
                num_objects += 1

        confirm_message = f"Creating this dataset will download {num_objects}" \
            f" files and consume {(float(num_bytes)/(10**9)):.2f} GB of local storage. Do you wish to continue?"

        return confirm_message

    def prepare_pull(self, dataset, objects: List[PullObject]) -> None:
        """Gigantum Object Service only requires that the user's tokens have been set

        Args:
            dataset: The current dataset instance
            objects: A list of PushObjects to be pulled
            status_update_fn: A function to update status during pushing

        Returns:
            None
        """
        if not self.is_configured:
            raise ValueError("S3 backend must be fully configured before running pull.")

    def finalize_pull(self, dataset) -> None:
        pass

    def _get_etag_file(self, dataset) -> str:
        """Helper to get the etag file, tracking S3 object hashes"""
        return os.path.join(dataset.root_dir, '.gigantum', 'etag_cache.json')

    def _load_etag_data(self, dataset) -> dict:
        """Helper to load the saved etag data

        Returns:

        """
        etag_file = self._get_etag_file(dataset)
        if os.path.exists(etag_file):
            with open(etag_file, 'rt') as ef:
                data = json.load(ef)
        else:
            data = dict()

        return data

    def _save_etag_data(self, dataset, etag_data: dict) -> None:
        etag_file = self._get_etag_file(dataset)
        with open(etag_file, 'wt') as ef:
            json.dump(etag_data, ef)

    def pull_objects(self, dataset: Dataset, objects: List[PullObject],
                     progress_update_fn: Callable) -> PullResult:
        """High-level method to simply link files from the source dir to the object directory to the revision directory

        Args:
            dataset: The current dataset
            objects: A list of PullObjects the enumerate objects to push
            progress_update_fn: A callable with arg "completed_bytes" (int) indicating how many bytes have been
                                downloaded in since last called

        Returns:
            PullResult
        """
        client = self._get_client()
        bucket, prefix = self._get_s3_config()

        backend_config = dataset.client_config.config['datasets']['backends'][dataset.backend.storage_type]
        chunk_size = backend_config['download_chunk_size']
        success = list()
        failure = list()
        message = f"Downloaded {len(objects)} objects successfully."

        for obj in objects:
            # Get object
            response = client.get_object(Bucket=bucket,
                                         Key=os.path.join(prefix, obj.dataset_path))

            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                # Save file
                with open(obj.object_path, 'wb') as out_file:
                    for cnt, chunk in enumerate(response['Body'].iter_chunks(chunk_size=chunk_size)):
                        out_file.write(chunk)
                        progress_update_fn(len(chunk))

                success.append(obj)
            else:
                failure.append(obj)

        if len(failure) > 0:
            message = f"Downloaded {len(success)} objects successfully, but {len(failure)} failed. Check results."

        # link from object dir through to revision dir
        m = Manifest(dataset, self.configuration.get('username'))
        m.link_revision()

        return PullResult(success=success,
                          failure=failure,
                          message=message)

    def can_update_from_remote(self) -> bool:
        """Property indicating if this backend can automatically update its contents to the latest on the remote

        Returns:
            bool
        """
        return True

    def update_from_remote(self, dataset, status_update_fn: Callable) -> None:
        """Optional method that updates the dataset by comparing against the remote. Not all unmanaged dataset backends
        will be able to do this.

        Args:
            dataset: Dataset object
            status_update_fn: A callable, accepting a string for logging/providing status to the UI

        Returns:
            None
        """
        if 'username' not in self.configuration:
            raise ValueError("Dataset storage backend requires current logged in username to verify contents")
        m = Manifest(dataset, self.configuration.get('username'))

        # Walk remote checking etags with cached versions
        etag_data = self._load_etag_data(dataset)

        bucket, prefix = self._get_s3_config()
        client = self._get_client()

        paginator = client.get_paginator('list_objects_v2')
        response_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

        all_files = list()
        added_files = list()
        modified_files = list()
        print_cnt = 0

        revision_dir = os.path.join(m.cache_mgr.cache_root, m.dataset_revision)
        for x in response_iterator:
            if print_cnt == 0:
                status_update_fn("Processing Bucket Contents, please wait.")
                print_cnt += 1
            elif print_cnt == 1:
                status_update_fn("Processing Bucket Contents, please wait..")
                print_cnt += 1
            else:
                status_update_fn("Processing Bucket Contents, please wait...")
                print_cnt = 0

            for item in x.get("Contents"):
                key = item['Key']
                all_files.append(key)
                if key in m.manifest:
                    # Object already tracked
                    if etag_data[key] != item['ETag']:
                        # Object has been modified since last update
                        modified_files.append(key)
                        if os.path.exists(os.path.join(revision_dir, key)):
                            # Delete current version
                            os.remove(os.path.join(revision_dir, key))

                        if key[-1] == "/":
                            # is a "directory
                            os.makedirs(os.path.join(revision_dir, key), exist_ok=True)
                        else:
                            client.download_file(bucket, key, os.path.join(revision_dir, key))
                else:
                    # New Object
                    etag_data[key] = item['ETag']
                    added_files.append(key)

                    if key[-1] == "/":
                        # is a "directory
                        os.makedirs(os.path.join(revision_dir, key), exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(os.path.join(revision_dir, key)), exist_ok=True)
                        client.download_file(bucket, key, os.path.join(revision_dir, key))

        deleted_files = sorted(list(set(m.manifest.keys()).difference(all_files)))

        # Create StatusResult to force modifications
        status = StatusResult(created=added_files, modified=modified_files, deleted=deleted_files)

        self._save_etag_data(dataset, etag_data)

        # Run local update
        self.update_from_local(dataset, status_update_fn, status_result=status)
