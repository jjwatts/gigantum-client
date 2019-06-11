import pytest
import os
import shutil
from mock import patch
import snappy
from pkg_resources import resource_filename
import tempfile

from gtmcore.configuration import Configuration
from gtmcore.fixtures.fixtures import _create_temp_work_dir
from gtmcore.inventory.inventory import InventoryManager
from gtmcore.dataset import Manifest
from gtmcore.dispatcher.jobs import import_dataset_from_zip

USERNAME = 'tester'


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
def mock_dataset_with_manifest(mock_dataset_with_cache_dir):
    """A pytest fixture that creates a dataset in a temp working dir and provides a cache manager"""
    m = Manifest(mock_dataset_with_cache_dir[0], USERNAME)
    m.link_revision()

    # yield dataset, manifest, working_dir
    yield mock_dataset_with_cache_dir[0], m, mock_dataset_with_cache_dir[1]


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
