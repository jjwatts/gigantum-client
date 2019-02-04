from hashlib import blake2b
import asyncio
import aiofiles

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
            file_info = [os.stat(self.get_abs_path(x)) for x in path_list]

            for path, info in zip(path_list, file_info):
                hash_val = f"{path}||{info.st_size}||{info.st_mtime}||{info.st_ctime}"
                fast_hash_result.append(HashResult(filename=path,
                                                   hash=None,
                                                   fast_hash=hash_val))
                if save:
                    self.fast_hash_data[path] = hash_val

            if save:
                self._save_fast_hash_file()

        return fast_hash_result

    async def compute_file_hash(self, path: str, blocksize: int = 4096) -> str:
        """Method to compute the black2b hash for the provided file

        Args:
            path: Relative path to the file
            blocksize: Blocksize to use when reading the file and computing the hash

        Returns:
            str
        """
        h = blake2b()

        abs_path = self.get_abs_path(path)
        if os.path.isfile(abs_path):
            async with aiofiles.open(abs_path, 'rb') as fh:
                chunk = await fh.read(blocksize)
                while chunk:
                    h.update(chunk)
                    chunk = await fh.read(blocksize)
        else:
            # If a directory, just hash the path as an alternative
            h.update(abs_path.encode('utf-8'))

        return h.hexdigest()

    async def hash(self, path_list: List[str]) -> List[HashResult]:
        """Method to compute the hash of a file

        Args:
            path_list:

        Returns:
            Tuple
        """
        hash_result_list: List[str] = [await self.compute_file_hash(path, self.hashing_block_size) for path in path_list]

        fast_hash_result_list = self.fast_hash(path_list)

        result = list()
        for hash_result, fast_hash_result in zip(hash_result_list, fast_hash_result_list):
            result.append(HashResult(filename=fast_hash_result.filename,
                                     hash=hash_result,
                                     fast_hash=fast_hash_result.fast_hash))

        return result
