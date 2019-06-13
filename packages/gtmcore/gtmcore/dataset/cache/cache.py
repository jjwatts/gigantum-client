import abc
import os
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from gtmcore.dataset import Dataset


class CacheManager(metaclass=abc.ABCMeta):
    """Abstract class to manage the dataset object cache.

    An object cache is the location where files are materialized (as unique objects). These objects are hardlinked
    into directories representing a revision of the dataset (with the appropriate filenames).

    """

    def __init__(self, dataset: 'Dataset', username: Optional[str]) -> None:
        """

        Args:
            dataset: Current dataset object
            username: Username of current logged in user, which may be required by the CacheManager implementation
        """
        self.dataset = dataset
        self.username = username
        self.initialize()

    @property
    def current_revision_dir(self) -> str:
        """Method to return the directory containing files for the current dataset revision

        Returns:
            str
        """
        return os.path.join(self.cache_root, self.dataset.git.repo.head.commit.hexsha)

    @property
    def cache_root(self) -> str:
        """The location of the file cache root

        Returns:
            str
        """
        raise NotImplemented

    def initialize(self) -> None:
        """Method to configure a file cache for use. this can include creating/provisioning resources or just loading
        things

        Returns:
            None
        """
        raise NotImplemented
