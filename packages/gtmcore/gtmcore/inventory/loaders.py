from typing import Optional, Callable, Any, cast
import subprocess
import shutil
import tempfile
import time
import os

from gtmcore.configuration.utils import call_subprocess
from gtmcore.labbook.labbook import LabBook
from gtmcore.dataset.dataset import Dataset
from gtmcore.inventory import Repository
from gtmcore.inventory.branching import BranchManager
from gtmcore.inventory.inventory import InventoryManager
from gtmcore.exceptions import GigantumException
from gtmcore.logging import LMLogger

logger = LMLogger.get_logger()


def _clone(repo: Repository, remote_url: str, working_dir: str) -> str:
    if repo.client_config.config["git"]["lfs_enabled"]:
        clone_tokens = f"git lfs clone {remote_url} --branch gm.workspace".split()
    else:
        clone_tokens = f"git clone {remote_url} --branch gm.workspace".split()
    print('INSIDE _clone')
    print(clone_tokens)

    # Perform a Git clone
    call_subprocess(clone_tokens, cwd=working_dir)

    # Affirm there is only one directory created
    dirs = os.listdir(working_dir)
    if len(dirs) != 1:
        assert False
    p = os.path.join(working_dir, dirs[0])
    assert os.path.exists(p)
    return p


def _switch_owner(repository: Repository, username: str) -> Repository:
    #TODO: owner is no longer used and this function should be removed
    logger.info(f"Cloning public repo; changing owner to {username}")
    repository._load_gigantum_data()
    if repository._data:
        if 'owner' in repository._data.keys():
            repository._data['owner']['username'] = username
    else:
        raise GigantumException("LabBook _data not defined")
    repository._save_gigantum_data()
    repository.remove_remote('origin')
    msg = f"Imported and changed owner to {username}"
    repository.sweep_uncommitted_changes(extra_msg=msg)
    return repository


def _from_remote(remote_url: str, username: str, owner: str,
                 repository: Repository, load_repository: Callable[[str], Any],
                 put_repository: Callable[[str, str, str], Any],
                 make_owner: bool = False) -> Repository:

    with tempfile.TemporaryDirectory() as tempdir:
        # Clone into a temporary directory, such that if anything
        # gets messed up, then this directory will be cleaned up.
        path = _clone(repository, remote_url=remote_url, working_dir=tempdir)
        candidate_repo = load_repository(path)

        if os.environ.get('WINDOWS_HOST'):
            logger.warning("Imported on Windows host - set fileMode to false")
            call_subprocess("git config core.fileMode false".split(),
                            cwd=candidate_repo.root_dir)

        bm = BranchManager(candidate_repo, username=username)
        bm.workon_branch("gm.workspace")
        user_workspace = f'gm.workspace-{username}'
        if user_workspace in bm.branches:
            bm.workon_branch(user_workspace)
        else:
            bm.create_branch(user_workspace)

        if make_owner:
            # Make the owner of the imported labbook the username
            candidate_repo = _switch_owner(candidate_repo, username)
            new_owner = username
        else:
            new_owner = owner

        repository = put_repository(candidate_repo.root_dir, username, new_owner)

    return repository


def labbook_from_remote(remote_url: str, username: str, owner: str,
                        labbook: Optional[LabBook] = None,
                        make_owner: bool = False) -> LabBook:
    """Clone a labbook from a remote Git repository.

    Args:
        remote_url: URL or path of remote repo
        username: Username of logged in user
        owner: Owner/namespace of labbook
        labbook: Optional LabBook instance with config
        make_owner: After cloning, make the owner the "username"

    Returns:
        LabBook
    """
    if labbook is None:
        s_labbook = LabBook()
    else:
        s_labbook = labbook  # type: ignore
    inv_manager = InventoryManager(s_labbook.client_config.config_file)
    return cast(LabBook, _from_remote(remote_url, username, owner, s_labbook,
                                      inv_manager.load_labbook_from_directory,
                                      inv_manager.put_labbook, make_owner))


def dataset_from_remote(remote_url: str, username: str, owner: str,
                        dataset: Optional[Dataset] = None,
                        make_owner: bool = False) -> Dataset:
    """Clone a dataset from a remote Git repository.

    Args:
        remote_url: URL or path of remote repo
        username: Username of logged in user
        owner: Owner/namespace of labbook
        dataset: Optional Dataset instance with config
        make_owner: After cloning, make the owner the "username"

    Returns:
        Dataset
    """
    if dataset is None:
        s_dataset = Dataset()
    else:
        s_dataset = dataset  # type: ignore
    inv_manager = InventoryManager(s_dataset.client_config.config_file)
    return cast(Dataset, _from_remote(remote_url, username, owner, s_dataset,
                                      inv_manager.load_dataset_from_directory,
                                      inv_manager.put_dataset, make_owner))
