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
import os
import re
import uuid
import yaml
import json
import time
import datetime
import gitdb
import redis_lock
from contextlib import contextmanager
from collections import OrderedDict
from redis import StrictRedis

from typing import (Any, Dict, List, Optional, Tuple)

from gtmcore.configuration import Configuration
from gtmcore.exceptions import GigantumLockedException, GigantumException
from gtmcore.configuration.utils import call_subprocess
from gtmcore.gitlib import get_git_interface, GitAuthor, GitRepoInterface
from gtmcore.logging import LMLogger
from gtmcore.activity import ActivityStore, ActivityType, ActivityRecord, ActivityDetailType, ActivityDetailRecord, \
    ActivityAction

logger = LMLogger.get_logger()


def check_git_tracked(repo: GitRepoInterface) -> None:
    """Validates that a Git repo is not leaving any uncommitted changes or files.
    Raises ValueError if it does."""

    try:
        # This is known to throw a ValueError if the repo is bare - i.e., does not yet
        # have any commits.
        # TODO - A better way to determine if the repo does not yet have any commits.
        # I tried a variety of ways and this try-catch-ValueError is the only thing that works.
        repo.commit_hash
    except ValueError as e:
        logger.info("Not checking Git status, appears to be uninitialized.")
        return

    result_status = repo.status()
    # status_key is one of "staged", "unstaged", "untracked"
    for status_key in result_status.keys():
        n = result_status.get(status_key)
        if n:
            errmsg = f"Found unexpected {status_key} files in repo {n} aborting."
            logger.error(errmsg)
            raise ValueError(errmsg)
            # TODO - Rollback, revert?


class Repository(object):
    """Class representing a Gigantum Repository Object"""
    # Set static attributes to the proper type in child classes
    _default_activity_type = ActivityType.LABBOOK
    _default_activity_detail_type = ActivityDetailType.LABBOOK
    _default_activity_section = "Default Section"

    def __init__(self, config_file: Optional[str] = None, author: Optional[GitAuthor] = None) -> None:
        self.client_config = Configuration(config_file)

        # Create gitlib instance
        self.git = get_git_interface(self.client_config.config["git"])

        # If author is set, update git interface
        if author:
            self.author = author

        # Repository Properties
        self._root_dir: Optional[str] = None  # The root dir is the location of the labbook this instance represents
        self._data: Dict[str, Any] = {}
        self._checkout_id: Optional[str] = None

        # Redis instance for the LabBook lock
        self._lock_redis_client: Optional[StrictRedis] = None

        # Persisted Favorites data for more efficient file listing operations
        self._favorite_keys: Optional[Dict[str, Any]] = None

    def _validate_git(method_ref):  #type: ignore
        """Definition of decorator that validates git operations.

        Note! The approach here is taken from Stack Overflow answer:
         https://stackoverflow.com/a/1263782
        """
        def __validator(self, *args, **kwargs):
            # Note, `create_activity_record` indicates whether this filesystem operation should be immediately
            # put into the Git history via an activity record. For now, if this is not true, then do not immediately
            # put this in the Git history. Generally, calls from within this class will set it to false (and do commits
            # later) and calls from outside will set create_activity_record to True.
            if kwargs.get('create_activity_record') is True:
                try:
                    check_git_tracked(self.git)
                    n = method_ref(self, *args, **kwargs)  #type: ignore
                except ValueError:
                    self.sweep_uncommitted_changes()
                    n = method_ref(self, *args, **kwargs)  # type: ignore
                    self.sweep_uncommitted_changes()
                finally:
                    check_git_tracked(self.git)
            else:
                n = method_ref(self, *args, **kwargs)  # type: ignore
            return n
        return __validator

    @contextmanager
    def lock(self, lock_key: Optional[str] = None, failfast: bool = False):
        """A context manager for locking labbook operations that is decorator compatible

        Manages the lock process along with catching and logging exceptions that may occur

        Args:
            lock_key: The lock key to override the default value.
            failfast: Raise LabbookLockedException right away if labbook
                      is already locked. Do not block.

        """
        lock: redis_lock.Lock = None
        try:
            config = self.client_config.config['lock']

            # Get a redis client
            if not self._lock_redis_client:
                self._lock_redis_client = StrictRedis(host=config['redis']['host'],
                                                      port=config['redis']['port'],
                                                      db=config['redis']['db'])

            # Create a lock key
            if not lock_key:
                lock_key = f'filesystem_lock|{self.key}'

            # Get a lock object
            lock = redis_lock.Lock(self._lock_redis_client, lock_key,
                                   expire=config['expire'],
                                   auto_renewal=config['auto_renewal'],
                                   strict=config['redis']['strict'])

            # Get the lock - blocking and timeout kw args can not
            # be used simultaneously
            if failfast:
                lock_kwargs = {'blocking': False}
            else:
                lock_kwargs = {'timeout': config['timeout']}

            if lock.acquire(**lock_kwargs):
                # Do the work
                start_time = time.time()
                yield
                if config['expire']:
                    if (time.time() - start_time) > config['expire']:
                        logger.error(
                            f"Task took more than {config['expire']}s. File locking possibly invalid.")
            else:
                if failfast:
                    raise GigantumLockedException("Cannot interrupt operation in progress")
                raise IOError(f"Could not acquire file system lock within {config['timeout']} seconds.")

        except Exception as e:
            logger.error(e)
            raise
        finally:
            # Release the Lock
            if lock:
                try:
                    lock.release()
                except redis_lock.NotAcquired as e:
                    # if you didn't get the lock and an error occurs, you probably won't be able to release, so log.
                    logger.error(e)

    @property
    def root_dir(self) -> str:
        if not self._root_dir:
            raise ValueError("No repository root dir specified. Could not get root dir")
        return self._root_dir

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        return self._data

    @property
    def author(self) -> Optional[GitAuthor]:
        return self.git.author

    @author.setter
    def author(self, value: Optional[GitAuthor]) -> None:
        if value:
            self.git.update_author(author=value)

    @property
    def schema(self) -> int:
        if self._data:
            return self._data["schema"]
        else:
            raise ValueError("No schema stored in repository data.")

    @property
    def id(self) -> str:
        """Method to get the repository unique ID (often from the gigantum.yaml file)"""
        raise NotImplemented

    @property
    def name(self) -> str:
        """Method to get the repository name (often from the gigantum.yaml file)"""
        raise NotImplemented

    @name.setter
    def name(self, value: str) -> None:
        """Method to set the repository name (often from the gigantum.yaml file)"""
        raise NotImplemented

    @property
    def key(self) -> str:
        """Return a unique key for identifying and locating a labbbok.

        DEPRECATED

        Note: A labbook does not exist notionally outside of a directory structure, therefore
        part of the key is determined by this structure. """

        dir_elements = self.root_dir.split(os.sep)
        return "|".join([dir_elements[-4], dir_elements[-3], dir_elements[-1]])

    @property
    def active_branch(self) -> str:
        return self.git.get_current_branch_name()

    @staticmethod
    def make_path_relative(path_str: str) -> str:
        while len(path_str or '') >= 1 and path_str[0] == os.path.sep:
            path_str = path_str[1:]
        return path_str

    @property
    def checkout_id(self) -> str:
        """Property that provides a unique ID for a checkout. This is used in the activity feed database to ensure
        parallel work in the same branch will merge safely

        Returns:
            str
        """
        if self._checkout_id:
            return self._checkout_id
        else:
            # Try to load checkout ID from disk
            checkout_file = os.path.join(self.root_dir, '.gigantum', '.checkout')
            if os.path.exists(checkout_file):
                # Load from disk
                with open(checkout_file, 'rt') as cf:
                    self._checkout_id = cf.read()
            else:
                # Create a new checkout ID and file
                self._checkout_id = f"{self.key}|{self.git.get_current_branch_name()}|{uuid.uuid4().hex[0:10]}"
                self._checkout_id = self._checkout_id.replace('|', '-')
                with open(checkout_file, 'wt') as cf:
                    cf.write(self._checkout_id)

                # Log new checkout ID creation
                logger.info(f"Created new checkout context ID {self._checkout_id}")
            return self._checkout_id

    @property
    def favorite_keys(self) -> Dict[str, List[Optional[str]]]:
        """Property that provides cached favorite data for file listing operations

        Returns:
            dict
        """
        if not self._favorite_keys:
            data: Dict[str, list] = dict()
            for section in ['code', 'input', 'output']:
                data[section] = list(self.get_favorites(section).keys())

            self._favorite_keys = data

        return self._favorite_keys

    @property
    def has_remote(self):
        """Return True if the Repository has a remote that it can push/pull to/from

        Returns:
            bool indicating whether a remote is set.
        """
        try:
            return len(self.git.list_remotes()) > 0
        except Exception as e:
            logger.exception(e)
            raise GigantumException(e)

    @property
    def remote(self) -> Optional[str]:
        try:
            r = self.git.list_remotes()
            if r:
                return r[0]['url']
            else:
                return None
        except Exception as e:
            logger.exception(e)
            raise GigantumException(e)

    @property
    def creation_date(self) -> Optional[datetime.datetime]:
        """Return the creation date of the repository"""
        raise NotImplemented

    @property
    def modified_on(self) -> datetime.datetime:
        return self.git.log(max_count=1)[0]['committed_on']

    @property
    def build_details(self) -> Optional[Dict[str, str]]:
        """Return the build info for the application that created the repository"""
        raise NotImplemented

    @property
    def is_repo_clean(self) -> bool:
        """Return true if the Git repo is ready to be push, pulled, or merged. I.e., no uncommitted changes
        or un-tracked files. """

        try:
            result_status = self.git.status()
            for status_key in result_status.keys():
                n = result_status.get(status_key)
                if n:
                    logger.warning(f"Found {status_key} in {str(self)}: {n}")
                    return False
            return True
        except gitdb.exc.BadName as e:
            logger.error(e)
            return False

    def _set_root_dir(self, new_root_dir: str) -> None:
        """Update the root directory and also reconfigure the git instance

        Returns:
            None
        """
        # Be sure to expand in case a user dir string is used
        self._root_dir = os.path.expanduser(new_root_dir)

        # Update the git working directory
        self.git.set_working_directory(self.root_dir)

    def _save_gigantum_data(self) -> None:
        """Method to save changes to the Repository metadata file

        Returns:
            None
        """
        if not self.root_dir:
            raise ValueError("No root directory assigned to repository. Failed to get root directory.")

        with open(os.path.join(self.root_dir, ".gigantum", "gigantum.yaml"), 'wt') as gf:
            gf.write(yaml.safe_dump(self._data, default_flow_style=False))
            gf.flush()

    def _load_gigantum_data(self) -> None:
        """Method to load the repository YAML file to a dictionary

        Returns:
            None
        """
        if not self.root_dir:
            raise ValueError("No root directory assigned to repository. Failed to get root directory.")

        with open(os.path.join(self.root_dir, ".gigantum", "gigantum.yaml"), 'rt') as gf:
            self._data = yaml.safe_load(gf)

    def _validate_gigantum_data(self) -> None:
        """Method to validate the Repository metadata file contents

        Returns:
            None
        """
        raise NotImplemented

    def validate_section(self, section: str) -> None:
        """Simple method to validate a user provided section name

        Args:
            section(str): Name of a LabBook section

        Returns:
            None
        """
        if section not in ['code', 'input', 'output']:
            raise ValueError("section (code, input, output) must be provided.")

    def sweep_uncommitted_changes(self, upload: bool = False,
                                  extra_msg: Optional[str] = None,
                                  show: bool = False) -> None:
        """ Sweep all changes into a commit, and create activity record.
            NOTE: This method MUST be called inside a lock.

        Args:
            upload(bool): Flag indicating if this was from a batch upload
            extra_msg(str): Optional string used to augment the activity message
            show(bool): Optional flag indicating if the result of this sweep is important enough to be shown in the feed

        Returns:

        """
        result_status = self.git.status()
        if any([result_status[k] for k in result_status.keys()]):
            self.git.add_all()
            self.git.commit("Sweep of uncommitted changes")

            ar = ActivityRecord(self._default_activity_type,
                                message="--overwritten--",
                                show=show,
                                importance=255,
                                linked_commit=self.git.commit_hash,
                                tags=['save'])
            if upload:
                ar.tags.append('upload')
            ar, newcnt, modcnt, delcnt = self.process_sweep_status(ar, result_status)
            nmsg = f"{newcnt} new file(s). " if newcnt > 0 else ""
            mmsg = f"{modcnt} modified file(s). " if modcnt > 0 else ""
            dmsg = f"{delcnt} deleted file(s). " if delcnt > 0 else ""

            message = f"{extra_msg or ''}" \
                      f"{'Uploaded ' if upload else ''}" \
                      f"{nmsg}{mmsg}{dmsg}"

            # This is used to handle if you try to delete an empty directory. This shouldn't technically happen, but if
            # a user manages to create an empty dir outside the client, we should handle it gracefully
            ar.message = "No detected changes" if not message else message
            ars = ActivityStore(self)
            ars.create_activity_record(ar)
        else:
            logger.info(f"{str(self)} no changes to sweep.")

    @staticmethod
    def get_activity_type_from_section(section_name: str) -> Tuple[ActivityType, ActivityDetailType, str]:
        """Method to get activity and detail types from the section name

        Args:
            section_name(str): section subdirectory/identifier (code, input, output)

        Returns:
            tuple
        """
        if section_name == 'code':
            activity_detail_type = ActivityDetailType.CODE
            activity_type = ActivityType.CODE
            section = "Code"
        elif section_name == 'input':
            activity_detail_type = ActivityDetailType.INPUT_DATA
            activity_type = ActivityType.INPUT_DATA
            section = "Input Data"
        elif section_name == 'output':
            activity_detail_type = ActivityDetailType.OUTPUT_DATA
            activity_type = ActivityType.OUTPUT_DATA
            section = "Output Data"
        else:
            # This is the labbook root, since we can't catagorize keep generic
            activity_detail_type = Repository._default_activity_detail_type
            activity_type = Repository._default_activity_type
            section = Repository._default_activity_section

        return activity_type, activity_detail_type, section

    @staticmethod
    def infer_section_from_relative_path(relative_path: str) -> Tuple[ActivityType, ActivityDetailType, str]:
        """Method to try to infer the "section" from a relative file path

        Args:
            relative_path(str): a relative file path within a LabBook section (code, input, output)

        Returns:
            tuple
        """
        # If leading slash, remove it first
        if relative_path[0] == os.path.sep:
            relative_path = relative_path[1:]

        # if no trailing slash add it. simple parsing below assumes no trailing and a leading slash to work.
        if relative_path[-1] != os.path.sep:
            relative_path = relative_path + os.path.sep

        possible_section, _ = relative_path.split('/', 1)
        return Repository.get_activity_type_from_section(possible_section)

    def process_sweep_status(self, result_obj: ActivityRecord,
                             status: Dict[str, Any]) -> Tuple[ActivityRecord, int, int, int]:
        sections = []
        ncnt = 0
        for filename in status['untracked']:
            # skip any file in .git or .gigantum dirs
            if ".git" in filename or ".gigantum" in filename:
                continue
            activity_type, activity_detail_type, section = self.infer_section_from_relative_path(filename)
            adr = ActivityDetailRecord(activity_detail_type, show=False, importance=max(255 - ncnt, 0),
                                       action=ActivityAction.CREATE)
            sections.append(section)
            if section == self._default_activity_section:
                msg = f"Created new file `{filename}` in the {self._default_activity_section}."
                msg = f"{msg}Note, it is best practice to use the Code, Input, and Output sections exclusively."
            else:
                msg = f"Created new {section} file `{filename}`"
            adr.add_value('text/markdown', msg)
            result_obj.add_detail_object(adr)
            ncnt += 1

        # If all modifications were of same section
        new_section_set = set(sections)
        if ncnt > 0 and len(new_section_set) == 1:
            if "Code" in new_section_set:
                result_obj.type = ActivityType.CODE
            elif "Input Data" in new_section_set:
                result_obj.type = ActivityType.INPUT_DATA
            elif "Output Data" in new_section_set:
                result_obj.type = ActivityType.OUTPUT_DATA

        mcnt = 0
        dcnt = 0
        msections = []
        changes = status['unstaged']
        changes.extend(status['staged'])
        for filename, change in changes:
            # skip any file in .git or .gigantum dirs
            if (".git" in filename and ".gitkeep" not in filename) or ".gigantum" in filename:
                continue

            activity_type, activity_detail_type, section = self.infer_section_from_relative_path(filename)
            msections.append(section)

            if change == "deleted":
                action = ActivityAction.DELETE
                dcnt += 1
            elif change == "added":
                action = ActivityAction.CREATE
                mcnt += 1
            elif change == "modified":
                action = ActivityAction.EDIT
                mcnt += 1
            elif change == "renamed":
                action = ActivityAction.EDIT
                mcnt += 1
            else:
                action = ActivityAction.NOACTION
                mcnt += 1

            adr = ActivityDetailRecord(activity_detail_type, show=False, importance=max(255 - mcnt, 0), action=action)
            if ".gitkeep" in filename:
                directory_name, _ = filename.split('.gitkeep')
                adr.add_value('text/markdown', f"{change[0].upper() + change[1:]} {section} directory `{directory_name}`")
            else:
                adr.add_value('text/markdown', f"{change[0].upper() + change[1:]} {section} file `{filename}`")
            result_obj.add_detail_object(adr)

        modified_section_set = set(msections)
        if result_obj.type == self._default_activity_type:
            # If new files are from different sections or no new files, you'll still be LABBOOK or DATASET type
            if (mcnt+dcnt) > 0 and len(modified_section_set) == 1:
                # If there have been modified files and they are all from the same section
                if len(new_section_set) == 0 or new_section_set == modified_section_set:
                    # If there have been only modified files from a single section,
                    # or new files are from the same section
                    if "Code" in modified_section_set:
                        result_obj.type = ActivityType.CODE
                    elif "Input Data" in modified_section_set:
                        result_obj.type = ActivityType.INPUT_DATA
                    elif "Output Data" in modified_section_set:
                        result_obj.type = ActivityType.OUTPUT_DATA
        elif (mcnt+dcnt) > 0:
            if len(modified_section_set) > 1 or new_section_set != modified_section_set:
                # Mismatch between new and modify or within modify, just use catchall LABBOOK or DATASET type
                result_obj.type = self._default_activity_type

        # Return additionally new file cnt (ncnt) and modified (mcnt)
        return result_obj, ncnt, mcnt, dcnt

    def checkout_branch(self, branch_name: str, new: bool = False) -> None:
        """
        Checkout a Git branch. Create a new branch locally.

        Args:
            branch_name(str): Name of branch to checkout or create
            new(bool): Indicates this branch should be created.

        Return:
            None
        """
        if not self.is_repo_clean:
            raise GigantumException(f"Cannot checkout {branch_name}: Untracked and/or uncommitted changes")

        try:
            if new:
                logger.info(f"Creating a new branch {branch_name}...")
                self.git.create_branch(branch_name)
            logger.info(f"Checking out branch {branch_name}...")
            self.git.checkout(branch_name=branch_name)

            # Clear out checkout context
            if self._root_dir and os.path.exists(os.path.join(self._root_dir, ".gigantum", ".checkout")):
                os.remove(os.path.join(self._root_dir, ".gigantum", ".checkout"))
            self._checkout_id = None
        except ValueError as e:
            logger.error(f"Cannot checkout branch {branch_name}: {e}")
            raise GigantumException(e)

    def add_remote(self, remote_name: str, url: str) -> None:
        """Add a new git remote

        Args:
            remote_name: Name of remote, e.g., "origin"
            url: Path to remote Git repository.
        """

        try:
            logger.info(f"Adding new remote {remote_name} at {url}")
            self.git.add_remote(remote_name, url)
            self.git.fetch(remote=remote_name)
        except Exception as e:
            raise GigantumException(e)

    def remove_remote(self, remote_name: Optional[str] = "origin") -> None:
        """Remove a remove from the git config

        Args:
            remote_name: Optional name of remote (default "origin")
        """
        try:
            logger.info(f"Removing remote {remote_name} from {str(self)}")
            self.git.remove_remote(remote_name)
        except Exception as e:
            raise GigantumException(e)

    def remove_lfs_remotes(self) -> None:
        """Remove all LFS endpoints.

        Each LFS enpoint has its own entry in the git config. It takes the form of the following:

        ```
        [lfs "https://repo.location.whatever"]
            access = basic
        ```

        In order to get the section name, which is "lfs.https://repo.location.whatever", we need to search
        by all LFS fields and remove them (and in order to get the section need to strip the variables off the end).

        Returns:
            None
        """
        lfs_sections = call_subprocess(['git', 'config', '--get-regexp', 'lfs.http*'], cwd=self.root_dir).split('\n')
        logger.info(f"LFS entries to delete are {lfs_sections}")
        for lfs_sec in set([n for n in lfs_sections if n]):
            var = lfs_sec.split(' ')[0]
            section = '.'.join(var.split('.')[:-1])
            call_subprocess(['git', 'config', '--remove-section', section], cwd=self.root_dir)

    def get_branches(self) -> Dict[str, List[str]]:
        """Return all branches a Dict of Lists. Dict contains two keys "local" and "remote".

        Args:
            None

        Returns:
            Dictionary of lists for "remote" and "local" branches.
        """

        try:
            # Note - do NOT fetch here - fetch should be done before this is called.
            return self.git.list_branches()
        except Exception as e:
            # Unsure what specific exception add_remote creates, so make a catchall.
            logger.exception(e)
            raise GigantumException(e)

    def create_favorite(self, section: str, relative_path: str,
                        description: Optional[str] = None, is_dir: bool = False) -> Dict[str, Any]:
        """Mark an existing file as a Favorite

        Data is stored in a json document, with each object name the relative path to the file

        Args:
            section(str): lab book subdir where file exists (code, input, output)
            relative_path(str): Relative path within the section to the file to favorite
            description(str): A short string containing information about the favorite
            is_dir(bool): If true, relative_path will expected to be a directory

        Returns:
            dict
        """
        if section not in ['code', 'input', 'output']:
            raise ValueError("Favorites only supported in `code`, `input`, and `output` Lab Book directories")

        # Generate desired absolute path
        target_path_rel = os.path.join(section, relative_path)

        # Remove any leading "/" -- without doing so os.path.join will break.
        target_path_rel = self.make_path_relative(target_path_rel)
        target_path = os.path.join(self.root_dir, target_path_rel.replace('..', ''))

        if not os.path.exists(target_path):
            raise ValueError(f"Target file/dir `{target_path}` does not exist")

        if is_dir != os.path.isdir(target_path):
            raise ValueError(f"Target `{target_path}` a directory")

        logger.info(f"Marking {target_path} as favorite")

        # Open existing Favorites json if exists
        favorites_dir = os.path.join(self.root_dir, '.gigantum', 'favorites')
        if not os.path.exists(favorites_dir):
            # No favorites have been created
            os.makedirs(favorites_dir)

        favorite_data: Dict[str, Any] = dict()
        if os.path.exists(os.path.join(favorites_dir, f'{section}.json')):
            # Read existing data
            with open(os.path.join(favorites_dir, f'{section}.json'), 'rt') as f_data:
                favorite_data = json.load(f_data)

        # Ensure the key has a trailing slash if a directory to meet convention
        if is_dir:
            if relative_path[-1] != os.path.sep:
                relative_path = relative_path + os.path.sep

        if relative_path in favorite_data:
            raise ValueError(f"Favorite `{relative_path}` already exists in {section}.")

        # Get last index
        if favorite_data:
            last_index = max([int(favorite_data[x]['index']) for x in favorite_data])
            index_val = last_index + 1
        else:
            index_val = 0

        # Create new record
        favorite_data[relative_path] = {"key": relative_path,
                                        "index": index_val,
                                        "description": description,
                                        "is_dir": is_dir}

        # Always be sure to sort the ordered dict
        favorite_data = OrderedDict(sorted(favorite_data.items(), key=lambda val: val[1]['index']))

        # Write favorites to lab book
        fav_data_file = os.path.join(favorites_dir, f'{section}.json')
        with open(fav_data_file, 'wt') as f_data:
            json.dump(favorite_data, f_data, indent=2)

        # Remove cached favorite key data
        self._favorite_keys = None

        # Commit the changes
        self.git.add(fav_data_file)
        self.git.commit(f"Committing new Favorite file {fav_data_file}")

        return favorite_data[relative_path]

    def update_favorite(self, section: str, relative_path: str,
                        new_description: Optional[str] = None,
                        new_index: Optional[int] = None) -> Dict[str, Any]:
        """Mark an existing file as a Favorite

        Args:
            section(str): subdir where file exists (code, input, output)
            relative_path(str): Relative path within the section to the file to favorite
            new_description(str): A short string containing information about the favorite
            new_index(int): The position to move the favorite

        Returns:
            dict
        """
        if section not in ['code', 'input', 'output']:
            raise ValueError("Favorites only supported in `code`, `input`, and `output` Lab Book directories")

        # Open existing Favorites json
        favorites_file = os.path.join(self.root_dir, '.gigantum', 'favorites', f'{section}.json')
        if not os.path.exists(favorites_file):
            # No favorites have been created
            raise ValueError(f"No favorites exist in '{section}'. Create a favorite before trying to update")

        # Read existing data
        with open(favorites_file, 'rt') as f_data:
            favorite_data = json.load(f_data)

        # Ensure the favorite already exists is valid
        if relative_path not in favorite_data:
            raise ValueError(f"Favorite {relative_path} in section {section} does not exist. Cannot update.")

        # Update description if needed
        if new_description:
            logger.info(f"Updating description for {relative_path} favorite in section {section}.")
            favorite_data[relative_path]['description'] = new_description

        # Update the index if needed
        if new_index is not None:
            if new_index < 0 or new_index > len(favorite_data.keys()) - 1:
                raise ValueError(f"Invalid index during favorite update: {new_index}")

            if new_index < favorite_data[relative_path]['index']:
                # Increment index of all items "after" updated index
                for fav in favorite_data:
                    if favorite_data[fav]['index'] >= new_index:
                        favorite_data[fav]['index'] = favorite_data[fav]['index'] + 1

            elif new_index > favorite_data[relative_path]['index']:
                # Decrement index of all items "before" updated index
                for fav in favorite_data:
                    if favorite_data[fav]['index'] <= new_index:
                        favorite_data[fav]['index'] = favorite_data[fav]['index'] - 1

            # Update new index
            favorite_data[relative_path]['index'] = new_index

        # Always be sure to sort the ordered dict
        favorite_data = OrderedDict(sorted(favorite_data.items(), key=lambda val: val[1]['index']))

        # Write favorites to lab book
        with open(favorites_file, 'wt') as f_data:
            json.dump(favorite_data, f_data, indent=2)

        # Remove cached favorite key data
        self._favorite_keys = None

        # Commit the changes
        self.git.add(favorites_file)
        self.git.commit(f"Committing update to Favorite file {favorites_file}")

        return favorite_data[relative_path]

    def remove_favorite(self, section: str, relative_path: str) -> None:
        """Mark an existing file as a Favorite

        Args:
            section(str): subdir where file exists (code, input, output)
            relative_path(str): Relative path within the section to the file to favorite

        Returns:
            None
        """
        if section not in ['code', 'input', 'output']:
            raise ValueError("Favorites only supported in `code`, `input`, and `output` directories")

        # Open existing Favorites json if exists
        favorites_dir = os.path.join(self.root_dir, '.gigantum', 'favorites')

        data_file = os.path.join(favorites_dir, f'{section}.json')
        if not os.path.exists(data_file):
            raise ValueError(f"No {section} favorites have been created yet. Cannot remove item {relative_path}!")

        # Read existing data
        with open(data_file, 'rt') as f_data:
            favorite_data = json.load(f_data)

        if relative_path not in favorite_data:
            raise ValueError(f"Favorite {relative_path} not found in {section}. Cannot remove.")

        # Remove favorite at index value
        del favorite_data[relative_path]

        # Always be sure to sort the ordered dict
        favorite_data = OrderedDict(sorted(favorite_data.items(), key=lambda val: val[1]['index']))

        # Reset index vals
        for idx, fav in enumerate(favorite_data):
            favorite_data[fav]['index'] = idx

        # Write favorites to back lab book
        with open(data_file, 'wt') as f_data:
            json.dump(favorite_data, f_data, indent=2)

        logger.info(f"Removed {section} favorite {relative_path}")

        # Remove cached favorite key data
        self._favorite_keys = None

        # Commit the changes
        self.git.add(data_file)
        self.git.commit(f"Committing update to Favorite file {data_file}")

        return None

    def get_favorites(self, section: str) -> OrderedDict:
        """Get Favorite data in an OrderedDict, sorted by index

        Args:
            section(str): subdir where file exists (code, input, output)

        Returns:
            None
        """
        if section not in ['code', 'input', 'output']:
            raise ValueError("Favorites only supported in `code`, `input`, and `output` directories")

        favorite_data: OrderedDict = OrderedDict()
        favorites_dir = os.path.join(self.root_dir, '.gigantum', 'favorites')
        if os.path.exists(os.path.join(favorites_dir, f'{section}.json')):
            # Read existing data
            with open(os.path.join(favorites_dir, f'{section}.json'), 'rt') as f_data:
                favorite_data = json.load(f_data, object_pairs_hook=OrderedDict)

        return favorite_data

    def log(self, username: str = None, max_count: int = 10):
        """Method to list commit history of a Labbook

        Args:
            username(str): Username to filter the query on
            max_count: Max number of log records to retrieve

        Returns:
            dict
        """
        # TODO: Add additional optional args to the git.log call to support further filtering
        return self.git.log(max_count=max_count, author=username)

    def log_entry(self, commit: str):
        """Method to get a single log entry by commit

        Args:
            commit(str): commit hash of the entry

        Returns:
            dict
        """
        return self.git.log_entry(commit)

    def write_readme(self, contents: str) -> None:
        """Method to write a string to the readme file within the repository. Must write ENTIRE document at once.

        Args:
            contents(str): entire readme document in markdown format

        Returns:
            None
        """
        # Validate readme data
        if len(contents) > (1000000 * 5):
            raise ValueError("Readme file is larger than the 5MB limit")

        if type(contents) is not str:
            raise TypeError("Invalid content. Must provide string")

        readme_file = os.path.join(self.root_dir, 'README.md')
        readme_exists = os.path.exists(readme_file)

        # Write file to disk
        with open(readme_file, 'wt') as rf:
            rf.write(contents)

        # Create commit
        if readme_exists:
            commit_msg = f"Updated README file"
            action = ActivityAction.EDIT
        else:
            commit_msg = f"Added README file"
            action = ActivityAction.CREATE

        self.git.add(readme_file)
        commit = self.git.commit(commit_msg)

        # Create detail record
        adr = ActivityDetailRecord(self._default_activity_detail_type, show=False, importance=0, action=action)
        adr.add_value('text/plain', commit_msg)

        # Create activity record
        ar = ActivityRecord(self._default_activity_type,
                            message=commit_msg,
                            show=False,
                            importance=255,
                            linked_commit=commit.hexsha,
                            tags=['readme'])
        ar.add_detail_object(adr)

        # Store
        ars = ActivityStore(self)
        ars.create_activity_record(ar)

    def get_readme(self) -> Optional[str]:
        """Method to read the readme document

        Returns:
            (str): entire readme document in markdown format
        """
        readme_file = os.path.join(self.root_dir, 'README.md')
        contents = None
        if os.path.exists(readme_file):
            with open(readme_file, 'rt') as rf:
                contents = rf.read()
        return contents
