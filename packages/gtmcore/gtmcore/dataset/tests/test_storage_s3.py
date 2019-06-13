import pytest
import shutil

import os
import tempfile
import boto3

from gtmcore.dataset.storage import get_storage_backend
from gtmcore.dataset.storage.s3 import PublicS3Bucket
from gtmcore.dataset.manifest.manifest import Manifest
from gtmcore.fixtures.datasets import helper_compress_file, mock_config_class, mock_public_bucket, \
    mock_enable_unmanaged_for_testing,  USERNAME
from gtmcore.dataset.io import PullObject


def helper_write_object(directory, object_id, contents):
    object_file = os.path.join(directory, object_id)
    with open(object_file, 'wt') as temp:
        temp.write(f'dummy data: {contents}')

    return object_file


def updater(msg):
    print(msg)


class TestStorageBackendS3PublicBuckets(object):
    def test_get_storage_backend(self, mock_config_class):
        sb = get_storage_backend("public_s3_bucket")

        assert isinstance(sb, PublicS3Bucket)

    def test_backend_config(self, mock_config_class):
        im = mock_config_class[0]
        ds = im.create_dataset(USERNAME, USERNAME, 'dataset-1', description="my dataset 1",
                               storage_type="public_s3_bucket")
        assert isinstance(ds.backend, PublicS3Bucket)

        assert ds.backend.is_configured is False

        missing = ds.backend.missing_configuration
        assert len(missing) == 5

        ds.backend.set_default_configuration('test', 'asdf', '1234')
        assert ds.backend.is_configured is False

        missing = ds.backend.missing_configuration
        assert len(missing) == 2
        assert missing[0]['parameter'] == "Bucket Name"
        assert missing[1]['parameter'] == "Prefix"

        current_config = ds.backend_config
        current_config['Bucket Name'] = "gigantum"
        current_config['Prefix'] = "desktop"
        ds.backend_config = current_config

        assert ds.backend.is_configured is True
        assert len(ds.backend.missing_configuration) == 0

    def test_confirm_configuration(self, mock_config_class, mock_public_bucket):
        im = mock_config_class[0]
        ds = im.create_dataset(USERNAME, USERNAME, 'dataset-1', description="my dataset 1",
                               storage_type="public_s3_bucket")

        ds.backend.set_default_configuration('test', 'asdf', '1234')

        with pytest.raises(ValueError):
            ds.backend.confirm_configuration(ds, updater)

        current_config = ds.backend_config
        current_config['Bucket Name'] = "gigantum-not-a-bucket"
        current_config['Prefix'] = "my-prefix"
        ds.backend_config = current_config

        assert ds.backend.is_configured is True
        assert len(ds.backend.missing_configuration) == 0

        with pytest.raises(ValueError):
            ds.backend.confirm_configuration(ds, updater)

        # use mocked bucket
        current_config = ds.backend_config
        current_config['Bucket Name'] = mock_public_bucket
        current_config['Prefix'] = ""
        ds.backend_config = current_config

        confirm_msg = ds.backend.confirm_configuration(ds, updater)

        assert "Creating this dataset will download 5 files" in confirm_msg

        # use mocked bucket with prefix
        current_config = ds.backend_config
        current_config['Bucket Name'] = mock_public_bucket
        current_config['Prefix'] = "metadata"
        ds.backend_config = current_config

        confirm_msg = ds.backend.confirm_configuration(ds, updater)

        assert "Creating this dataset will download 3 files" in confirm_msg

    def test_prepare_pull_not_configured(self, mock_config_class):
        im = mock_config_class[0]
        ds = im.create_dataset(USERNAME, USERNAME, 'dataset-1', description="my dataset 1",
                               storage_type="public_s3_bucket")

        with pytest.raises(ValueError):
            ds.backend.prepare_pull(ds, [], updater)

    def test_update_from_remote(self, mock_config_class, mock_public_bucket):
        im = mock_config_class[0]
        ds = im.create_dataset(USERNAME, USERNAME, 'dataset-1', description="my dataset 1",
                               storage_type="public_s3_bucket")
        ds.backend.set_default_configuration(USERNAME, 'fakebearertoken', 'fakeidtoken')

        assert ds.backend.can_update_from_remote() is True

        m = Manifest(ds, USERNAME)
        assert len(m.manifest.keys()) == 0

        # Configure backend completely
        current_config = ds.backend_config
        current_config['Bucket Name'] = mock_public_bucket
        current_config['Prefix'] = ""
        ds.backend_config = current_config

        # Trigger update
        ds.backend.update_from_remote(ds, updater)

        m = Manifest(ds, USERNAME)
        assert len(m.manifest.keys()) == 7
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test-file-1.bin'))
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test-file-2.bin'))
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'metadata/test-file-3.bin'))
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'metadata/test-file-4.bin'))
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'metadata/sub/test-file-5.bin'))

        with open(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test-file-1.bin'), 'rt') as tf:
            data = tf.read()
            assert data[0:4] == 'asdf'

        with open(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'metadata/test-file-4.bin'), 'rt') as tf:
            data = tf.read()
            assert data[0:4] == '1234'

    def test_update_from_remote_backend_change(self, mock_config_class, mock_public_bucket):
        im = mock_config_class[0]
        ds = im.create_dataset(USERNAME, USERNAME, 'dataset-1', description="my dataset 1",
                               storage_type="public_s3_bucket")
        ds.backend.set_default_configuration(USERNAME, 'fakebearertoken', 'fakeidtoken')

        assert ds.backend.can_update_from_remote() is True

        m = Manifest(ds, USERNAME)
        assert len(m.manifest.keys()) == 0

        # Configure backend completely
        current_config = ds.backend_config
        current_config['Bucket Name'] = mock_public_bucket
        current_config['Prefix'] = ""
        ds.backend_config = current_config

        # Trigger update
        ds.backend.update_from_remote(ds, updater)

        m = Manifest(ds, USERNAME)
        assert len(m.manifest.keys()) == 7

        modified_items = ds.backend.verify_contents(ds, updater)
        assert len(modified_items) == 0

        with tempfile.NamedTemporaryFile('wt') as tf:
            conn = boto3.resource('s3', region_name='us-east-1')
            tf.write("This file has been updated!")
            tf.seek(0)
            conn.meta.client.upload_file(tf.name, mock_public_bucket, 'test-file-1.bin')

        ds.backend.update_from_remote(ds, updater)
        assert len(m.manifest.keys()) == 7

        modified_items = ds.backend.verify_contents(ds, updater)
        assert len(modified_items) == 0

        with open(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test-file-1.bin'), 'rt') as tf:
            assert tf.read() == "This file has been updated!"

    def test_pull(self, mock_config_class, mock_public_bucket):
        im = mock_config_class[0]
        ds = im.create_dataset(USERNAME, USERNAME, 'dataset-1', description="my dataset 1",
                               storage_type="public_s3_bucket")
        ds.backend.set_default_configuration(USERNAME, 'fakebearertoken', 'fakeidtoken')

        # Configure backend completely
        current_config = ds.backend_config
        current_config['Bucket Name'] = mock_public_bucket
        current_config['Prefix'] = ""
        ds.backend_config = current_config

        ds.backend.update_from_remote(ds, updater)
        m = Manifest(ds, 'tester')

        # Remove revision dir and objects from cache
        shutil.rmtree(os.path.join(m.cache_mgr.cache_root, m.dataset_revision))

        keys = ['test-file-1.bin', 'metadata/test-file-3.bin', 'metadata/sub/test-file-5.bin']
        pull_objects = list()
        for key in keys:
            pull_objects.append(PullObject(object_path=m.dataset_to_object_path(key),
                                           revision=m.dataset_revision,
                                           dataset_path=key))
            # Remove objects
            os.remove(m.dataset_to_object_path(key))

        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test-file-1.bin')) is False
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root,
                                           m.dataset_revision, 'metadata', 'test-file-3.bin')) is False
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision,
                                           'metadata', 'sub', 'test-file-5.bin')) is False
        
        for key in keys:
            assert os.path.isfile(m.dataset_to_object_path(key)) is False

        # Pull 1 File (duplicate contents so 2 files show up)
        ds.backend.pull_objects(ds, [pull_objects[0]], updater)
        assert os.path.isdir(os.path.join(m.cache_mgr.cache_root, m.dataset_revision))
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test-file-1.bin')) is True
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test-file-2.bin')) is True
        assert os.path.isfile(m.dataset_to_object_path('test-file-1.bin')) is True
        assert os.path.isfile(m.dataset_to_object_path('test-file-2.bin')) is True

        # Pull all Files
        ds.backend.pull_objects(ds, pull_objects, updater)
        assert os.path.isdir(os.path.join(m.cache_mgr.cache_root, m.dataset_revision))
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test-file-1.bin')) is True
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, 'test-file-2.bin')) is True
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root,
                                           m.dataset_revision, 'metadata', 'test-file-3.bin')) is True
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root,
                                           m.dataset_revision, 'metadata', 'test-file-4.bin')) is True
        assert os.path.isfile(os.path.join(m.cache_mgr.cache_root, m.dataset_revision,
                                           'metadata', 'sub', 'test-file-5.bin')) is True
        for key in keys:
            assert os.path.isfile(m.dataset_to_object_path(key)) is True
