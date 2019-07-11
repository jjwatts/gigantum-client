from typing import List, Tuple, Dict

from promise import Promise
from promise.dataloader import DataLoader
from gtmcore.environment.utils import get_package_manager
from gtmcore.environment.packagemanager import PackageMetadata
from gtmcore.labbook import LabBook
from gtmcore.logging import LMLogger

logger = LMLogger.get_logger()


class PackageDataloader(DataLoader):
    """Dataloader to manage running package latest version and metadata queries

    The key for this dataloader is  manager&package
    """
    def __init__(self, keys: List[str], labbook: LabBook, username: str) -> None:
        DataLoader.__init__(self)
        self.keys = keys
        self.results: Dict[str, PackageMetadata] = dict()
        self.labbook = labbook
        self.username = username

    def populate_results(self) -> None:
        # Repack key data
        packages: Dict[str, List[Tuple[str, str, str]]] = {'conda2': list(),
                                                           'conda3': list(),
                                                           'pip': list(),
                                                           'apt': list()}
        for key in self.keys:
            manager, package = key.split('&')
            packages[manager].append((manager, package, key))

        for manager in packages.keys():
            package_names = [x[1] for x in packages[manager]]
            if package_names:
                mgr = get_package_manager(manager)

                try:
                    metadata = mgr.get_packages_metadata(package_names, labbook=self.labbook, username=self.username)

                    # save
                    for pkg_input, metadata in zip(packages[manager], metadata):
                        self.results[pkg_input[2]] = metadata

                except ValueError as err:
                    logger.warning(f"An error occurred while looking up {manager} latest versions and metadata: {err}")

    def get_data(self, key: str) -> PackageMetadata:
        if not self.results:
            self.populate_results()

        return self.results[key]

    def batch_load_fn(self, keys: List[str]):
        """Method to load labbook objects based on a list of unique keys

        Args:
            keys(list(str)): Unique key to identify the labbook

        Returns:

        """
        # Resolve objects
        return Promise.resolve([self.get_data(key) for key in keys])
