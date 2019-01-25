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
import time

from typing import Optional, Callable

from gtmcore.configuration.utils import call_subprocess
from gtmcore.logging import LMLogger
from gtmcore.workflows import core
from gtmcore.inventory import Repository
from gtmcore.dataset import Dataset
from gtmcore.inventory.branching import BranchManager
from gtmcore.dataset.manifest import Manifest
from gtmcore.dataset.io.manager import IOManager

logger = LMLogger.get_logger()


def helper_push_objects(dataset, logged_in_username, feedback_callback, access_token, id_token):
    dataset.backend.set_default_configuration(logged_in_username, access_token, id_token)
    m = Manifest(dataset, logged_in_username)
    iom = IOManager(dataset, m)

    iom.push_objects(status_update_fn=feedback_callback)

    # Relink all files
    iom.manifest.link_revision()


class GitWorkflow(object):
    """Manages all aspects of interaction with Git remote server

    """

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def garbagecollect(self):
        """ Run a `git gc` on the repository. """
        core.git_garbage_collect(self.repository)

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

        Returns:
            None
        """

        logger.info(f"Publishing {str(self.repository)} for user {username} to remote {remote}")
        if self.repository.has_remote:
            raise ValueError("Cannot publish Labbook when remote already set.")

        branch_mgr = BranchManager(self.repository, username=username)
        if branch_mgr.active_branch != f'gm.workspace-{username}':
            raise ValueError(f"Must be on user workspace (gm.workspace-{username}) to sync")

        try:
            self.repository.sweep_uncommitted_changes()
            vis = "public" if public is True else "private"
            t0 = time.time()
            core.create_remote_gitlab_repo(repository=self.repository, username=username,
                                           access_token=access_token, visibility=vis)
            logger.info(f"Created remote repo for {str(self.repository)} in {time.time()-t0:.1f}sec")
            t0 = time.time()
            core.publish_to_remote(repository=self.repository, username=username,
                                   remote=remote, feedback_callback=feedback_callback)
            logger.info(f"Published {str(self.repository)} in {time.time()-t0:.1f}sec")

            if isinstance(self.repository, Dataset):
                helper_push_objects(self.repository, username, feedback_callback, access_token, id_token)
        except Exception as e:
            # Unsure what specific exception add_remote creates, so make a catchall.
            logger.error(f"Publish failed {e}: {str(self.repository)} may be in corrupted Git state!")
            call_subprocess(['git', 'reset', '--hard'], cwd=self.repository.root_dir)

            branch_mgr.workon_branch(f"gm.workspace-{username}")
            raise e

    def sync(self, username: str, remote: str = "origin", force: bool = False,
             feedback_callback: Callable = lambda _ : None,
             access_token: Optional[str] = None, id_token: Optional[str] = None) -> int:
        """ Sync with remote GitLab repo (i.e., pull any upstream changes and push any new changes). Following
        a sync operation both the local repo and remote should be at the same revision.

        Args:
            username: Subject user
            remote: Name of remote (usually only origin for now)
            force: In the event of conflict, force overwrite local changes
            feedback_callback: Used to give periodic feedback

        Returns:
            Integer number of commits pulled down from remote.
        """
        result = core.sync_with_remote(repository=self.repository, username=username, remote=remote,
                                       force=force, feedback_callback=feedback_callback)

        if isinstance(self.repository, Dataset):
            helper_push_objects(self.repository, username, feedback_callback, access_token, id_token)

        return result

    def _add_remote(self, remote_name: str, url: str):
        self.repository.add_remote(remote_name=remote_name, url=url)
