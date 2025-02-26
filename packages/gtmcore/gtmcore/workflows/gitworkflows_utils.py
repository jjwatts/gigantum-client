# Copyright (c) 2017 FlashX, LLC
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
import subprocess
import time
import os
from typing import Optional, Callable

from gtmcore.workflows.gitlab import GitLabManager
from gtmcore.activity import ActivityStore, ActivityType, ActivityRecord, \
                             ActivityDetailType, ActivityDetailRecord, \
                             ActivityAction
from gtmcore.exceptions import GigantumException
from gtmcore.labbook import LabBook
from gtmcore.labbook.schemas import migrate_schema_to_current, \
                                    CURRENT_SCHEMA as CURRENT_LABBOOK_SCHEMA
from gtmcore.inventory import Repository
from gtmcore.inventory.inventory import InventoryManager
from gtmcore.logging import LMLogger
from gtmcore.configuration.utils import call_subprocess
from gtmcore.inventory.branching import BranchManager, MergeConflict


logger = LMLogger.get_logger()


class WorkflowsException(Exception):
    pass


class MergeError(WorkflowsException):
    pass


class GitLabRemoteError(WorkflowsException):
    pass


def git_garbage_collect(repository: Repository) -> None:
    """Run "git gc" (garbage collect) over the repo. If run frequently enough, this only takes a short time
    even on large repos.

    Note!! This method assumes the subject repository has already been locked!

    TODO(billvb): Refactor into BranchManager

    Args:
        repository: Subject Repository

    Returns:
        None

    Raises:
        subprocess.CalledProcessError when git gc fails.
        """
    logger.info(f"Running git gc (Garbage Collect) in {str(repository)}...")
    if os.environ.get('WINDOWS_HOST'):
        logger.warning(f"Avoiding `git gc` in {str(repository)} on Windows host fs")
        return

    try:
        call_subprocess(['git', 'gc'], cwd=repository.root_dir)
    except subprocess.CalledProcessError:
        logger.warning(f"Ignore `git gc` error - {str(repository)} repo remains unpruned")


def create_remote_gitlab_repo(repository: Repository, username: str, visibility: str,
                              access_token: Optional[str] = None) -> None:
    """Create a new repository in GitLab,

    Note: It may make more sense to factor this out later on. """

    default_remote = repository.client_config.config['git']['default_remote']
    admin_service = None
    for remote in repository.client_config.config['git']['remotes']:
        if default_remote == remote:
            admin_service = repository.client_config.config['git']['remotes'][remote]['admin_service']
            break

    if not admin_service:
        raise ValueError('admin_service could not be found')

    try:
        # Add collaborator to remote service
        mgr = GitLabManager(default_remote, admin_service,
                            access_token=access_token or 'invalid')
        mgr.configure_git_credentials(default_remote, username)
        mgr.create_labbook(namespace=InventoryManager().query_owner(repository),
                           labbook_name=repository.name,
                           visibility=visibility)
        repository.add_remote("origin", f"https://{default_remote}/{username}/{repository.name}.git")
    except Exception as e:
        raise GitLabRemoteError(e)


def publish_to_remote(repository: Repository, username: str, remote: str,
                      feedback_callback: Callable) -> None:
    # TODO(billvb) - Refactor all (or part) to BranchManager
    bm = BranchManager(repository, username=username)
    if bm.workspace_branch != bm.active_branch:
        raise ValueError(f'Must be on branch {bm.workspace_branch} to publish')

    feedback_callback(f"Preparing to publish {repository.name}")
    git_garbage_collect(repository)

    # Try five attempts to fetch - the remote repo could have been created just milliseconds
    # ago, so may need a few moments to settle before it supports all the git operations.
    for tr in range(5):
        try:
            repository.git.fetch(remote=remote)
            break
        except Exception as e:
            logger.warning(f"Fetch attempt {tr+1}/5 failed for {str(repository)}: {e}")
            time.sleep(1)
    else:
        raise ValueError(f"Timed out trying to fetch repo for {str(repository)}")

    feedback_callback("Pushing up regular objects...")
    call_subprocess(['git', 'push', '--set-upstream', 'origin', bm.workspace_branch],
                    cwd=repository.root_dir)
    feedback_callback(f"Publish complete.")
    repository.git.clear_checkout_context()


def _set_upstream_branch(repository: Repository, branch_name: str, feedback_cb: Callable):
    # TODO(billvb) - Refactor to BranchManager
    set_upstream_tokens = ['git', 'push', '--set-upstream', 'origin', branch_name]
    call_subprocess(set_upstream_tokens, cwd=repository.root_dir)


def _pull(repository: Repository, branch_name: str, override: str, feedback_cb: Callable,
          username: Optional[str] = None) -> None:
    # TODO(billvb) Refactor to BranchManager
    feedback_cb(f"Pulling from remote branch \"{branch_name}\"...")
    cp = repository.git.commit_hash
    try:
        call_subprocess(f'git pull'.split(), cwd=repository.root_dir)
        if isinstance(repository, LabBook):
            if not username:
                raise ValueError("Current logged in username required to checkout a Project with a linked dataset")
            InventoryManager().update_linked_dataset(repository, username, init=True)

    except subprocess.CalledProcessError as cp_error:
        if 'Automatic merge failed' in cp_error.stdout.decode():
            feedback_cb(f"Detected merge conflict, resolution method = {override}")
            bm = BranchManager(repository, username='')
            conflicted_files = bm._infer_conflicted_files(cp_error.stdout.decode())
            if 'abort' == override:
                call_subprocess(f'git reset --hard {cp}'.split(), cwd=repository.root_dir)
                raise MergeConflict('Merge conflict pulling upstream', conflicted_files)
            call_subprocess(f'git checkout --{override} {" ".join(conflicted_files)}'.split(),
                            cwd=repository.root_dir)
            call_subprocess('git add .'.split(), cwd=repository.root_dir)
            call_subprocess('git commit -m "Merge"'.split(), cwd=repository.root_dir)
            feedback_cb("Resolved merge conflict")
        else:
            raise


def sync_branch(repository: Repository, username: Optional[str], override: str,
                pull_only: bool, feedback_callback: Callable) -> int:
    """"""
    if not repository.has_remote:
        return 0

    repository.sweep_uncommitted_changes()
    repository.git.fetch()

    bm = BranchManager(repository)
    branch_name = bm.active_branch

    if pull_only and branch_name not in bm.branches_remote:
        # Cannot pull when remote branch doesn't exist.
        feedback_callback("Pull complete - nothing to pull")
        repository.git.clear_checkout_context()
        return 0

    if branch_name not in bm.branches_remote:
        # Branch does not exist, so push it to remote.
        _set_upstream_branch(repository, bm.active_branch, feedback_callback)
        repository.git.clear_checkout_context()
        feedback_callback("Synced current branch up to remote")
        return 0
    else:
        pulled_updates_count = bm.get_commits_behind()
        _pull(repository, branch_name, override, feedback_callback, username=username)
        should_push = not pull_only
        if should_push:
            # Skip pushing back up if set to pull_only
            push_tokens = f'git push origin {branch_name}'.split()
            if branch_name not in bm.branches_remote:
                push_tokens.insert(2, "--set-upstream")
            call_subprocess(push_tokens, cwd=repository.root_dir)
            feedback_callback("Sync complete")
        else:
            feedback_callback("Pull complete")

        repository.git.clear_checkout_context()
        return pulled_updates_count


def migrate_labbook_schema(labbook: LabBook) -> None:
    # Fallback point in case of a problem
    initial_commit = labbook.git.commit_hash

    try:
        migrate_schema_to_current(labbook.root_dir)
    except Exception as e:
        logger.exception(e)
        call_subprocess(f'git reset --hard {initial_commit}'.split(), cwd=labbook.root_dir)
        raise

    msg = f"Migrate schema to {CURRENT_LABBOOK_SCHEMA}"
    labbook.git.add(labbook.config_path)
    cmt = labbook.git.commit(msg, author=labbook.author, committer=labbook.author)
    adr = ActivityDetailRecord(ActivityDetailType.LABBOOK, show=True,
                               importance=100,
                               action=ActivityAction.EDIT)

    adr.add_value('text/plain', msg)
    ar = ActivityRecord(ActivityType.LABBOOK, message=msg, show=True,
                        importance=255, linked_commit=cmt.hexsha,
                        tags=['schema', 'update', 'migration'])
    ar.add_detail_object(adr)
    ars = ActivityStore(labbook)
    ars.create_activity_record(ar)


def migrate_labbook_untracked_space(labbook: LabBook) -> None:

    gitignore_path = os.path.join(labbook.root_dir, '.gitignore')
    gitignored_lines = open(gitignore_path).readlines()
    has_untracked_dir = any(['output/untracked' in l.strip() for l in gitignored_lines])
    if not has_untracked_dir:
        with open(gitignore_path, 'a') as gi_file:
            gi_file.write('\n\n# Migrated - allow untracked area\n'
                          'output/untracked\n')
        labbook.sweep_uncommitted_changes(extra_msg="Added untracked area")

    # Make the untracked directory -- makedirs is no-op if already exists
    untracked_path = os.path.join(labbook.root_dir, 'output/untracked')
    if not os.path.exists(untracked_path):
        os.makedirs(untracked_path, exist_ok=True)


def migrate_labbook_branches(labbook: LabBook) -> None:
    bm = BranchManager(labbook)
    if 'gm.workspace' not in bm.active_branch:
        raise ValueError('Can only migrate branches if active branch contains'
                         '"gm.workspace"')

    master_branch = 'master'
    if master_branch in bm.branches_local:
        bm.remove_branch(master_branch)

    bm.create_branch(master_branch)
