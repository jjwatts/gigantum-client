import os

from tempfile import TemporaryDirectory
from typing import Optional, Callable, List, cast

from gtmcore.exceptions import GigantumException
from gtmcore.configuration.utils import call_subprocess
from gtmcore.inventory.inventory import InventoryManager, Repository
from gtmcore.labbook import LabBook
from gtmcore.dataset import Dataset
from gtmcore.logging import LMLogger
from gtmcore.workflows import gitworkflows_utils

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
            lb = cast(LabBook, repo)
            gitworkflows_utils.process_linked_datasets(lb, username)
            return lb
        except Exception as e:
            logger.error(e)
            raise ZipWorkflowException(e)
        finally:
            if os.path.isfile(archive_path) and archive_path != '/opt/my-first-project.zip':
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
            if os.path.isfile(archive_path) and archive_path != '/opt/my-first-project.zip':
                os.remove(archive_path)
