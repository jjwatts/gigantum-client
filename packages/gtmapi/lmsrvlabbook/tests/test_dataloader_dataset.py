import pytest
from lmsrvlabbook.tests.fixtures import fixture_working_dir

from promise import Promise
from lmsrvlabbook.dataloader.dataset import DatasetLoader
from gtmcore.inventory.inventory import InventoryManager


class TestDataloaderDataset(object):

    def test_load_one(self, fixture_working_dir):
        """Test loading 1 dataset"""
        im = InventoryManager(fixture_working_dir[0])
        im.create_dataset("default", "default", "dataset1", storage_type="gigantum_object_v1",
                          description="a dataset")
        im.create_dataset("default", "default", "dataset2", storage_type="gigantum_object_v1",
                          description="another dataset")
        loader = DatasetLoader()

        key = f"default&default&dataset1"
        promise1 = loader.load(key)
        assert isinstance(promise1, Promise)

        lb = promise1.get()
        assert lb.name == "dataset1"
        assert lb.description == "a dataset"

    def test_load_many(self, fixture_working_dir):
        """Test loading many labbooks"""
        im = InventoryManager(fixture_working_dir[0])
        im.create_dataset("default", "default", "dataset1", storage_type="gigantum_object_v1",
                          description="a dataset")
        im.create_dataset("default", "default", "dataset2", storage_type="gigantum_object_v1",
                          description="another dataset")
        im.create_dataset("default", "tester_user", "dataset3", storage_type="gigantum_object_v1",
                          description="yet another dataset")

        loader = DatasetLoader()

        keys = ["default&default&dataset1", "default&default&dataset2", "default&tester_user&dataset3"]
        promise1 = loader.load_many(keys)
        assert isinstance(promise1, Promise)

        ds_list = promise1.get()
        assert ds_list[0].name == "dataset1"
        assert ds_list[0].description == "a dataset"
        assert ds_list[1].name == "dataset2"
        assert ds_list[1].description == "another dataset"
        assert ds_list[2].name == "dataset3"
        assert ds_list[2].description == "yet another dataset"

