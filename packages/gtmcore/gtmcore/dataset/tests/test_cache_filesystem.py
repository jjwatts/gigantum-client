import pytest
import os

from gtmcore.fixtures.datasets import mock_dataset_with_cache_dir
from gtmcore.dataset.cache import get_cache_manager_class
from gtmcore.dataset.cache.filesystem import HostFilesystemCache


class TestHostFilesystemCache(object):
    def test_get_cache_manager_class(self, mock_dataset_with_cache_dir):
        ds = mock_dataset_with_cache_dir[0]
        cm = get_cache_manager_class(ds.client_config)
        hfc = cm(ds, "tester")
        assert isinstance(hfc, HostFilesystemCache)

        assert hfc.cache_root == os.path.join(ds.client_config.config.get('git')['working_directory'], '.labmanager',
                                              'datasets', 'tester', 'tester', ds.name)

        rev = ds.git.repo.head.commit.hexsha
        assert hfc.current_revision_dir == os.path.join(ds.client_config.config.get('git')['working_directory'],
                                                        '.labmanager', 'datasets', 'tester', 'tester', ds.name, rev)

    def test_get_cache_manager_class_no_config(self, mock_dataset_with_cache_dir):
        ds = mock_dataset_with_cache_dir[0]
        config = ds.client_config
        assert 'datasets' in config.config
        del config.config['datasets']
        assert 'datasets' not in config.config

        cm = get_cache_manager_class(config)
        hfc = cm(ds, "tester")
        assert isinstance(hfc, HostFilesystemCache)

        assert hfc.cache_root == os.path.join(ds.client_config.config.get('git')['working_directory'], '.labmanager',
                                              'datasets', 'tester', 'tester', ds.name)
