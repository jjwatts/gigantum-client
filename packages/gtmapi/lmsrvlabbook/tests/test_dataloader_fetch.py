import pytest
from lmsrvlabbook.tests.fixtures import fixture_working_dir

from promise import Promise
from lmsrvlabbook.dataloader.fetch import FetchLoader
from gtmcore.inventory.inventory import InventoryManager


class TestDataloaderFetch(object):
    def test_load_one_dataset(self, fixture_working_dir):
        im = InventoryManager(fixture_working_dir[0])
        im.create_dataset("default", "default", "dataset1", storage_type="gigantum_object_v1",
                          description="a dataset")
        im.create_dataset("default", "default", "dataset2", storage_type="gigantum_object_v1",
                          description="another dataset")
        loader = FetchLoader()

        key = f"dataset&default&default&dataset1"
        promise1 = loader.load(key)
        assert isinstance(promise1, Promise)
        assert promise1.get() is None

    def test_load_many_dataset(self, fixture_working_dir):
        im = InventoryManager(fixture_working_dir[0])
        im.create_dataset("default", "default", "dataset1", storage_type="gigantum_object_v1",
                          description="a dataset")
        im.create_dataset("default", "default", "dataset2", storage_type="gigantum_object_v1",
                          description="another dataset")
        im.create_dataset("default", "tester_user", "dataset3", storage_type="gigantum_object_v1",
                          description="yet another dataset")

        loader = FetchLoader()

        keys = ["dataset&default&default&dataset1", "dataset&default&default&dataset2",
                "dataset&default&tester_user&dataset3"]
        promise1 = loader.load_many(keys)
        assert isinstance(promise1, Promise)
        promise1.get()

    def test_load_one_labbook(self, fixture_working_dir):
        im = InventoryManager(fixture_working_dir[0])
        im.create_labbook("default", "default", "lb1", description="a project")
        im.create_labbook("default", "default", "lb2", description="a project")
        loader = FetchLoader()

        key = "labbook&default&default&lb1"
        promise1 = loader.load(key)
        assert isinstance(promise1, Promise)
        assert promise1.get() is None

    def test_load_labbook_multiple(self, fixture_working_dir):
        im = InventoryManager(fixture_working_dir[0])
        im.create_labbook("default", "default", "lb1", description="a project")
        im.create_labbook("default", "default", "lb2", description="a project")
        loader = FetchLoader()

        key = "labbook&default&default&lb1"
        promise1 = loader.load(key)
        promise2 = loader.load(key)
        promise3 = loader.load(key)
        assert isinstance(promise1, Promise)
        assert promise1.get() is None
        assert promise2.get() is None
        assert promise3.get() is None

    def test_load_many_labbook(self, fixture_working_dir):
        im = InventoryManager(fixture_working_dir[0])
        im.create_labbook("default", "default", "lb1", description="a project")
        im.create_labbook("default", "default", "lb2", description="a project")
        im.create_labbook("default", "default", "lb3", description="a project")

        loader = FetchLoader()

        keys = ["labbook&default&default&lb1", "labbook&default&default&lb2",
                "labbook&default&default&lb3"]
        promise1 = loader.load_many(keys)
        assert isinstance(promise1, Promise)
        promise1.get()

    def test_load_err(self, fixture_working_dir):
        im = InventoryManager(fixture_working_dir[0])
        im.create_labbook("default", "default", "lb1", description="a project")
        loader = FetchLoader()

        key = "invalidkey&default&default&lb1"
        with pytest.raises(ValueError):
            promise1 = loader.load(key)
            promise1.get()
