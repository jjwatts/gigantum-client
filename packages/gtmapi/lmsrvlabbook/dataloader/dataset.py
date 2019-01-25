from typing import List

from promise import Promise
from promise.dataloader import DataLoader

from gtmcore.inventory.inventory import InventoryManager
from lmsrvcore.auth.user import get_logged_in_author


class DatasetLoader(DataLoader):
    """Dataloader for gtmcore.dataset.Dataset instances

    The key for this object is username&owner&dataset_name
    """

    @staticmethod
    def get_dataset_instance(key: str):
        # Get identifying info from key
        username, owner_name, dataset_name = key.split('&')
        lb = InventoryManager().load_dataset(username, owner_name, dataset_name,
                                             author=get_logged_in_author())
        return lb

    def batch_load_fn(self, keys: List[str]):
        """Method to load dataset objects based on a list of unique keys

        Args:
            keys(list(str)): Unique key to identify the dataset

        Returns:

        """
        return Promise.resolve([self.get_dataset_instance(key) for key in keys])
