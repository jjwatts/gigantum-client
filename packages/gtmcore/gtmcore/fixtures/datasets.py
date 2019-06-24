import pytest
import os
import shutil
from mock import patch

import boto3
from moto import mock_s3

import snappy
from pkg_resources import resource_filename
import tempfile

from gtmcore.configuration import Configuration
from gtmcore.fixtures.fixtures import _create_temp_work_dir, mock_config_file_background_tests
from gtmcore.inventory.inventory import InventoryManager
from gtmcore.dataset import Manifest
from gtmcore.dispatcher.jobs import import_dataset_from_zip
import gtmcore

USERNAME = 'tester'


@pytest.fixture(scope='session')
def mock_enable_unmanaged_for_testing():
    """A pytest fixture that enables unmanaged datasets for testing. Until unmanaged datasets are completed, they
    are disabled and dormant. We want to keep testing them and carry the code forward, but don't want them to be
    used yet.

    When running via a normal build, only "gigantum_object_v1" is available. To enable the others, you need to edit
    gtmcore.dataset.storage.SUPPORTED_STORAGE_BACKENDS in gtmcore.dataset.storage.__init__.py

    When this is done (unmanaged datasets are being re-activated) you should remove this fixture everywhere.
    """
    gtmcore.dataset.storage.SUPPORTED_STORAGE_BACKENDS = {
        "gigantum_object_v1": ("gtmcore.dataset.storage.gigantum", "GigantumObjectStore"),
        "local_filesystem": ("gtmcore.dataset.storage.local", "LocalFilesystem"),
        "public_s3_bucket": ("gtmcore.dataset.storage.s3", "PublicS3Bucket")}

    yield


@pytest.fixture()
def mock_dataset_with_cache_dir():
    """A pytest fixture that creates a dataset in a temp working dir. Deletes directory after test"""
    conf_file, working_dir = _create_temp_work_dir()
    with patch.object(Configuration, 'find_default_config', lambda self: conf_file):
        im = InventoryManager(conf_file)
        ds = im.create_dataset(USERNAME, USERNAME, 'dataset-1', description="my dataset 1",
                               storage_type="gigantum_object_v1")

        yield ds, working_dir, ds.git.repo.head.commit.hexsha
        shutil.rmtree(working_dir)


@pytest.fixture()
def mock_config_class(mock_enable_unmanaged_for_testing):
    """A pytest fixture that creates a temp working dir, mocks the Configuration class to resolve the mocked config"""
    conf_file, working_dir = _create_temp_work_dir()
    with patch.object(Configuration, 'find_default_config', lambda self: conf_file):
        im = InventoryManager(conf_file)
        yield im, conf_file, working_dir
        shutil.rmtree(working_dir)


@pytest.fixture()
def mock_dataset_with_cache_dir_local(mock_enable_unmanaged_for_testing):
    """A pytest fixture that creates a dataset in a temp working dir. Deletes directory after test"""
    conf_file, working_dir = _create_temp_work_dir()
    with patch.object(Configuration, 'find_default_config', lambda self: conf_file):
        im = InventoryManager(conf_file)
        ds = im.create_dataset(USERNAME, USERNAME, 'dataset-1', description="my dataset 1",
                               storage_type="local_filesystem")

        yield ds, working_dir, ds.git.repo.head.commit.hexsha

        shutil.rmtree(working_dir)


@pytest.fixture()
def mock_dataset_with_manifest(mock_dataset_with_cache_dir):
    """A pytest fixture that creates a dataset in a temp working dir and provides a cache manager"""
    m = Manifest(mock_dataset_with_cache_dir[0], USERNAME)
    m.link_revision()

    # yield dataset, manifest, working_dir
    yield mock_dataset_with_cache_dir[0], m, mock_dataset_with_cache_dir[1]


@pytest.fixture()
def mock_dataset_with_manifest_bg_tests(mock_config_file_background_tests):
    """A pytest fixture that creates a dataset in a temp working dir and provides a cache manager, configured with
    additional overrides for dataset tests running in the background"""
    conf_file, working_dir = mock_config_file_background_tests
    with patch.object(Configuration, 'find_default_config', lambda self: conf_file):
        im = InventoryManager(conf_file)
        ds = im.create_dataset(USERNAME,  USERNAME, 'dataset-1', description="my dataset 1",
                               storage_type="gigantum_object_v1")

        m = Manifest(ds, USERNAME)
        m.link_revision()

        # yield dataset, manifest, working_dir
        yield ds, m, working_dir


@pytest.fixture()
def mock_legacy_dataset(mock_dataset_with_cache_dir):
    """A pytest fixture that imports the legacy dataset"""
    archive_path = os.path.join(resource_filename('gtmcore.dataset.tests', 'data'), 'test-legacy-dataset.zip')
    temp_path = os.path.join(tempfile.gettempdir(), 'test-legacy-dataset.zip')
    shutil.copyfile(archive_path, temp_path)
    conf_file = mock_dataset_with_cache_dir[0].client_config.config_file
    import_dataset_from_zip(archive_path=temp_path, username=USERNAME,
                            owner=USERNAME, config_file=conf_file)

    im = InventoryManager()
    ds = im.load_dataset(USERNAME, USERNAME, 'test-legacy-dataset')
    m = Manifest(ds, USERNAME)

    # yield dataset, manifest, working_dir
    yield ds, m, mock_dataset_with_cache_dir[1]


@pytest.fixture()
def mock_public_bucket():
    """A pytest fixture that creates a temp working dir, mocks the Configuration class to resolve the mocked config"""
    os.environ['AWS_ACCESS_KEY_ID'] = "fake-access-key"
    os.environ['AWS_SECRET_ACCESS_KEY'] = "fake-secret-key"

    with mock_s3():
        boto3.setup_default_session()
        bucket = "gigantum-test-bucket"
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=bucket)
        conn.meta.client.put_bucket_acl(ACL='public-read', Bucket=bucket)

        with tempfile.NamedTemporaryFile('wt') as tf:
            tf.write("asdf" * 1000)
            tf.seek(0)
            conn.meta.client.upload_file(tf.name, bucket, 'test-file-1.bin')
            conn.meta.client.upload_file(tf.name, bucket, 'test-file-2.bin')

        with tempfile.NamedTemporaryFile('wt') as tf:
            tf.write("1234" * 100)
            tf.seek(0)
            conn.meta.client.upload_file(tf.name, bucket, 'metadata/test-file-3.bin')
            conn.meta.client.upload_file(tf.name, bucket, 'metadata/test-file-4.bin')

        with tempfile.NamedTemporaryFile('wt') as tf:
            tf.write("5656" * 100)
            tf.seek(0)
            conn.meta.client.upload_file(tf.name, bucket, 'metadata/sub/test-file-5.bin')

        yield bucket


def helper_append_file(cache_dir, revision, rel_path, content):
    if not os.path.exists(os.path.join(cache_dir, revision)):
        os.makedirs(os.path.join(cache_dir, revision))
    with open(os.path.join(cache_dir, revision, rel_path), 'at') as fh:
        fh.write(content)


def helper_write_big_file(cache_dir, revision, rel_path, content):
    if not os.path.exists(os.path.join(cache_dir, revision)):
        os.makedirs(os.path.join(cache_dir, revision))
    with open(os.path.join(cache_dir, revision, rel_path), 'wt') as fh:
        fh.write(content * 250000000)
        fh.write(content * 250000000)
        fh.write(content * 250000000)
        fh.write(content * 250000000)


def helper_compress_file(source, destination):
    with open(source, "rb") as src_file:
        with open(destination, mode="wb") as compressed_file:
            snappy.stream_compress(src_file, compressed_file)
    os.remove(source)
