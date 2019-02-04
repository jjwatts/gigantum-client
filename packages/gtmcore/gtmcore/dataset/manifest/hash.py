from hashlib import blake2b
import asyncio
from typing import List, Tuple
import pickle
import os
from collections import namedtuple
from gtmcore.dataset.manifest.eventloop import get_event_loop


HashResult = namedtuple('HashResult', ['hash', 'fast_hash', 'filename'])


class SmartHash(object):
    """Class to handle file hashing that is operationally optimized for Gigantum"""

    def __init__(self, root_dir: str, file_cache_root: str, current_revision: str) -> None:
        self.root_dir = root_dir
        self.file_cache_root = file_cache_root
        self.current_revision = current_revision

        self.fast_hash_data = self._load_fast_hash_file()

        self.hashing_block_size = 65536

    @property
    def fast_hash_file(self):
        return os.path.join(self.file_cache_root, self.current_revision, ".smarthash")

    def _load_fast_hash_file(self) -> dict:
        """Method to load the cached fast hash file

        Returns:
            dict
        """
        if os.path.exists(self.fast_hash_file):
            with open(self.fast_hash_file, 'rb') as mf:
                return pickle.load(mf)
        else:
            return dict()

    def _save_fast_hash_file(self) -> None:
        """Method to save the cached fast hash file

        Returns:
            dict
        """
        with open(self.fast_hash_file, 'wb') as mf:
            pickle.dump(self.fast_hash_data, mf, pickle.HIGHEST_PROTOCOL)

    def get_abs_path(self, relative_path: str) -> str:
        """Method to generate the absolute path to the file

        Args:
            relative_path:

        Returns:

        """
        if relative_path[0] == '/':
            relative_path = relative_path[1:]

        return os.path.join(self.file_cache_root, self.current_revision, relative_path)

    def is_cached(self, path) -> bool:
        """

        Args:
            path:

        Returns:

        """
        return path in self.fast_hash_data

    def has_changed_fast(self, path) -> bool:
        """

        Args:
            path:

        Returns:

        """
        return self.fast_hash([path], save=False)[0].fast_hash != self.fast_hash_data.get(path)

    def get_deleted_files(self, file_list: List[str]) -> list:
        """

        Args:
            file_list:

        Returns:

        """
        return sorted(list(set(self.fast_hash_data.keys()).difference(file_list)))

    def delete_hashes(self, file_list: List[str]) -> None:
        """

        Args:
            file_list:

        Returns:

        """
        for f in file_list:
            del self.fast_hash_data[f]

        self._save_fast_hash_file()

    async def async_stat(self, path):
        try:
            result = os.stat(self.get_abs_path(path))
        except FileNotFoundError:
            result = None
        return result

    def fast_hash(self, path_list: list, save: bool = True) -> List[HashResult]:
        """

        Note, the delimiter `||` is used as it's unlikely to be in a path. Hash structure:

        relative file path || size in bytes || mtime || ctime

        Args:
            path_list:
            save:

        Returns:

        """
        fast_hash_result = list()
        if len(path_list) > 0:
            loop = get_event_loop()
            tasks = [asyncio.ensure_future(self.async_stat(path)) for path in path_list]
            loop.run_until_complete(asyncio.ensure_future(asyncio.wait(tasks)))

            for p, r in zip(path_list, tasks):
                stat_data = r.result()
                if stat_data:
                    hash_val = f"{p}||{stat_data[6]}||{stat_data[8]}||{stat_data[9]}"
                    fast_hash_result.append(HashResult(filename=p,
                                                       hash=None,
                                                       fast_hash=hash_val))
                    if save:
                        self.fast_hash_data[p] = hash_val

            if save:
                self._save_fast_hash_file()

        return fast_hash_result

    @staticmethod
    async def read_block(file_handle, blocksize):
        return file_handle.read(blocksize)

    async def async_hash_file(self, path: str, blocksize: int = 4096):
        """Method to compute

        Args:
            path:
            blocksize:

        Returns:

        """
        h = blake2b()

        abs_path = self.get_abs_path(path)
        if os.path.isfile(abs_path):
            with open(abs_path, 'rb') as fh:
                file_buffer = await self.read_block(fh, blocksize)
                while len(file_buffer) > 0:
                    h.update(file_buffer)
                    file_buffer = await self.read_block(fh, blocksize)
        else:
            h.update(abs_path.encode('utf-8'))

        return h.hexdigest()

    def hash(self, path_list: list) -> List[HashResult]:
        """Method to compute the hash of a file

        Args:
            path_list:

        Returns:
            Tuple
        """
        loop = get_event_loop()
        tasks = [asyncio.ensure_future(self.async_hash_file(path, self.hashing_block_size)) for path in path_list]
        loop.run_until_complete(asyncio.ensure_future(asyncio.gather(*tasks)))

        fast_hash_result = self.fast_hash(path_list)

        result = list()
        for path, hash_result, fast_result in zip(path_list, tasks, fast_hash_result):
            task_result = hash_result.result()
            assert fast_result.filename == path, "Task processing out of order. Failed to hash."
            result.append(HashResult(filename=path,
                                     hash=task_result,
                                     fast_hash=fast_result.fast_hash))

        return result
