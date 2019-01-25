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
import re
import subprocess

import git
from typing import Optional, List, Tuple

from gtmcore.exceptions import GigantumException
from gtmcore.logging import LMLogger
# from gtmcore.repository import LabBook
from gtmcore.inventory import Repository
from gtmcore.configuration.utils import call_subprocess

logger = LMLogger.get_logger()


class BranchException(GigantumException):
    pass


class BranchWorkflowViolation(BranchException):
    pass


class InvalidBranchName(BranchException):
    pass


class BranchManager(object):
    """Responsible for all Git branch and merge operations.

    Intended to be the sole entrypoint for operations to query for
    and perform basic Git branching operations. The Workflows package
    in particular is intended to be the main user of this class, which
    will use the methods provided here to support conflict-free distributed
    workflow among users.

    TODO(billvb): Finish removing all workflow-specific fields
    """

    def __init__(self, repository: Repository, username: str) -> None:
        self.repository = repository
        self.username = username

    @classmethod
    def is_branch_name_valid(cls, new_branch_name: str) -> bool:
        """Query if the given branch name is can be the name of a new branch"""
        if len(new_branch_name) > 80:
            return False
        return all([(e.replace('.', '').isalnum() and e == e.lower()) for e in new_branch_name.split('-')])

    @property
    def active_branch(self) -> str:
        """Return the name of the current branch."""
        return self.repository.active_branch

    @property
    def workspace_branch(self) -> str:
        """Return the user's primary branch name

        TODO(billvb): Migrate to Workflows (does not belong here).
        """
        b = f'gm.workspace-{self.username}'
        if b not in self.branches:
            raise BranchException(f'Cannot find user workspace branch {b}')
        return b

    @property
    def available_branches(self) -> List[str]:
        # TODO(billvb): Migrate to Workflows
        return [b for b in self.branches if f'gm.workspace-{self.username}' in b]

    @property
    def branches(self) -> List[str]:
        """List all branches (local AND remote) available for checkout"""
        return sorted(list(set(self.repository.get_branches()['local']
                               + self.repository.get_branches()['remote'])))

    def create_branch(self, title: str, revision: Optional[str] = None) -> str:
        """Create and checkout (work on) a new managed branch."""
        if not self.is_branch_name_valid(title):
            raise InvalidBranchName(f'Branch name `{title}` invalid pattern')

        if title in self.branches:
            raise InvalidBranchName(f'Branch name `{title}` already exists')

        self.repository.sweep_uncommitted_changes()
        if revision:
            # The following call prints "commit" if {revision} exists in git history.
            result = subprocess.check_output(f'git cat-file -t {revision} || echo "invalid"',
                                             cwd=self.repository.root_dir, shell=True)
            if result.decode().strip() != 'commit':
                logger.error(result.decode().strip())
                raise InvalidBranchName(f'Revision {revision} does not exist in {str(self.repository)};'
                                        f'cannot create branch {title}')
            # Should be in a detached-head, and then make branch from there.
            logger.info(f"Creating rollback branch from revision {revision} in {str(self.repository)}")
            r = subprocess.check_output(f'git checkout {revision}', cwd=self.repository.root_dir, shell=True)
            logger.info(r)
        self.repository.checkout_branch(branch_name=title, new=True)
        logger.info(f'Activated new branch {self.active_branch} in {str(self.repository)}')

        return title

    def remove_branch(self, target_branch: str) -> None:
        """Delete a local feature branch that is NOT the active branch.

        Args:
            target_branch: Full name of feature branch to delete

        Returns:
            None
        """
        if target_branch not in self.branches:
            raise InvalidBranchName(f'Cannot delete `{target_branch}`; does not exist')

        if target_branch == self.workspace_branch:
            raise BranchWorkflowViolation(f'Cannot delete workspace branch `{target_branch}` in {str(self.repository)}')

        if target_branch == self.active_branch:
            raise BranchWorkflowViolation(f'Cannot delete current active branch `{target_branch}`')

        logger.info(f'Removing from {str(self.repository)} feature branch `{target_branch}`')
        # Note use "force=True" to prevent warning on merge.
        self.repository.git.delete_branch(target_branch, force=True)

        if target_branch in self.branches:
            raise BranchWorkflowViolation(f'Removal of branch `{target_branch}` in {str(self.repository)} failed.')

    def _workon_branch(self, branch_name: str) -> None:
        """Checkouts a branch as the working revision. """

        #if branch_name not in self.branches:
        #    raise InvalidBranchName(f'Target branch `{branch_name}` does not exist')

        self.repository.sweep_uncommitted_changes(extra_msg="Save state on branch change")
        self.repository.checkout_branch(branch_name=branch_name)
        logger.info(f'Checked out branch {self.active_branch} in {str(self.repository)}')

    def workon_branch(self, branch_name: str) -> None:
        """Performs a Git checkout on the given branch_name"""
        try:
            self._workon_branch(branch_name)
        except Exception as e:
            logger.error(e)
            raise BranchException(e)

    def merge_from(self, other_branch: str, force: bool = False) -> None:
        """Pulls/merges `other_branch` into current branch.

        Args:
            other_branch: Name of other branch to merge from
            force: Force overwrite if conflicts occur
        """

        if other_branch not in self.branches:
            raise InvalidBranchName(f'Other branch {other_branch} not found')

        logger.info(f"In {str(self.repository)} merging branch `{other_branch}` into `{self.active_branch}`...")
        try:
            self.repository.sweep_uncommitted_changes()
            if force:
                logger.warning("Using force to overwrite local changes")
                call_subprocess(['git', 'merge', '-s', 'recursive', '-X', 'theirs', other_branch],
                                cwd=self.repository.root_dir)
            else:
                try:
                    call_subprocess(['git', 'merge', other_branch], cwd=self.repository.root_dir)
                except (git.exc.GitCommandError, subprocess.CalledProcessError) as merge_error:
                    logger.error(f"Merge conflict syncing {str(self.repository)} - Use `force` to overwrite.")
                    # TODO - This should be cleaned up (The UI attempts to match on the token "Cannot merge")
                    raise BranchException(f"Cannot merge - {merge_error}")
            self.repository.git.commit(f'Merged from branch `{other_branch}`')
            logger.info(f"{str(self.repository)} finished merge")
        except Exception as e:
            call_subprocess(['git', 'reset', '--hard'], cwd=self.repository.root_dir)
            raise e

    def get_commits_behind_remote(self, remote_name: str = "origin") -> Tuple[str, int]:
        """Return the number of commits local branch is behind remote. Note, only works with
        currently checked-out branch. If the local branch is AHEAD of the remote, returns a negative
        value.

        Args:
            remote_name: Name of remote, e.g., "origin"

        Returns:
            tuple containing branch name, and number of commits behind (zero implies up-to-date,
                negative implies local branch is ahead.)
        """
        # TODO(billvb/dmk/?) - This can be one-lined using some versions of GitPython
        # https://stackoverflow.com/questions/17224134/check-status-of-local-python-relative-to-remote-with-gitpython/21431791
        # However, it's not clear we will continue to use GitPython going forward or that this implementation
        # needs to change right now.
        try:
            if self.repository.has_remote:
                self.repository.git.fetch(remote=remote_name)
            result_str = self.repository.git.repo.git.status().replace('\n', ' ')
        except Exception as e:
            logger.exception(e)
            raise GigantumException(e)

        if 'branch is up-to-date' in result_str:
            return self.active_branch, 0
        elif 'branch is behind' in result_str:
            m = re.search(' by ([\d]+) commit', result_str)
            if m:
                assert int(m.groups()[0]) > 0
                return self.active_branch, int(m.groups()[0])
            else:
                logger.error(f"Could not find count in: {result_str}")
                raise GigantumException("Unable to determine commit behind-count")
        elif 'branch is ahead of' in result_str:
            # Return NEGATIVE if your branch is ahead of remote
            m = re.search(' by ([\d]+) commit', result_str)
            if m:
                assert int(m.groups()[0]) > 0
                return self.active_branch, -1 * int(m.groups()[0])
            else:
                logger.error(f"Could not find count in: {result_str}")
                raise GigantumException("Unable to determine commit behind-count")
        else:
            # This branch is local-only
            return self.active_branch, 0
