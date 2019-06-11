# Copyright (c) 2018 FlashX, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Callable, cast

from gtmcore.configuration.utils import call_subprocess
from gtmcore.logging import LMLogger
from gtmcore.labbook import LabBook
from gtmcore.labbook.schemas import CURRENT_SCHEMA as CURRENT_LABBOOK_SCHEMA
from gtmcore.workflows import gitworkflows_utils
from gtmcore.exceptions import GigantumException
from gtmcore.inventory import Repository
from gtmcore.inventory.inventory import InventoryManager
from gtmcore.dataset import Dataset
from gtmcore.inventory.branching import BranchManager
from gtmcore.dataset.manifest import Manifest
from gtmcore.dataset.io.manager import IOManager

logger = LMLogger.get_logger()


class GitWorkflowException(GigantumException):
    pass


class MergeOverride(Enum):
    OURS = 'ours'
    THEIRS = 'theirs'
    ABORT = 'abort'


class GitWorkflow(ABC):
    """Manages all aspects of interaction with Git remote server
    """

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    @property
    def remote(self) -> Optional[str]:
        return self.repository.remote

    @classmethod
    @abstractmethod
    def import_from_remote(cls, remote_url: str, username: str) -> 'GitWorkflow':
        pass

    def garbagecollect(self):
        """ Run a `git gc` on the repository. """
        gitworkflows_utils.git_garbage_collect(self.repository)

    def publish(self, username: str, access_token: Optional[str] = None, remote: str = "origin",
                public: bool = False, feedback_callback: Callable = lambda _ : None,
                id_token: Optional[str] = None) -> None:
        """ Publish this repository to the remote GitLab instance.

        Args:
            username: Subject username
            access_token: Temp token/password to gain permissions on GitLab instance
            remote: Name of Git remote (always "origin" for now).
            public: Allow public read access
            feedback_callback: Callback to give user-facing realtime feedback
            id_token: Dataset credentials
        Returns:
            None
        """

        logger.info(f"Publishing {str(self.repository)} for user {username} to remote {remote}")
        if self.remote:
            raise GitWorkflowException("Cannot publish Labbook when remote already set.")

        branch_mgr = BranchManager(self.repository, username=username)
        if branch_mgr.active_branch != branch_mgr.workspace_branch:
            raise GitWorkflowException(f"Must be on branch {branch_mgr.workspace_branch} to publish")

        try:
            self.repository.sweep_uncommitted_changes()
            vis = "public" if public is True else "private"
            gitworkflows_utils.create_remote_gitlab_repo(repository=self.repository, username=username,
                                                         access_token=access_token, visibility=vis)
            gitworkflows_utils.publish_to_remote(repository=self.repository, username=username,
                                                 remote=remote, feedback_callback=feedback_callback)
        except Exception as e:
            # Unsure what specific exception add_remote creates, so make a catchall.
            logger.error(f"Publish failed {e}: {str(self.repository)} may be in corrupted Git state!")
            call_subprocess(['git', 'reset', '--hard'], cwd=self.repository.root_dir)
            raise e

    def sync(self, username: str, remote: str = "origin", override: MergeOverride = MergeOverride.ABORT,
             feedback_callback: Callable = lambda _: None, pull_only: bool = False,
             access_token: Optional[str] = None, id_token: Optional[str] = None) -> int:
        """ Sync with remote GitLab repo (i.e., pull any upstream changes and push any new changes). Following
        a sync operation both the local repo and remote should be at the same revision.

        Args:
            username: Subject user
            remote: Name of remote (usually only origin for now)
            override: In the event of conflict, select merge method (mine/theirs/abort)
            pull_only: If true, do not push back after doing a pull.
            feedback_callback: Used to give periodic feedback

        Returns:
            Integer number of commits pulled down from remote.
        """
        updates_cnt = gitworkflows_utils.sync_branch(self.repository, username=username,
                                                     override=override.value, pull_only=pull_only,
                                                     feedback_callback=feedback_callback)
        return updates_cnt

    def reset(self, username: str):
        """ Perform a Git reset to undo all local changes"""
        bm = BranchManager(self.repository, username)
        if self.remote and bm.active_branch in bm.branches_remote:
            self.repository.git.fetch()
            self.repository.sweep_uncommitted_changes()
            call_subprocess(['git', 'reset', '--hard', f'origin/{bm.active_branch}'],
                            cwd=self.repository.root_dir)
            call_subprocess(['git', 'clean', '-fd'], cwd=self.repository.root_dir)
            self.repository.git.clear_checkout_context()

            # update dataset references on reset
            if isinstance(self.repository, LabBook):
                InventoryManager().update_linked_dataset(self.repository, username, init=True)


class LabbookWorkflow(GitWorkflow):
    @property
    def labbook(self):
        return cast(LabBook, self.repository)

    @classmethod
    def import_from_remote(cls, remote_url: str, username: str,
                           config_file: str = None) -> 'LabbookWorkflow':
        """Take a URL of a remote Labbook and manifest it locally on this system. """

        try:
            inv_manager = InventoryManager(config_file=config_file)
            _, namespace, repo_name = remote_url.rsplit('/', 2)
            repo = gitworkflows_utils.clone_repo(remote_url=remote_url, username=username, owner=namespace,
                                      load_repository=inv_manager.load_labbook_from_directory,
                                      put_repository=inv_manager.put_labbook)
            logger.info(f"Imported remote Project {str(repo)} on branch {repo.active_branch}")
            return cls(repo)
        except Exception as e:
            logger.error(e)
            raise

    def should_migrate(self) -> bool:
        """
        Indicate whether a migration should be performed

        Only looks at LOCAL details.
        """
        bm = BranchManager(self.labbook)
        if 'gm.workspace' not in bm.active_branch:
            return False

        if 'master' not in bm.branches_local:
            return True

        logmsgs = call_subprocess('git log master --oneline --pretty=format:"%s"'.split(),
                                  cwd=self.labbook.root_dir).split('\n')
        if '"Migrate schema to 2"' in logmsgs:
            return False

        return True

    def migrate(self) -> bool:
        """ Migrate the given LabBook to the most recent schema AND branch version.

        Returns:
            Boolean indicating whether a migration was performed (False if already up-to-date)
        """

        if self.repository.schema == CURRENT_LABBOOK_SCHEMA:
            logger.info(f"{str(self.labbook)} already migrated.")
            return False

        if 'gm.workspace' not in BranchManager(self.labbook).active_branch:
            raise GitWorkflowException('Must be on a gm.workspace branch to migrate')

        im = InventoryManager(self.labbook.client_config.config_file)
        gitworkflows_utils.migrate_labbook_branches(self.labbook)
        self.repository = im.load_labbook_from_directory(self.labbook.root_dir)

        gitworkflows_utils.migrate_labbook_schema(self.labbook)
        self.repository = im.load_labbook_from_directory(self.labbook.root_dir)

        gitworkflows_utils.migrate_labbook_untracked_space(self.labbook)
        self.repository = im.load_labbook_from_directory(self.labbook.root_dir)

        # Pushes up the new master branch
        if self.repository.has_remote:
            self.sync(username='')

        return True


class DatasetWorkflow(GitWorkflow):
    @property
    def dataset(self):
        return cast(Dataset, self.repository)

    @classmethod
    def import_from_remote(cls, remote_url: str, username: str,
                           config_file: str = None) -> 'DatasetWorkflow':
        """Take a URL of a remote Dataset and manifest it locally on this system. """
        inv_manager = InventoryManager(config_file=config_file)
        _, namespace, repo_name = remote_url.rsplit('/', 2)
        repo = gitworkflows_utils.clone_repo(remote_url=remote_url, username=username, owner=namespace,
                                  load_repository=inv_manager.load_dataset_from_directory,
                                  put_repository=inv_manager.put_dataset)
        return cls(repo)

    def _push_dataset_objects(self, dataset: Dataset, logged_in_username: str,
                              feedback_callback: Callable, access_token, id_token) -> None:
        dataset.backend.set_default_configuration(logged_in_username, access_token, id_token)
        m = Manifest(dataset, logged_in_username)
        iom = IOManager(dataset, m)
        iom.push_objects(status_update_fn=feedback_callback)
        iom.manifest.link_revision()

    def publish(self, username: str, access_token: Optional[str] = None, remote: str = "origin",
                public: bool = False, feedback_callback: Callable = lambda _ : None,
                id_token: Optional[str] = None):
        super().publish(username, access_token, remote, public, feedback_callback, id_token)
        self._push_dataset_objects(self.dataset, username, feedback_callback,
                                   access_token, id_token)

    def sync(self, username: str, remote: str = "origin", override: MergeOverride = MergeOverride.ABORT,
             feedback_callback: Callable = lambda _ : None, pull_only: bool = False,
             access_token: Optional[str] = None, id_token: Optional[str] = None):
        v = super().sync(username, remote, override, feedback_callback, pull_only,
                         access_token, id_token)
        self._push_dataset_objects(self.dataset, username, feedback_callback,
                                   access_token, id_token)
        return v
