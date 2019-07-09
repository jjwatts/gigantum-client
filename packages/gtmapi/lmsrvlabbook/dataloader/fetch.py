from typing import List

from promise import Promise
from promise.dataloader import DataLoader

from gtmcore.inventory.inventory import InventoryManager
from gtmcore.configuration.utils import call_subprocess


class FetchLoader(DataLoader):
    """Dataloader to fetch a project or dataset once per request if needed

    The key for this object is (labbook|dataset)&username&owner&repository_name
    """

    @staticmethod
    def run_fetch(key: str):
        # Get identifying info from key
        repository_type, username, owner_name, repository_name = key.split('&')
        if repository_type == 'labbook':
            repo = InventoryManager().load_labbook(username, owner_name, repository_name)
        elif repository_type == 'dataset':
            repo = InventoryManager().load_dataset(username, owner_name, repository_name)
        else:
            raise ValueError(f"Unsupported repository type: {repository_type}")

        if repo.remote:
            # If no remote, can't fetch!
            call_subprocess(['git', 'fetch'], cwd=repo.root_dir).strip()

        return None

    def batch_load_fn(self, keys: List[str]):
        """Method to load dataset objects based on a list of unique keys

        Args:
            keys(list(str)): Unique key to identify the dataset

        Returns:

        """
        return Promise.resolve([self.run_fetch(key) for key in keys])
