from typing import Callable, List, Dict, Any, Tuple, Optional
import pickle
import os
from enum import Enum
import shutil
import asyncio
from collections import OrderedDict, namedtuple
from natsort import natsorted
import copy
from pathlib import Path

from gtmcore.activity import ActivityStore, ActivityRecord, ActivityDetailType, ActivityType,\
    ActivityAction, ActivityDetailRecord
from gtmcore.dataset.dataset import Dataset
from gtmcore.dataset.manifest.hash import SmartHash
from gtmcore.dataset.cache import get_cache_manager_class, CacheManager
from gtmcore.dataset.manifest.eventloop import get_event_loop
from gtmcore.logging import LMLogger

logger = LMLogger.get_logger()


class FileChangeType(Enum):
    """Enumeration representing types of file changes"""
    NOCHANGE = 0
    CREATED = 1
    MODIFIED = 2
    DELETED = 3


StatusResult = namedtuple('StatusResult', ['created', 'modified', 'deleted'])


class Manifest(object):
    """Class to handle file file manifest"""

    def __init__(self, dataset: Dataset, logged_in_username: Optional[str] = None) -> None:
        self.dataset = dataset

        cache_mgr_class = get_cache_manager_class(self.dataset.client_config)
        self.cache_mgr: CacheManager = cache_mgr_class(self.dataset, logged_in_username)

        self.hasher = SmartHash(dataset.root_dir, self.cache_mgr.cache_root,
                                self.dataset.git.repo.head.commit.hexsha)

        self.ignore_file = os.path.join(dataset.root_dir, ".gigantumignore")

        self.manifest = self._load_manifest()

        # TODO: Support ignoring files
        # self.ignored = self._load_ignored()

    @property
    def dataset_revision(self) -> str:
        """Property to get the current revision hash of the dataset

        Returns:
            str
        """
        return self.dataset.git.repo.head.commit.hexsha

    def _load_manifest(self) -> OrderedDict:
        """Method to load the manifest file

        Returns:
            dict
        """
        manifest_file = os.path.join(self.dataset.root_dir, 'manifest', 'manifest0')
        if os.path.exists(manifest_file):
            with open(manifest_file, 'rb') as mf:
                return pickle.load(mf)
        else:
            return OrderedDict()

    def _save_manifest(self) -> None:
        """Method to load the manifest file

        Returns:
            dict
        """
        with open(os.path.join(self.dataset.root_dir, 'manifest', 'manifest0'), 'wb') as mf:
            pickle.dump(self.manifest, mf, pickle.HIGHEST_PROTOCOL)

    def get_abs_path(self, relative_path: str) -> str:
        """Method to generate the absolute path to a file in the cache at the current revision

        Args:
            relative_path:

        Returns:

        """
        return self.hasher.get_abs_path(relative_path)

    def queue_to_push(self, obj: str, rel_path: str, revision: str) -> None:
        """Method to queue and object for push to remote storage backend

        Objects to push are stored in a file named with the revision at which the files were written. This is different
        from the revision that contains the files (after written and untracked, changes are committed and then an
        activity record is created with another commit)

        Args:
            obj: object path
            revision: revision of the dataset the object exists in
            rel_path: Objects relative file path in the dataset

        Returns:

        """
        if not os.path.exists(obj):
            raise ValueError("Object does not exist. Failed to add to push queue.")

        push_dir = os.path.join(self.cache_mgr.cache_root, 'objects', '.push')
        if not os.path.exists(push_dir):
            os.makedirs(push_dir)

        with open(os.path.join(push_dir, revision), 'at') as fh:
            fh.write(f"{rel_path},{obj}\n")

    def get_change_type(self, path) -> FileChangeType:
        """

        Args:
            path:

        Returns:

        """
        if self.hasher.is_cached(path):
            if self.hasher.has_changed_fast(path):
                result = FileChangeType.MODIFIED
            else:
                result = FileChangeType.NOCHANGE
        else:
            if path in self.manifest.keys():
                # No fast hash, but exists in manifest. User just edited a file that hasn't been pulled
                result = FileChangeType.MODIFIED
            else:
                # No fast hash, not in manifest.
                result = FileChangeType.CREATED
        return result

    def status(self) -> StatusResult:
        """

        Returns:

        """
        # TODO: think about how to send batches to get_change_type
        status: Dict[str, List] = {"created": [], "modified": [], "deleted": []}
        all_files = list()
        revision_directory = os.path.join(self.cache_mgr.cache_root, self.dataset_revision)

        for root, dirs, files in os.walk(revision_directory):
            _, folder = root.split(revision_directory)
            if len(folder) > 0:
                if folder[0] == os.path.sep:
                    folder = folder[1:]

            for d in dirs:
                # TODO: Check for ignored
                rel_path = os.path.join(folder, d) + os.path.sep  # All folders are represented with a trailing slash
                all_files.append(rel_path)
                change = self.get_change_type(rel_path)
                if change == FileChangeType.NOCHANGE:
                    continue
                elif change == FileChangeType.MODIFIED:
                    status['modified'].append(rel_path)
                elif change == FileChangeType.CREATED:
                    status['created'].append(rel_path)
                else:
                    raise ValueError(f"Invalid Change type: {change}")

            for file in files:
                # TODO: Check for ignored
                if file in ['.smarthash', '.DS_STORE']:
                    continue

                rel_path = os.path.join(folder, file)
                all_files.append(rel_path)
                change = self.get_change_type(rel_path)
                if change == FileChangeType.NOCHANGE:
                    continue
                elif change == FileChangeType.MODIFIED:
                    status['modified'].append(rel_path)
                elif change == FileChangeType.CREATED:
                    status['created'].append(rel_path)
                else:
                    raise ValueError(f"Invalid Change type: {change}")

        # De-dup and sort
        status['created'] = list(set(status['created']))
        status['modified'] = list(set(status['modified']))
        status['modified'] = natsorted(status['modified'])
        status['created'] = natsorted(status['created'])

        all_files = list(set(all_files))
        return StatusResult(created=status.get('created'), modified=status.get('modified'),
                            deleted=self.hasher.get_deleted_files(all_files))

    @staticmethod
    def _get_object_subdirs(object_id) -> Tuple[str, str]:
        """

        Args:
            object_id:

        Returns:

        """
        return object_id[0:8], object_id[8:16]

    def dataset_to_object_path(self, dataset_path: str) -> str:
        """

        Args:
            dataset_path:

        Returns:

        """
        data: Optional[dict] = self.manifest.get(dataset_path)
        if not data:
            raise ValueError(f"{dataset_path} not found in Dataset manifest.")

        hash_str: str = data['h']
        level1, level2 = self._get_object_subdirs(hash_str)
        return os.path.join(self.cache_mgr.cache_root, 'objects', level1, level2, hash_str)

    async def _async_move(self, source, destination):
        shutil.move(source, destination)

    async def _move_to_object_cache(self, relative_path, hash_str):
        """

        Args:
            relative_path:
            hash_str:

        Returns:

        """
        source = os.path.join(self.cache_mgr.cache_root, self.dataset_revision, relative_path)
        if os.path.isfile(source):
            level1, level2 = self._get_object_subdirs(hash_str)

            os.makedirs(os.path.join(self.cache_mgr.cache_root, 'objects', level1), exist_ok=True)
            os.makedirs(os.path.join(self.cache_mgr.cache_root, 'objects', level1, level2), exist_ok=True)

            destination = os.path.join(self.cache_mgr.cache_root, 'objects', level1, level2, hash_str)
            if os.path.isfile(destination):
                # Object already exists, no need to store again
                os.remove(source)
            else:
                # Move file to new object
                await self._async_move(source, destination)

            # Link object back
            os.link(destination, source)

            # Queue new object for push
            self.queue_to_push(destination, relative_path, self.dataset_revision)
        else:
            destination = source

        return destination

    def update(self, status: StatusResult = None) -> StatusResult:
        """

        Args:
            status:

        Returns:

        """
        if not status:
            status = self.status()

        update_files = copy.deepcopy(status.created)
        update_files.extend(status.modified)

        if update_files:
            # Hash Files
            hash_result = self.hasher.hash(update_files)

            # Move files into object cache and link back to the revision directory
            loop = get_event_loop()
            tasks = [asyncio.ensure_future(self._move_to_object_cache(fd.filename, fd.hash)) for fd in hash_result]
            loop.run_until_complete(asyncio.ensure_future(asyncio.wait(tasks)))

            # Update fast hash
            self.hasher.fast_hash(update_files)

            # Update manifest file
            for result in hash_result:
                _, file_bytes, mtime, ctime = result.fast_hash.split("||")
                self.manifest[result.filename] = {'h': result.hash,
                                                  'c': ctime,
                                                  'm': mtime,
                                                  'b': file_bytes}

        if status.deleted:
            self.hasher.delete_hashes(status.deleted)
            for f in status.deleted:
                del self.manifest[f]

        self._save_manifest()

        return status

    def _file_info(self, key, item) -> Dict[str, Any]:
        """

        Args:
            key:
            item:

        Returns:

        """
        # TODO: Support favorites
        abs_path = os.path.join(self.cache_mgr.cache_root, self.dataset_revision, key)
        return {'key': key,
                'size': item.get('b'),
                'is_favorite': False,
                'is_local': os.path.exists(abs_path),
                'is_dir': os.path.isdir(abs_path),
                'modified_at': int(item.get('m'))}

    def gen_file_info(self, key) -> Dict[str, Any]:
        """

        Args:
            key:
            item:

        Returns:

        """
        # TODO: Support favorites
        abs_path = self.get_abs_path(key)
        stat = os.stat(abs_path)
        is_dir = os.path.isdir(abs_path)

        return {'key': key,
                'size': str(stat.st_size) if not is_dir else '0',
                'is_favorite': False,
                'is_local': os.path.exists(abs_path),
                'is_dir': is_dir,
                'modified_at': stat.st_mtime}

    def get(self, dataset_path: str) -> dict:
        """Method to get the file info for a single file from the manifest

        Args:
            dataset_path: Relative path to the object within the dataset

        Returns:
        """
        item = self.manifest.get(dataset_path)
        return self._file_info(dataset_path, item)

    def list(self, first: int = None, after_index: int = 0) -> List[Dict[str, Any]]:
        """

        Args:
            first:
            after_index:

        Returns:

        """
        if first:
            if first <= 0:
                raise ValueError("`first` must be greater than 0")
        if after_index:
            if after_index < 0:
                raise ValueError("`after_index` must be greater or equal than 0")

        result = list()
        if first is not None:
            first = min(first + after_index, len(self.manifest))

        for key, item in list(self.manifest.items())[after_index:first]:
            result.append(self._file_info(key, item))

        return result

    def delete(self, path_list: List[str]) -> None:
        """Method to delete a list of files/folders from the dataset

        Args:
            path_list: List of relative paths in the dataset

        Returns:

        """
        revision_directory = os.path.join(self.cache_mgr.cache_root, self.dataset_revision)

        for path in path_list:
            target_path = os.path.join(revision_directory, path)
            if os.path.isdir(target_path):
                shutil.rmtree(target_path)
            else:
                os.remove(target_path)

        self.sweep_all_changes()

    def move(self, src_path: str, dest_path: str) -> List[Dict[str, Any]]:
        """Method to move/rename a file or directory in a dataset

        Args:
            src_path: The relative path in the dataset to the source file/folder
            dest_path: The relative path in the dataset to the destination file/folder

        Returns:

        """
        revision_directory = os.path.join(self.cache_mgr.cache_root, self.dataset_revision)
        src_rel_path = self.dataset.make_path_relative(src_path.replace('..', ''))
        dest_rel_path = self.dataset.make_path_relative(dest_path.replace('..', ''))
        src_abs_path = os.path.join(revision_directory, src_rel_path)
        dest_abs_path = os.path.join(revision_directory, dest_rel_path)

        src_type = 'directory' if os.path.isdir(src_abs_path) else 'file'

        if not os.path.exists(src_abs_path):
            raise ValueError(f"No src file or folder exists at `{src_abs_path}`")

        # Move
        result_path = shutil.move(src_abs_path, dest_abs_path)
        msg = f"Moved {src_type} `{src_rel_path}` to `{dest_rel_path}`"
        previous_revision_directory = os.path.join(self.cache_mgr.cache_root, self.dataset_revision)
        self.sweep_all_changes(extra_msg=msg)

        # Update paths due to relinking
        revision_directory = os.path.join(self.cache_mgr.cache_root, self.dataset_revision)
        final_rel_path = self.dataset.make_path_relative(result_path.replace(previous_revision_directory, ''))
        dest_abs_path = os.path.join(revision_directory, final_rel_path)

        if os.path.isfile(dest_abs_path):
            manifest_data = self.manifest.get(final_rel_path)
            return [self._file_info(final_rel_path, manifest_data)]
        elif os.path.isdir(dest_abs_path):
            moved_files = list()
            moved_files.append(self.gen_file_info(final_rel_path))
            for root, dirs, files in os.walk(dest_abs_path):
                dirs.sort()
                rt = root.replace(revision_directory, '')
                rt = self.dataset.make_path_relative(rt)
                for d in dirs:
                    if d[-1] != os.path.sep:
                        d = d + '/'
                    moved_files.append(self.gen_file_info(os.path.join(rt, d)))
                for f in filter(lambda n: n != '.gitkeep', sorted(files)):
                    rel_path = os.path.join(rt, f)
                    manifest_data = self.manifest.get(rel_path)
                    moved_files.append(self._file_info(rel_path, manifest_data))
        else:
            raise ValueError("Destination path does not exist after move operation")

        logger.info(msg)
        return moved_files

    def create_directory(self, path: str) -> Dict[str, Any]:
        """Method to create an empty directory in a dataset

        Args:
            path: Relative path to the directory

        Returns:
            dict
        """
        relative_path = self.dataset.make_path_relative(path)
        new_directory_path = os.path.join(self.cache_mgr.cache_root, self.dataset_revision, relative_path)
        previous_revision = self.dataset_revision

        if os.path.exists(new_directory_path):
            raise ValueError(f"Directory already exists: `{relative_path}`")
        else:
            logger.info(f"Creating new empty directory in `{new_directory_path}`")

            if os.path.isdir(Path(new_directory_path).parent) is False:
                raise ValueError(f"Parent directory does not exist. Failed to create `{new_directory_path}` ")

            # create dir
            os.makedirs(new_directory_path)
            self.update()
            if relative_path not in self.manifest:
                raise ValueError("Failed to add directory to manifest")

            # Create detail record
            adr = ActivityDetailRecord(ActivityDetailType.DATASET, show=False, importance=0,
                                       action=ActivityAction.CREATE)

            msg = f"Created new empty directory `{relative_path}`"
            adr.add_value('text/markdown', msg)

            commit = self.dataset.git.commit(msg)

            # Create activity record
            ar = ActivityRecord(ActivityType.DATASET,
                                message=msg,
                                linked_commit=commit.hexsha,
                                show=True,
                                importance=255,
                                tags=['directory-create'])
            ar.add_detail_object(adr)

            # Store
            ars = ActivityStore(self.dataset)
            ars.create_activity_record(ar)

            # Relink after the commit
            self.link_revision()
            if os.path.isdir(os.path.join(self.cache_mgr.cache_root, previous_revision)):
                shutil.rmtree(os.path.join(self.cache_mgr.cache_root, previous_revision))

            return self.gen_file_info(relative_path)

    def link_revision(self) -> None:
        """Method to link all the objects in the cache to the current revision directory, so that all files are
        accessible with the correct file names.

        Note: This update the current revision in the hashing class

        Returns:
            None
        """
        current_revision = self.dataset_revision
        self.hasher.current_revision = current_revision

        revision_directory = os.path.join(self.cache_mgr.cache_root, current_revision)

        if not os.path.exists(revision_directory):
            os.makedirs(revision_directory)

        for f in self.manifest:
            hash_str = self.manifest[f].get('h')
            level1, level2 = self._get_object_subdirs(hash_str)

            target = os.path.join(revision_directory, f)
            if target[-1] == os.path.sep:
                # Create directory from manifest
                if not os.path.exists(target):
                    os.makedirs(target)
            else:
                # Link file
                source = os.path.join(self.cache_mgr.cache_root, 'objects', level1, level2, hash_str)

                target_dir = os.path.dirname(target)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                # Link if not already linked
                if not os.path.exists(target):
                    try:
                        if os.path.exists(source):
                            # Only try to link if the source object has been materialized
                            os.link(source, target)
                    except Exception as err:
                        logger.exception(err)
                        continue

        # Update fast hash
        self.hasher.fast_hash(list(self.manifest.keys()))

    def sweep_all_changes(self, upload: bool = False, extra_msg: str = None) -> None:
        """

        Args:
            upload:
            extra_msg:

        Returns:

        """
        def _item_type(key):
            if key[-1] == os.path.sep:
                return 'directory'
            else:
                return 'file'

        previous_revision = self.dataset_revision

        # Update manifest
        status = self.update()

        if len(status.deleted) > 0 or len(status.created) > 0 or len(status.modified) > 0:
            # commit changed manifest file
            self.dataset.git.add_all()
            self.dataset.git.commit("Commit changes to manifest file.")

            ar = ActivityRecord(ActivityType.DATASET,
                                message="msg is set below after detail record processing...",
                                show=True,
                                importance=255,
                                linked_commit=self.dataset.git.commit_hash,
                                tags=[])
            if upload:
                ar.tags.append('upload')

            for cnt, f in enumerate(status.created):
                adr = ActivityDetailRecord(ActivityDetailType.DATASET, show=False, importance=max(255 - cnt, 0),
                                           action=ActivityAction.CREATE)

                msg = f"Created new {_item_type(f)} `{f}`"
                adr.add_value('text/markdown', msg)
                ar.add_detail_object(adr)

            for cnt, f in enumerate(status.modified):
                adr = ActivityDetailRecord(ActivityDetailType.DATASET, show=False, importance=max(255 - cnt, 0),
                                           action=ActivityAction.EDIT)

                msg = f"Modified {_item_type(f)} `{f}`"
                adr.add_value('text/markdown', msg)
                ar.add_detail_object(adr)

            for cnt, f in enumerate(status.deleted):
                adr = ActivityDetailRecord(ActivityDetailType.DATASET, show=False, importance=max(255 - cnt, 0),
                                           action=ActivityAction.DELETE)

                msg = f"Deleted {_item_type(f)} `{f}`"
                adr.add_value('text/markdown', msg)
                ar.add_detail_object(adr)

            nmsg = f"{len(status.created)} new file(s). " if len(status.created) > 0 else ""
            mmsg = f"{len(status.modified)} modified file(s). " if len(status.modified) > 0 else ""
            dmsg = f"{len(status.deleted)} deleted file(s). " if len(status.deleted) > 0 else ""

            ar.message = f"{extra_msg if extra_msg else ''}" \
                         f"{'Uploaded ' if upload else ''}" \
                         f"{nmsg}{mmsg}{dmsg}"

            ars = ActivityStore(self.dataset)
            ars.create_activity_record(ar)

        # Re-link new revision, unlink old revision
        self.link_revision()
        if os.path.isdir(os.path.join(self.cache_mgr.cache_root, previous_revision)):
            shutil.rmtree(os.path.join(self.cache_mgr.cache_root, previous_revision))
