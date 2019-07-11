import abc
import os
from pkg_resources import resource_filename
from typing import Optional, List, Dict, Callable, Tuple
import base64
import asyncio
import shutil
import copy

from gtmcore.dataset.io import PushResult, PushObject, PullObject, PullResult
from gtmcore.dataset.manifest.manifest import Manifest, StatusResult
from gtmcore.dataset.manifest.eventloop import get_event_loop


class StorageBackend(metaclass=abc.ABCMeta):
    """Parent class for Dataset storage backends"""

    def __init__(self):
        # Optional configuration data that is in the form of key-value pairs
        # No nesting of values is supported
        # Configuration is populated from the Dataset at runtime (via a file and in-memory secrets)
        self.configuration = dict()

        # Attributes used to store the required keys for a backend
        self._required_configuration_params = [{'parameter': 'username',
                                                'description': "the Gigantum username for the logged in user",
                                                'type': 'str'
                                                },
                                               {'parameter': 'gigantum_bearer_token',
                                                'description': "Gigantum bearer token for the current session",
                                                'type': 'str'
                                                },
                                               {'parameter': 'gigantum_id_token',
                                                'description': "Gigantum ID token for the current session",
                                                'type': 'str'
                                                }]
        if self._required_configuration():
            # If additional config required, append
            self._required_configuration_params.extend(self._required_configuration())

    @property
    def storage_type(self) -> str:
        """Return the string identifier for the dataset's storage class"""
        return self._backend_metadata()['storage_type']

    def _backend_metadata(self) -> dict:
        """Method to specify Storage Backend metadata for each implementation. This is used to render the UI

        Simply implement this method in a child class. Note, 'icon' should be the name of the icon file saved in the
        thumbnails directory. It should be a 128x128 px PNG image.

        return {"storage_type": "a_unique_identifier",
                "name": "My Dataset Type",
                "description": "Short string",
                "readme": "Long string",
                "icon": "my_icon.png",
                "url": "http://moreinfo.com"
                }

        Returns:
            dict
        """
        raise NotImplemented

    @property
    def metadata(self):
        """

        Returns:

        """
        metadata = self._backend_metadata()

        dataset_pkg = resource_filename('gtmcore', 'dataset')
        icon_file = os.path.join(dataset_pkg, 'storage', 'thumbnails', metadata['icon'])

        metadata['is_managed'] = self.is_managed

        with open(icon_file, 'rb') as icf:
            metadata['icon'] = base64.b64encode(icf.read()).decode("utf-8")

        return metadata

    @property
    def is_managed(self):
        """Boolean property indicating if this is a managed dataset type"""
        return isinstance(self, ManagedStorageBackend)

    def set_default_configuration(self, username: str, bearer_token: str, id_token: str) -> None:
        """Method to configure default keys. This should be called from API and other situations where
        remote ops are desired and the bearer and ID tokens exist

        Args:
            username: current logged in username
            bearer_token: current session bearer token (gigantum auth service)
            id_token: current session id token (gigantum auth service)

        Returns:
            None
        """
        self.configuration['username'] = username
        self.configuration['gigantum_bearer_token'] = bearer_token
        self.configuration['gigantum_id_token'] = id_token

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
        raise NotImplemented

    def confirm_configuration(self, dataset) -> Optional[str]:
        """Method to verify a configuration and optionally allow the user to confirm before proceeding

        Should return the desired confirmation message if there is one. If no confirmation is required/possible,
        return None

        """
        raise NotImplemented

    @property
    def is_configured(self) -> bool:
        """Boolean property indicating if a storage backend has all required config items set"""
        return len(self.missing_configuration) == 0

    @property
    def missing_configuration(self) -> List[Dict[str, str]]:
        """Property returning the missing configuration parameters"""
        configured_params = list(self.configuration.keys())

        missing_params = list()
        for param in self._required_configuration_params:
            if param['parameter'] not in configured_params:
                missing_params.append(param)

        return missing_params

    @property
    def safe_current_configuration(self) -> List[Dict[str, str]]:
        """Property returning the current configuration, excluding the default parameters which include secrets"""
        current_params = list()
        for param in self._required_configuration_params:
            if param['parameter'] in ['username', 'gigantum_bearer_token', 'gigantum_id_token']:
                continue
            param['value'] = self.configuration.get(param['parameter'])
            current_params.append(param)

        return current_params

    def prepare_pull(self, dataset, objects: List[PullObject]) -> None:
        """Method to prepare a backend for pulling objects locally

        Args:
            dataset: The dataset instance
            objects: A list of PullObjects, indicating which objects to pull
            status_update_fn: A callable, accepting a string for logging/providing status to the UI

        Returns:

        """
        raise NotImplemented

    def pull_objects(self, dataset, objects: List[PullObject], progress_update_fn: Callable) -> PullResult:
        """Method to pull objects locally

        Args:
            dataset: The dataset instance
            objects: A list of PullObjects, indicating which objects to pull
            progress_update_fn: A callable with arg "completed_bytes" (int) indicating how many bytes have been
                                downloaded in since last called

        Returns:
            PullResult
        """
        raise NotImplemented

    def finalize_pull(self, dataset) -> None:
        """Method to finalize and cleanup a backend after pulling objects locally

        Args:
            dataset: The dataset instance
            status_update_fn: A callable, accepting a string for logging/providing status to the UI

        Returns:

        """
        raise NotImplemented

    def hash_file_key_list(self, dataset, keys):
        m = Manifest(dataset, self.configuration.get('username'))
        loop = get_event_loop()
        hash_task = asyncio.ensure_future(m.hasher.hash(keys))
        loop.run_until_complete(asyncio.gather(hash_task))
        return hash_task.result()

    def verify_contents(self, dataset, status_update_fn: Callable) -> List[str]:
        """Method to verify the hashes of all local files and indicate if they have changed

        Args:
            dataset: Dataset object
            status_update_fn: A callable, accepting a string for logging/providing status to the UI

        Returns:
            list
        """
        if 'username' not in self.configuration:
            raise ValueError("Dataset storage backend requires current logged in username to verify contents")

        m = Manifest(dataset, self.configuration.get('username'))
        keys_to_verify = list()
        for item in m.manifest:
            if os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, item)):
                # File exists locally
                keys_to_verify.append(item)

        # re-hash files
        status_update_fn(f"Validating contents of {len(keys_to_verify)} files. Please wait.")
        updated_hashes = self.hash_file_key_list(dataset, keys_to_verify)

        modified_items = list()
        for key, new_hash in zip(keys_to_verify, updated_hashes):
            item = m.manifest.get(key)
            if item:
                if new_hash != item.get('h'):
                    modified_items.append(key)

        if modified_items:
            status_update_fn(f"Integrity check complete. {len(modified_items)} files have been modified.")
        else:
            status_update_fn(f"Integrity check complete. No files have been modified.")

        return modified_items


class ManagedStorageBackend(StorageBackend):
    """Parent class for Managed Dataset storage backends"""

    @property
    def client_should_dedup_on_push(self) -> bool:
        """Property to indicate if the client should perform deduplication of objects based on content hashing on push

        This effectively removes duplicate objects from the list of PushObjects before calling prepare_push() and
        push_objects(). If two different files have the same contents only 1 copy will be pushed.

        Returns:
            bool
        """
        raise NotImplemented

    def prepare_push(self, dataset, objects: List[PushObject]) -> None:
        """Method to prepare a backend for pushing objects to the remote storage backend

        Args:
            dataset: The dataset instance
            objects: A list of PushObjects, indicating which objects to push
            status_update_fn: A callable, accepting a string for logging/providing status to the UI

        Returns:

        """
        raise NotImplemented

    def push_objects(self, dataset, objects: List[PushObject], progress_update_fn: Callable) -> PushResult:
        """Method to push objects to the remote storage backend

        Args:
            dataset: The dataset instance
            objects: A list of PushObject, indicating which objects to push
            progress_update_fn: A callable with arg "completed_bytes" (int) indicating how many bytes have been
                                uploaded in since last called

                                      
        Returns:

        """
        raise NotImplemented

    def finalize_push(self, dataset) -> None:
        """Method to finalize and cleanup a backend after pushing objects to the remote storage backend

        Args:
            dataset: The dataset instance
            status_update_fn: A callable, accepting a string for logging/providing status to the UI

        Returns:

        """
        raise NotImplemented

    def delete_contents(self, dataset) -> None:
        """Method to remove the contents of a dataset from the storage backend, should only work if managed

        Args:
            dataset: Dataset object

        Returns:
            None
        """
        raise NotImplemented


class UnmanagedStorageBackend(StorageBackend):
    """Parent class for Unmanaged Dataset storage backends"""

    def update_from_local(self, dataset, status_update_fn: Callable,
                          verify_contents: bool = False,
                          status_result: Optional[StatusResult] = None) -> None:
        """Method to update the dataset manifest for changed files that exists locally

        Args:
            dataset: Dataset object
            status_update_fn: A callable, accepting a string for logging/providing status to the UI
            verify_contents: Boolean indicating if "verify_contents" should be run, and the results added to modified
            status_result: Optional StatusResult object to include in the update (typically from update_from_remote())

        Returns:
            None
        """
        if 'username' not in self.configuration:
            raise ValueError("Dataset storage backend requires current logged in username to verify contents")
        m = Manifest(dataset, self.configuration.get('username'))

        status_update_fn("Updating Dataset manifest from local file state.")

        if status_result is not None:
            if status_result.modified is not None:
                modified_keys = copy.deepcopy(status_result.modified)
            else:
                modified_keys = list()
        else:
            modified_keys = list()

        if verify_contents:
            modified_keys.extend(self.verify_contents(dataset, status_update_fn))

        # Create StatusResult to force modifications
        if status_result:
            created_result = copy.deepcopy(status_result.created)
            # Check if any directories got created
            for key in status_result.created:
                if key[-1] != '/':
                    # a file
                    if os.path.dirname(key) not in m.manifest:
                        # Add the directory to the manifest
                        created_result.append(f"{os.path.dirname(key)}/")

            created_result = list(set(created_result))
            if '/' in created_result:
                created_result.remove('/')

            # Combine a previous StatusResult object (typically from "update_from_remote")
            status = StatusResult(created=created_result,
                                  modified=modified_keys,
                                  deleted=status_result.deleted)
        else:
            status = StatusResult(created=[], modified=modified_keys, deleted=[])

        # Update the manifest
        previous_revision = m.dataset_revision

        m.update(status)
        m.create_update_activity_record(status)

        # Link the revision dir
        m.link_revision()
        if os.path.isdir(os.path.join(m.cache_mgr.cache_root, previous_revision)):
            shutil.rmtree(os.path.join(m.cache_mgr.cache_root, previous_revision))

        status_update_fn("Update complete.")

    @property
    def can_update_from_remote(self) -> bool:
        """Property indicating if this backend can automatically update its contents to the latest on the remote

        Returns:
            bool
        """
        raise NotImplemented

    def update_from_remote(self, dataset, status_update_fn: Callable) -> None:
        """Optional method that updates the dataset by comparing against the remote. Not all unmanaged dataset backends
        will be able to do this.

        Args:
            dataset: Dataset object
            status_update_fn: A callable, accepting a string for logging/providing status to the UI

        Returns:
            None
        """
        raise NotImplemented
