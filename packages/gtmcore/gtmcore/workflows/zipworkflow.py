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

from tempfile import TemporaryDirectory
from typing import Optional, Callable, List, cast

from gtmcore.exceptions import GigantumException
from gtmcore.configuration.utils import call_subprocess
from gtmcore.inventory.inventory import InventoryManager, Repository
from gtmcore.labbook import LabBook
from gtmcore.dataset import Dataset
from gtmcore.logging import LMLogger
from gtmcore.workflows import core

logger = LMLogger.get_logger()


class ZipWorkflowException(GigantumException):
    pass


class ZipExporter(object):
    """Provides project import from a zipfile, and export to a zip file."""

    @classmethod
    def _export_zip(cls, repo: Repository, export_directory: str,
                    config_file: Optional[str] = None, ) -> str:
        if not os.path.isdir(export_directory):
            os.makedirs(export_directory, exist_ok=True)

        core.sync_locally(repo)

        repo_dir, _ = repo.root_dir.rsplit(os.path.sep, 1)

        repo_zip_name = f'{repo.name}-' \
                      f'{repo.git.log()[0]["commit"][:6]}'
        zip_path = f'{repo_zip_name}.zip'
        exported_path = os.path.join(export_directory, zip_path)

        try:
            # zip data using subprocess - NOTE! Python zipfile library does not work correctly.
            call_subprocess(['zip', '-r', exported_path, os.path.basename(repo.root_dir)],
                            cwd=repo_dir, check=True)
            assert os.path.exists(exported_path)
            return exported_path
        except:
            try:
                os.remove(exported_path)
            except:
                pass
            raise

    @classmethod
    def export_labbook(cls, labbook_path: str, lb_export_directory: str) -> str:
        try:
            labbook = InventoryManager().load_labbook_from_directory(labbook_path)
            return cls._export_zip(labbook, lb_export_directory)
        except Exception as e:
            logger.error(e)
            raise ZipWorkflowException(e)

    @classmethod
    def export_dataset(cls, dataset_path: str, ds_export_directory: str) -> str:
        try:
            dataset = InventoryManager().load_dataset_from_directory(dataset_path)
            return cls._export_zip(dataset, ds_export_directory)
        except Exception as e:
            logger.error(e)
            raise ZipWorkflowException(e)

    @classmethod
    def _import_zip(cls, archive_path: str, username: str, owner: str,
                    fetch_method: Callable, put_method: Callable,
                    update_meta: Callable = lambda _ : None) -> Repository:

        if not os.path.isfile(archive_path):
            raise ValueError(f'Archive at {archive_path} is not a file or does not exist')

        if '.zip' not in archive_path and '.lbk' not in archive_path:
            raise ValueError(f'Archive at {archive_path} does not have .zip (or legacy .lbk) extension')

        statusmsg = f'Unzipping Repository Archive...'
        update_meta(statusmsg)

        # Unzip into a temporary directory and cleanup if fails
        with TemporaryDirectory() as temp_dir:
            call_subprocess(['unzip', archive_path, '-d', 'project'],
                            cwd=temp_dir, check=True)

            pdirs = os.listdir(os.path.join(temp_dir, 'project'))
            if len(pdirs) != 1:
                raise ValueError("Expected only one directory unzipped")
            unzipped_path = os.path.join(temp_dir, 'project', pdirs[0])

            repo = fetch_method(unzipped_path)
            statusmsg = f'{statusmsg}\nCreating workspace branch...'
            update_meta(statusmsg)

            # This makes sure the working directory is set properly.
            core.sync_locally(repo, username=username)

            if 'owner' in repo._data:
                repo._data['owner']['username'] = owner
            repo._save_gigantum_data()
            if not repo.is_repo_clean:
                repo.git.add('.gigantum/labbook.yaml')
                repo.git.commit(message="Updated owner in labbook.yaml")

            #if repo._data['owner']['username'] != owner:
            #    raise ValueError(f'Error importing LabBook {repo} - cannot set owner')

            # Also, remove any lingering remotes.
            # If it gets re-published, it will be to a new remote.
            if repo.has_remote:
                repo.git.remove_remote('origin')

            # Ignore execution bit changes (due to moving between windows/mac/linux)
            call_subprocess("git config core.fileMode false".split(),
                            cwd=repo.root_dir)

            repo = put_method(unzipped_path, username=username, owner=owner)

            statusmsg = f'{statusmsg}\nImport Complete'
            update_meta(statusmsg)

            return repo

    @classmethod
    def import_labbook(cls, archive_path: str, username: str, owner: str,
                       config_file: Optional[str] = None,
                       update_meta: Callable = lambda _ : None) -> LabBook:
        try:
            repo = cls._import_zip(archive_path, username, owner,
                                   fetch_method=InventoryManager(config_file).load_labbook_from_directory,
                                   put_method=InventoryManager(config_file).put_labbook,
                                   update_meta=update_meta)
            return cast(LabBook, repo)
        except Exception as e:
            logger.error(e)
            raise ZipWorkflowException(e)
        finally:
            if os.path.isfile(archive_path):
                os.remove(archive_path)

    @classmethod
    def import_dataset(cls, archive_path: str, username: str, owner: str,
                   config_file: Optional[str] = None,
                   update_meta: Callable = lambda _ : None) -> Dataset:
        try:
            repo = cls._import_zip(archive_path, username, owner,
                                   fetch_method=InventoryManager(config_file).load_dataset_from_directory,
                                   put_method=InventoryManager(config_file).put_dataset,
                                   update_meta=update_meta)
            return cast(Dataset, repo)
        except Exception as e:
            logger.error(e)
            raise ZipWorkflowException(e)
        finally:
            if os.path.isfile(archive_path) and archive_path != '/opt/awful-intersections-demo.lbk':
                os.remove(archive_path)
