import pytest
import shutil

import os

from gtmcore.dataset.storage import get_storage_backend
from gtmcore.dataset.storage.local import LocalFilesystem
from gtmcore.dataset.manifest.manifest import Manifest
from gtmcore.fixtures.datasets import helper_compress_file, mock_dataset_with_cache_dir_local, USERNAME, \
    mock_enable_unmanaged_for_testing
from gtmcore.dataset.io import PullObject
from gtmcore.fixtures.datasets import mock_enable_unmanaged_for_testing


def helper_write_object(directory, object_id, contents):
    object_file = os.path.join(directory, object_id)
    with open(object_file, 'wt') as temp:
        temp.write(f'dummy data: {contents}')

    return object_file


@pytest.fixture()
def mock_dataset_with_local_dir(mock_dataset_with_cache_dir_local):
    """A mock when testing local filesystem backend and you need local contents to add to the dataset"""

    ds = mock_dataset_with_cache_dir_local[0]
    working_dir = mock_dataset_with_cache_dir_local[1]
    ds.backend.set_default_configuration(USERNAME, 'asdf', '1234')
    current_config = ds.backend_config
    current_config['Data Directory'] = "test_dir"
    ds.backend_config = current_config
    test_dir = os.path.join(working_dir, "local_data", "test_dir")

    os.makedirs(test_dir)

    helper_write_object(test_dir, "test1.txt", "temp contents 1")
    helper_write_object(test_dir, "test2.txt", "temp contents 2")
    os.makedirs(os.path.join(test_dir, 'subdir'))
    helper_write_object(test_dir, "subdir/test3.txt", "temp contents 3")

    yield mock_dataset_with_cache_dir_local
    shutil.rmtree(test_dir)


def updater(msg):
    print(msg)


class TestStorageBackendLocalFilesystem(object):
    def test_get_storage_backend(self, mock_dataset_with_cache_dir_local):
        sb = get_storage_backend("local_filesystem")

        assert isinstance(sb, LocalFilesystem)

    def test_backend_config(self, mock_dataset_with_cache_dir_local):
        ds = mock_dataset_with_cache_dir_local[0]
        assert isinstance(ds.backend, LocalFilesystem)

        assert ds.backend.is_configured is False

        missing = ds.backend.missing_configuration
        assert len(missing) == 4

        ds.backend.set_default_configuration('test', 'asdf', '1234')
        assert ds.backend.is_configured is False

        missing = ds.backend.missing_configuration
        assert len(missing) == 1
        assert missing[0]['parameter'] == "Data Directory"

        current_config = ds.backend_config
        current_config['Data Directory'] = "test_dir"
        ds.backend_config = current_config

        assert ds.backend.is_configured is True
        assert len(ds.backend.missing_configuration) == 0

    def test_backend_current_config(self, mock_dataset_with_cache_dir_local):
        ds = mock_dataset_with_cache_dir_local[0]
        assert isinstance(ds.backend, LocalFilesystem)

        assert ds.backend.is_configured is False

        current_config = ds.backend.safe_current_configuration
        assert len(current_config) == 1
        assert current_config[0]['value'] is None
        assert current_config[0]['parameter'] == "Data Directory"

        current_config = ds.backend_config
        current_config['Data Directory'] = "test_dir"
        ds.backend_config = current_config

        current_config = ds.backend.safe_current_configuration
        assert len(current_config) == 1
        assert current_config[0]['value'] == "test_dir"
        assert current_config[0]['parameter'] == "Data Directory"

    def test_confirm_configuration(self, mock_dataset_with_cache_dir_local):
        ds = mock_dataset_with_cache_dir_local[0]

        ds.backend.set_default_configuration('test', 'asdf', '1234')

        with pytest.raises(ValueError):
            ds.backend.confirm_configuration(ds)

        current_config = ds.backend_config
        current_config['Data Directory'] = "test_dir"
        ds.backend_config = current_config

        assert ds.backend.is_configured is True
        assert len(ds.backend.missing_configuration) == 0

        with pytest.raises(ValueError):
            ds.backend.confirm_configuration(ds)

        # Create test data dir
        os.makedirs(os.path.join(mock_dataset_with_cache_dir_local[1], "local_data", "test_dir"))

        assert ds.backend.confirm_configuration(ds) is None

    def test_prepare_pull_not_configured(self, mock_dataset_with_cache_dir_local):
        ds = mock_dataset_with_cache_dir_local[0]

        with pytest.raises(ValueError):
            ds.backend.prepare_pull(ds, [])

    def test_update_from_remote(self, mock_dataset_with_local_dir):
        ds = mock_dataset_with_local_dir[0]

        assert ds.backend.can_update_from_remote() is True

        m = Manifest(ds, 'tester')
        assert len(m.manifest.keys()) == 0

        ds.backend.update_from_remote(ds, updater)

        m = Manifest(ds, 'tester')
        assert len(m.manifest.keys()) == 4
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test1.txt'))
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test2.txt'))
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'subdir', 'test3.txt'))

    def test_update_from_local(self, mock_dataset_with_local_dir):
        ds = mock_dataset_with_local_dir[0]

        assert ds.backend.can_update_from_remote() is True

        m = Manifest(ds, 'tester')
        assert len(m.manifest.keys()) == 0

        ds.backend.update_from_remote(ds, updater)

        m = Manifest(ds, 'tester')
        assert len(m.manifest.keys()) == 4
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test1.txt'))
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test2.txt'))
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'subdir', 'test3.txt'))

        modified_items = ds.backend.verify_contents(ds, updater)
        assert len(modified_items) == 0

        test_dir = os.path.join(mock_dataset_with_local_dir[1], "local_data", "test_dir")
        with open(os.path.join(test_dir, 'test1.txt'), 'wt') as tf:
            tf.write("This file got changed in the filesystem")

        modified_items = ds.backend.verify_contents(ds, updater)
        assert len(modified_items) == 1
        assert 'test1.txt' in modified_items

        ds.backend.update_from_local(ds, updater, verify_contents=True)
        assert len(m.manifest.keys()) == 4
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test1.txt'))
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test2.txt'))
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'subdir', 'test3.txt'))

        modified_items = ds.backend.verify_contents(ds, updater)
        assert len(modified_items) == 0

        with open(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test1.txt'), 'rt') as tf:
            assert tf.read() == "This file got changed in the filesystem"

    def test_pull(self, mock_dataset_with_local_dir):
        def chunk_update_callback(completed_bytes: int):
            """Method to update the job's metadata and provide feedback to the UI"""
            assert type(completed_bytes) == int
            assert completed_bytes > 0

        ds = mock_dataset_with_local_dir[0]
        m = Manifest(ds, 'tester')
        assert len(m.manifest.keys()) == 0
        ds.backend.update_from_remote(ds, updater)
        m = Manifest(ds, 'tester')

        # Remove revision dir
        shutil.rmtree(os.path.join(m.cache_mgr.cache_root, m.dataset_revision))

        keys = ['test1.txt', 'test2.txt', 'subdir/test3.txt']
        pull_objects = list()
        for key in keys:
            pull_objects.append(PullObject(object_path=m.dataset_to_object_path(key),
                                           revision=m.dataset_revision,
                                           dataset_path=key))
            # Remove objects
            os.remove(m.dataset_to_object_path(key))
            
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test1.txt')) is False
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test2.txt')) is False
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'subdir', 'test3.txt')) is False
        
        for key in keys:
            assert os.path.isfile(m.dataset_to_object_path(key)) is False

        # Pull 1 File
        ds.backend.pull_objects(ds, [pull_objects[0]], chunk_update_callback)
        assert os.path.isdir(os.path.join(m.cache_mgr.cache_root, m.dataset_revision))
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test1.txt')) is True
        assert os.path.isfile(m.dataset_to_object_path('test1.txt')) is True

        # Pull all Files
        ds.backend.pull_objects(ds, pull_objects, chunk_update_callback)
        assert os.path.isdir(os.path.join(m.cache_mgr.cache_root, m.dataset_revision))
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test1.txt')) is True
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test2.txt')) is True
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'subdir', 'test3.txt')) is True
        for key in keys:
            assert os.path.isfile(m.dataset_to_object_path(key)) is True
