import os
from typing import List, Callable
import subprocess
import glob
from natsort import natsorted
from operator import attrgetter

from gtmcore.dataset.dataset import Dataset
from gtmcore.dataset.manifest import Manifest
from gtmcore.dataset.io import PushObject, PushResult, PullResult, PullObject

from gtmcore.logging import LMLogger

logger = LMLogger.get_logger()


class IOManager(object):
    """Class to manage file IO with remote storage backends and glue everything together"""

    def __init__(self, dataset: Dataset, manifest: Manifest) -> None:
        self.dataset = dataset
        self.manifest = manifest

        self.push_dir = os.path.join(self.manifest.cache_mgr.cache_root, 'objects', '.push')

        # Property to keep status state if needed when appending messages
        self._status_msg = ""

    def _commit_in_branch(self, commit_hash: str) -> bool:
        """Method to check if a commit is in the current branch, ignoring the last commit.

        This is used for the purpose of only pushing objects that are part of the current branch. We ignore the last
        commit because objects to push are stored in a file named with the revision at which the files were written.
        This is different from the revision that contains the files (after written and untracked, changes are
        committed and then an activity record is created with another commit). The last commit can be used in a
        different branch where objects were written, but can't contain any objects to push in the current branch.

        Args:
            commit_hash(str): Commit hash to check if in branch

        Returns:
            bool
        """
        try:
            subprocess.run(['git', 'merge-base', '--is-ancestor', commit_hash, 'HEAD~1'], check=True,
                           cwd=self.dataset.root_dir)
            return True
        except subprocess.CalledProcessError:
            return False

    def objects_to_push(self, remove_duplicates: bool = False) -> List[PushObject]:
        """Return a list of named tuples of all objects that need to be pushed

        Returns:
            List[namedtuple]
        """
        objects = list()
        if os.path.exists(self.push_dir):
            push_files = [f for f in os.listdir(self.push_dir) if os.path.isfile(os.path.join(self.push_dir, f))]

            if push_files:
                object_ids: List[str] = list()
                for pf in push_files:
                    if os.path.basename(pf) == '.DS_Store':
                        continue

                    if not self._commit_in_branch(pf):
                        continue

                    with open(os.path.join(self.push_dir, pf), 'rt') as pfh:
                        lines = pfh.readlines()
                        lines = sorted(lines)
                        for line in lines:
                            line = line.strip()
                            dataset_path, object_path = line.split(',')
                            _, object_id = object_path.rsplit('/', 1)

                            # Handle de-duplicating objects if the backend supports it
                            if remove_duplicates is True:
                                if object_id in object_ids:
                                    continue

                                object_ids.append(object_id)

                            objects.append(PushObject(dataset_path=dataset_path, object_path=object_path, revision=pf))

            objects = natsorted(objects, key=attrgetter('dataset_path'))

        return objects

    def num_objects_to_push(self, remove_duplicates: bool = False) -> int:
        """Helper to get the total number of objects to push

        Returns:
            int
        """
        return len(self.objects_to_push(remove_duplicates))

    def _log_updater(self, message: str, append: bool = False) -> None:
        """A status updater method that simply logs. Used by default if a custom status updater isn't provided in some
        methods that are expected to run in the background.

        Args:
            message(str): Message to update

        Returns:
            None
        """
        if append:
            self._status_msg = f"{self._status_msg}\n{message}"
        else:
            self._status_msg = message
        logger.info(self._status_msg)

    def push_objects(self, status_update_fn: Callable = None) -> PushResult:
        """Method to push all available objects

        This method hands most of the work over to the StorageBackend implementation for the dataset. It is expected
        that the StorageBackend will return a PushResult named tuple so the user can be properly notified and
        everything stays consistent.

        Returns:
            IOResult
        """
        if not status_update_fn:
            status_update_fn = self._log_updater

        objs: List[PushObject] = self.objects_to_push(remove_duplicates=self.dataset.backend.client_should_dedup_on_push)

        try:
            self.dataset.backend.prepare_push(self.dataset, objs, status_update_fn)
            result = self.dataset.backend.push_objects(self.dataset, objs, status_update_fn)
            logger.warning(result)
            self.dataset.backend.finalize_push(self.dataset, status_update_fn)
        except Exception as err:
            logger.exception(err)
            raise

        # Remove push files that have been processed
        files = glob.glob(f'{self.push_dir}/*')
        for f in files:
            os.remove(f)

        # Collect objects that still need to be pushed due to errors and write push files
        for failed_push in result.failure:
            self.manifest.queue_to_push(failed_push.object_path, failed_push.dataset_path, failed_push.revision)

        return result

    def _gen_pull_objects(self, keys: List[str]) -> List[PullObject]:
        """

        Args:
            keys:

        Returns:

        """
        result = list()
        revision = self.manifest.dataset_revision
        for key in keys:
            data = self.manifest.dataset_to_object_path(key)
            result.append(PullObject(object_path=data, revision=revision, dataset_path=key))

        return result

    def pull_objects(self, keys: List[str], status_update_fn: Callable = None) -> PullResult:
        """Method to pull a single object

        This method hands most of the work over to the StorageBackend implementation for the dataset. It is expected
        that the StorageBackend will return a PushResult named tuple so the user can be properly notified and
        everything stays consistent.

        Returns:
            PullResult
        """
        if not status_update_fn:
            status_update_fn = self._log_updater

        objs: List[PullObject] = self._gen_pull_objects(keys)

        # Pull the object
        self.dataset.backend.prepare_pull(self.dataset, objs, status_update_fn)
        result = self.dataset.backend.pull_objects(self.dataset, objs, status_update_fn)
        self.dataset.backend.finalize_pull(self.dataset, status_update_fn)

        # Relink the revision
        self.manifest.link_revision()

        # Return pull result
        return result

    def pull_all(self, status_update_fn: Callable = None) -> PullResult:
        """Helper to pull every object in the dataset, ignoring files that already exist and linking files if needed

        Args:
            status_update_fn: Callable to provide status during pull

        Returns:
            PullResult
        """
        keys_to_pull = list()
        for key in self.manifest.manifest:
            # If dir, skip
            if key[-1] == os.path.sep:
                continue

            # If object is linked to the revision already, skip
            revision_path = os.path.join(self.manifest.cache_mgr.current_revision_dir, key)
            if os.path.exists(revision_path):
                continue

            # Check if file exists in object cache and simply needs to be linked
            obj_path = self.manifest.dataset_to_object_path(key)
            if os.path.isfile(obj_path):
                os.link(obj_path, revision_path)
                continue

            # Queue for downloading
            keys_to_pull.append(key)

        if keys_to_pull:
            return self.pull_objects(keys_to_pull, status_update_fn)
        else:
            return PullResult(success=[], failure=[], message="Dataset already downloaded.")
