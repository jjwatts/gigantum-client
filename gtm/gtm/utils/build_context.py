"""A collection of functions to help describe build contexts (e.g., git hash)"""

from git import Repo

# Need submodule precision to avoid circular import
from gtm import common


def get_current_commit_hash(length=None) -> str:
    """Method to get the current commit hash of the gtm repository

    Returns:
        str
    """
    # Get the path of the root directory
    repo = Repo(common.config.get_client_root())
    if length is None:
        return repo.head.commit.hexsha
    else:
        return repo.head.commit.hexsha[:length]

