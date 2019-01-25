import abc
import os
from pkg_resources import resource_filename
from typing import Optional, List, Dict, Callable
import base64

from gtmcore.dataset.io import PushResult, PushObject, PullObject, PullResult


class StorageBackend(metaclass=abc.ABCMeta):
    """Parent class for Dataset storage backends"""

    def __init__(self):
        # Optional configuration data that is in the form of string key-value pairs for simplicity and standardization
        # across types. This means Backend implementations are responsible for casting strings to other types if needed.
        # No nesting of values is supported
        self.configuration = dict()

        # Attributes used to store the required keys for a backend
        default_configuration = {'username': "the gigantum username for the logged in user",
                                 'gigantum_bearer_token': "Gigantum bearer token for the current session",
                                 'gigantum_id_token': "Gigantum ID token for the current session"}
        self._required_configuration_keys = {**default_configuration, **self._required_configuration()}

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
        raise NotImplemented

    def _backend_metadata(self) -> dict:
        """Method to specify Storage Backend metadata for each implementation. This is used to render the UI

        Simply implement this method in a child class. Note, 'icon' should be the name of the icon file saved in the
        thumbnails directory. It should be a 128x128 px PNG image.

        return {"storage_type": "a_unique_identifier",
                "name": "My Dataset Type",
                "description": "Short string",
                "readme": "Long string",
                "is_managed": True|False,
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

        with open(icon_file, 'rb') as icf:
            metadata['icon'] = base64.b64encode(icf.read()).decode("utf-8")

        return metadata

    @property
    def is_managed(self):
        return self._backend_metadata().get("is_managed")

    @property
    def is_configured(self) -> bool:
        """A storage backend is configured if all required config items are set"""
        return len(set(self.configuration.keys()) - set(self._required_configuration_keys.keys())) == 0

    @property
    def missing_configuration(self) -> dict:
        missing_keys = list(set(self.configuration.keys()) - set(self._required_configuration_keys.keys()))
        result = dict()
        for key in missing_keys:
            result[key] = self._required_configuration_keys.get(key)

        return result

    def prepare_push(self, dataset, objects: List[PushObject], status_update_fn: Callable) -> None:
        raise NotImplemented

    def push_objects(self, dataset, objects: List[PushObject], status_update_fn: Callable) -> PushResult:
        raise NotImplemented

    def finalize_push(self, dataset, status_update_fn: Callable) -> None:
        raise NotImplemented

    def prepare_pull(self, dataset, objects: List[PullObject], status_update_fn: Callable) -> None:
        raise NotImplemented

    def pull_objects(self, dataset, objects: List[PullObject], status_update_fn: Callable) -> PullResult:
        raise NotImplemented

    def finalize_pull(self, dataset, status_update_fn: Callable) -> None:
        raise NotImplemented
