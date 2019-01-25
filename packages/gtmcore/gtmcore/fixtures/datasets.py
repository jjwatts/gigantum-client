import pytest
import os
import shutil
from mock import patch

from gtmcore.configuration import Configuration
from gtmcore.fixtures.fixtures import _create_temp_work_dir
from gtmcore.inventory.inventory import InventoryManager
from gtmcore.dataset import Manifest

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


def helper_append_file(cache_dir, revision, rel_path, content):
    if not os.path.exists(os.path.join(cache_dir, revision)):
        os.makedirs(os.path.join(cache_dir, revision))
    with open(os.path.join(cache_dir, revision, rel_path), 'at') as fh:
        fh.write(content)
