import os
import shutil
import uuid
import json
import datetime
from natsort import natsorted
from pkg_resources import resource_filename

from typing import Optional, Generator, List, Tuple, Dict

from gtmcore.exceptions import GigantumException
from gtmcore.labbook.schemas import CURRENT_SCHEMA as LABBOOK_CURRENT_SCHEMA
from gtmcore.dataset.schemas import CURRENT_SCHEMA as DATASET_CURRENT_SCHEMA
from gtmcore.gitlib import GitAuthor
from gtmcore.logging import LMLogger
from gtmcore.configuration import Configuration
from gtmcore.configuration.utils import call_subprocess
from gtmcore.labbook.labbook import LabBook
from gtmcore.inventory.branching import BranchManager
from gtmcore.dataset.dataset import Dataset

logger = LMLogger.get_logger()


class InventoryException(GigantumException):
    pass


class InventoryManager(object):
    """ This class absorbs the complexity of accepting data structures into the client's
        working directory. We need this class because interacting with the "inventory"
        (i.e., the tree of labbooks located in the user's working directory) can be
        a messy and error-prone process. Any other functionality that needs to insert
        data into the inventory no longer needs to be aware of any specifics of the internal
        structure of it or worry about cleanup. """

    def __init__(self, config_file: Optional[str] = None) -> None:
        self.config_file = config_file
        cfg = Configuration(self.config_file)
        self.inventory_root = os.path.expanduser(cfg.config['git']['working_directory'])

    def __str__(self) -> str:
        return f'<InventoryManager: {self.inventory_root}>'

    def __eq__(self, other) -> bool:
        return isinstance(other, InventoryManager) \
               and self.inventory_root == other.inventory_root

    def query_labbook_owner(self, labbook: LabBook) -> str:
        """Returns the LabBook's owner in the Inventory. """
        tokens = labbook.root_dir.rsplit('/', 3)
        if tokens[-2] != 'labbooks':
            raise InventoryException(f'Unexpected root in {str(labbook)}')
        return tokens[-3]

    def _put_labbook(self, path: str, username: str, owner: str) -> LabBook:
        # Validate that given path contains labbook
        temp_lb = self.load_labbook_from_directory(path)

        p = os.path.join(self.inventory_root, username, owner, 'labbooks')
        dname = os.path.basename(path)
        if os.path.exists(p) and dname in os.listdir(p):
            raise InventoryException(f"Project directory {dname} already exists")

        if not os.path.exists(p):
            os.makedirs(p, exist_ok=True)

        if os.path.exists(os.path.join(p, dname)):
            raise InventoryException(f"Project directory {dname} already exists")

        final_path = shutil.move(path, p)
        assert os.path.dirname(final_path) != 'labbooks', \
               f"shutil.move used incorrectly"

        lb = self.load_labbook_from_directory(final_path)
        return lb

    def put_labbook(self, path: str, username: str, owner: str) -> LabBook:
        """ Take given path to a candidate labbook and insert it
        into its proper place in the file system.

        Args:
            path: Path to a given labbook
            username: Active username
            owner: Intended owner of labbook

        Returns:
            LabBook
        """
        try:
            return self._put_labbook(path, username, owner)
        except Exception as e:
            logger.error(e)
            raise InventoryException(e)

    def load_labbook_from_directory(self, path: str, author: Optional[GitAuthor] = None) -> LabBook:
        """ Load and return a LabBook object from a given path on disk

        Warning - Deprecated !! Use load_labbook instead

        Args:
            path: Full path on disk to LabBook
            author: Labbook Author of commits

        Returns:
            LabBook object
        """
        try:
            lb = LabBook(config_file=self.config_file)
            lb._set_root_dir(path)
            lb._load_gigantum_data()
            lb._validate_gigantum_data()
            lb.author = author
            return lb
        except Exception as e:
            logger.error(e)
            raise InventoryException(e)

    def load_labbook(self, username: str, owner: str, labbook_name: str,
                     author: Optional[GitAuthor] = None) -> LabBook:
        try:
            lb = LabBook(self.config_file)
            lbroot = os.path.join(self.inventory_root, username,
                                  owner, 'labbooks', labbook_name)
            lb._set_root_dir(lbroot)
            lb._load_gigantum_data()
            lb._validate_gigantum_data()
            lb.author = author
            return lb
        except Exception as e:
            raise InventoryException(f"Cannot retrieve "
                                     f"({username}, {owner}, {labbook_name}): {e}")

    def list_repository_ids(self, username: str, repository_type: str) -> List[Tuple[str, str, str]]:
        """Return a list of (username, owner, labbook or dataset name) tuples corresponding
           to all repositories (labbook or datasets) whose existence is inferred. Since this method does not
           actually load the repositories, it returns quite fast.

           Warnings - there *may* exist corrupted repositories in the returned set -
            no validation is guaranteed.

        Args:
            username(str): Active username to crawl for
            repository_type(str): type of repository to list (labbook or dataset)

        Returns:
            List of 3-tuples containing (username, owner, labook-name)
        """
        if repository_type not in ["labbook", "dataset"]:
            raise ValueError(f"Unsupported repository type: {repository_type}")

        user_root = os.path.join(self.inventory_root, username)
        if not os.path.exists(user_root):
            return []

        owner_dirs = sorted([os.path.join(user_root, d)
                             for d in os.listdir(user_root)
                             if os.path.isdir(os.path.join(user_root, d))])
        repository_paths = []
        for owner_dir in owner_dirs:
            repository_dirs = sorted([os.path.join(owner_dir, f'{repository_type}s', l)
                                      for l in os.listdir(os.path.join(owner_dir, f'{repository_type}s'))
                                      if os.path.isdir(os.path.join(owner_dir, f'{repository_type}s', l))])
            for repository_dir in repository_dirs:
                repository_paths.append((username,
                                         os.path.basename(owner_dir),
                                         os.path.basename(repository_dir)))
        return repository_paths

    def list_labbooks(self, username: str, sort_mode: str = "name") -> List[LabBook]:
        """ Return list of all available labbooks for a given user

        Args:
            username: Active username
            sort_mode: One of "name", "modified_on" or "created_on"

        Returns:
            Sorted list of LabBook objects
        """
        local_labbooks = []
        for username, owner, lbname in self.list_repository_ids(username, 'labbook'):
            try:
                labbook = self.load_labbook(username, owner, lbname)
                local_labbooks.append(labbook)
            except Exception as e:
                logger.error(e)

        if sort_mode == "name":
            return natsorted(local_labbooks, key=lambda lb: lb.name)
        elif sort_mode == 'modified_on':
            return sorted(local_labbooks, key=lambda lb: lb.modified_on)
        elif sort_mode == 'created_on':
            return sorted(local_labbooks, key=lambda lb: lb.creation_date)
        else:
            raise InventoryException(f"Invalid sort mode {sort_mode}")

    def create_labbook_disabled_lfs(self, username: str, owner: str, labbook_name: str,
                                    description: Optional[str] = None,
                                    author: Optional[GitAuthor] = None) -> LabBook:
        path = self._new_labbook(username=username, owner={'username': owner},
                                 name=labbook_name, description=description,
                                 author=author, bypass_lfs=True)
        lb = self.load_labbook_from_directory(path, author=author)
        assert lb.active_branch == f'gm.workspace-{username}'
        return lb

    def create_labbook(self, username: str, owner: str, labbook_name: str,
                       description: Optional[str] = None, author: Optional[GitAuthor] = None) -> LabBook:
        """Create a new LabBook in this Gigantum working directory.

        Args:
            username: Active username
            owner: Namespace in which to place this LabBook
            labbook_name: Name of labbook
            description: Optional brief description of LabBook
            author: Optional Git Author

        Returns:
            Newly created LabBook instance

        """
        path = self._new_labbook(username=username, owner={'username': owner},
                                 name=labbook_name, description=description,
                                 author=author, bypass_lfs=False)
        return self.load_labbook_from_directory(path, author=author)

    def _new_labbook(self, owner: Dict[str, str], name: str,
                     username: str,
                     description: Optional[str] = None,
                     bypass_lfs: bool = False,
                     author: Optional[GitAuthor] = None) -> str:
        """Method to create a new minimal LabBook instance on disk

        NOTE: This is the exact same as the old LabBook.new() method.
        This method is deprecated and will be re-worked in the near future.

        Args:
            owner(dict): Owner information. Can be a user or a team/org.
            name(str): Name of the LabBook
            username(str): Username of the logged in user. Used to store the LabBook in the proper location. If omitted
                           the owner username is used
            description(str): A short description of the LabBook
            bypass_lfs: If True does not use LFS to track input and output dirs.
            author: Git author for commits

        Returns:
            str: Path to the LabBook contents
        """

        if not username:
            logger.warning("Using owner username `{}` when making new labbook".format(owner['username']))
            username = owner["username"]

        labbook = LabBook(config_file=self.config_file, author=author)

        # Build data file contents
        labbook._data = {
            "cuda_version": None,
            "labbook": {"id": uuid.uuid4().hex,
                        "name": name,
                        "description": description or ''},
            "owner": owner,
            "schema": LABBOOK_CURRENT_SCHEMA
        }

        # Validate data
        labbook._validate_gigantum_data()

        logger.info("Creating new labbook on disk for {}/{}/{} ...".format(username, owner, name))

        # lock while creating initial directory
        with labbook.lock(lock_key=f"new_labbook_lock|{username}|{owner['username']}|{name}"):
            # Verify or Create user subdirectory
            # Make sure you expand a user dir string
            starting_dir = os.path.expanduser(labbook.client_config.config["git"]["working_directory"])
            user_dir = os.path.join(starting_dir, username)
            if not os.path.isdir(user_dir):
                os.makedirs(user_dir)

            # Create owner dir - store LabBooks in working dir > logged in user > owner
            owner_dir = os.path.join(user_dir, owner["username"])
            if not os.path.isdir(owner_dir):
                os.makedirs(owner_dir)

                # Create `labbooks` subdir in the owner dir
                owner_dir = os.path.join(owner_dir, "labbooks")
            else:
                owner_dir = os.path.join(owner_dir, "labbooks")

            # Verify name not already in use
            if os.path.isdir(os.path.join(owner_dir, name)):
                raise ValueError(f"LabBook `{name}` already exists locally. Choose a new LabBook name")

            # Create LabBook subdirectory
            new_root_dir = os.path.join(owner_dir, name)
            os.makedirs(new_root_dir)
            labbook._set_root_dir(new_root_dir)

            # Init repository
            labbook.git.initialize()

            # Setup LFS
            if labbook.client_config.config["git"]["lfs_enabled"] and not bypass_lfs:
                # Make sure LFS install is setup and rack input and output directories
                call_subprocess(["git", "lfs", "install"], cwd=new_root_dir)
                call_subprocess(["git", "lfs", "track", "input/**"], cwd=new_root_dir)
                call_subprocess(["git", "lfs", "track", "output/**"], cwd=new_root_dir)

                # Commit .gitattributes file
                labbook.git.add(os.path.join(labbook.root_dir, ".gitattributes"))
                labbook.git.commit("Configuring LFS")

            # Create Directory Structure
            dirs = [
                'code', 'input', 'output', '.gigantum',
                os.path.join('.gigantum', 'env'),
                os.path.join('.gigantum', 'env', 'base'),
                os.path.join('.gigantum', 'env', 'custom'),
                os.path.join('.gigantum', 'env', 'package_manager'),
                os.path.join('.gigantum', 'activity'),
                os.path.join('.gigantum', 'activity', 'log'),
                os.path.join('.gigantum', 'activity', 'index'),
                os.path.join('.gigantum', 'activity', 'importance'),
            ]

            for d in dirs:
                p = os.path.join(labbook.root_dir, d, '.gitkeep')
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, 'w') as gk:
                    gk.write("This file is necessary to keep this directory tracked by Git"
                             " and archivable by compression tools. Do not delete or modify!")

            # Create labbook.yaml file
            labbook._save_gigantum_data()

            # Save build info
            try:
                buildinfo = Configuration(self.config_file).config['build_info']
            except KeyError:
                logger.warning("Could not obtain build_info from config")
                buildinfo = None
            buildinfo = {
                'creation_utc': datetime.datetime.utcnow().isoformat(),
                'build_info': buildinfo
            }

            buildinfo_path = os.path.join(labbook.root_dir, '.gigantum', 'buildinfo')
            with open(buildinfo_path, 'w') as f:
                json.dump(buildinfo, f)

            # Create .gitignore default file
            shutil.copyfile(os.path.join(resource_filename('gtmcore', 'labbook'), 'gitignore.default'),
                            os.path.join(labbook.root_dir, ".gitignore"))

            # Commit
            labbook.git.add_all()
            labbook.git.create_branch(name="gm.workspace")
            bm = BranchManager(labbook, username=username)
            # NOTE: this string is used to indicate there are no more activity records to get. Changing the string will
            # break activity paging.
            # TODO: Improve method for detecting the first activity record
            labbook.git.commit(f"Creating new empty LabBook: {name}")
            user_workspace_branch = f"gm.workspace-{username}"
            bm.create_branch(user_workspace_branch)

            if labbook.active_branch != user_workspace_branch:
                raise ValueError(f"active_branch should be '{user_workspace_branch}'")

            return labbook.root_dir

    def create_dataset(self, username: str, owner: str, dataset_name: str, storage_type: str,
                       description: Optional[str] = None, author: Optional[GitAuthor] = None) -> Dataset:
        """Create a new Dataset in this Gigantum working directory.

        Args:
            username: Active username
            owner: Namespace in which to place this Dataset
            dataset_name: Name of the Dataset
            storage_type: String identifying the type of Dataset to instantiate
            description: Optional brief description of Dataset
            author: Optional Git Author

        Returns:
            Newly created LabBook instance

        """
        dataset = Dataset(config_file=self.config_file, author=author)

        try:
            build_info = Configuration(self.config_file).config['build_info']
        except KeyError:
            logger.warning("Could not obtain build_info from config")
            build_info = None

        # Build data file contents
        dataset._data = {
            "schema": DATASET_CURRENT_SCHEMA,
            "id": uuid.uuid4().hex,
            "name": dataset_name,
            "storage_type": storage_type,
            "description": description or '',
            "created_on": datetime.datetime.utcnow().isoformat(),
            "build_info": build_info
        }
        dataset._validate_gigantum_data()

        logger.info("Creating new Dataset on disk for {}/{}/{}".format(username, owner, dataset_name))
        # lock while creating initial directory
        with dataset.lock(lock_key=f"new_dataset_lock|{username}|{owner}|{dataset_name}"):
            # Verify or Create user subdirectory
            # Make sure you expand a user dir string
            starting_dir = os.path.expanduser(dataset.client_config.config["git"]["working_directory"])
            user_dir = os.path.join(starting_dir, username)
            if not os.path.isdir(user_dir):
                os.makedirs(user_dir)

            # Create owner dir - store LabBooks in working dir > logged in user > owner
            owner_dir = os.path.join(user_dir, owner)
            if not os.path.isdir(owner_dir):
                os.makedirs(owner_dir)

                # Create `datasets` subdir in the owner dir
                owner_dir = os.path.join(owner_dir, "datasets")
            else:
                owner_dir = os.path.join(owner_dir, "datasets")

            # Verify name not already in use
            if os.path.isdir(os.path.join(owner_dir, dataset_name)):
                raise ValueError(f"Dataset `{dataset_name}` already exists locally. Choose a new Dataset name")

            # Create Dataset subdirectory
            new_root_dir = os.path.join(owner_dir, dataset_name)
            os.makedirs(new_root_dir)
            dataset._set_root_dir(new_root_dir)

            # Init repository
            dataset.git.initialize()

            # Create Directory Structure
            dirs = [
                'manifest', 'metadata', '.gigantum',
                os.path.join('.gigantum', 'favorites'),
                os.path.join('.gigantum', 'activity'),
                os.path.join('.gigantum', 'activity', 'log')
            ]

            for d in dirs:
                p = os.path.join(dataset.root_dir, d, '.gitkeep')
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, 'w') as gk:
                    gk.write("This file is necessary to keep this directory tracked by Git"
                             " and archivable by compression tools. Do not delete or modify!")

            # Create labbook.yaml file
            dataset._save_gigantum_data()

            # Create an empty storage.json file
            dataset.storage_config = {}

            # Create .gitignore default file
            shutil.copyfile(os.path.join(resource_filename('gtmcore', 'dataset'), 'gitignore.default'),
                            os.path.join(dataset.root_dir, ".gitignore"))

            # Commit
            dataset.git.add_all()

            # NOTE: this string is used to indicate there are no more activity records to get. Changing the string will
            # break activity paging.
            # TODO: Improve method for detecting the first activity record
            dataset.git.commit(f"Creating new empty Dataset: {dataset_name}")

            # TODO: Move to branch manager class
            dataset.git.create_branch(name="workspace")

            return dataset

    def delete_dataset(self, username: str, owner: str, dataset_name: str) -> None:
        """Delete a Dataset from this Gigantum working directory.

        Args:
            username: Active username
            owner: Namespace in which to place this Dataset
            dataset_name: Name of the Datasets

        Returns:
            None

        """
        ds = self.load_dataset(username, owner, dataset_name)
        shutil.rmtree(ds.root_dir, ignore_errors=True)

    def load_dataset(self, username: str, owner: str, dataset_name: str,
                     author: Optional[GitAuthor] = None) -> Dataset:
        """Method to load a dataset from disk

        Args:
            username(str): Username of user logged in
            owner(str): Username of the owner (namespace) of the Dataset
            dataset_name(str): Name of the dataset
            author(GitAuthor): GitAuthor object

        Returns:
            Dataset
        """
        try:
            ds = Dataset(self.config_file, author=author)

            ds_root = os.path.join(self.inventory_root, username,
                                   owner, 'datasets', dataset_name)
            ds._set_root_dir(ds_root)
            ds._load_gigantum_data()
            ds._validate_gigantum_data()
            return ds
        except Exception as e:
            raise InventoryException(f"Cannot retrieve ({username}, {owner}, {dataset_name}): {e}")

    def list_datasets(self, username: str, sort_mode: str = "name") -> List[Dataset]:
        """ Return list of all available datasets for a given user

        This will result in sorting a-z and with the oldest to newest.

        Args:
            username: Active username
            sort_mode: One of "name", "modified_on" or "created_on"

        Returns:
            Sorted list of Dataset objects
        """
        local_datasets = []
        for username, owner, dsname in self.list_repository_ids(username, 'dataset'):
            try:
                dataset = self.load_dataset(username, owner, dsname)
                local_datasets.append(dataset)
            except Exception as e:
                logger.error(e)

        if sort_mode == "name":
            return natsorted(local_datasets, key=lambda ds: ds.name)
        elif sort_mode == 'modified_on':
            return sorted(local_datasets, key=lambda ds: ds.modified_on)
        elif sort_mode == 'created_on':
            return sorted(local_datasets, key=lambda ds: ds.creation_date)
        else:
            raise InventoryException(f"Invalid sort mode {sort_mode}")
