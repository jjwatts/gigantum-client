import pytest
import getpass
import os
import yaml
import datetime
import shutil
import tempfile
import time

from gtmcore.dataset.dataset import Dataset
from gtmcore.inventory.inventory import InventoryManager, InventoryException
from gtmcore.gitlib.git import GitAuthor

from gtmcore.fixtures import mock_config_file, mock_labbook, _MOCK_create_remote_repo2


@pytest.fixture()
def create_datasets_to_list(mock_config_file):
    inv_manager = InventoryManager(mock_config_file[0])
    inv_manager.create_dataset("user1", "user1", "dataset2", "gigantum_object_v1", description="my dataset")
    inv_manager.create_dataset("user1", "user2", "a-dataset3", "gigantum_object_v1", description="my dataset")
    inv_manager.create_dataset("user1", "user1", "dataset12", "gigantum_object_v1", description="my dataset")
    inv_manager.create_dataset("user2", "user1", "dataset1", "gigantum_object_v1", description="my dataset")
    yield mock_config_file


class TestInventoryDatasets(object):
    def test_create_dataset_with_author(self, mock_config_file):
        """Test creating an empty labbook with the author set"""
        inv_manager = InventoryManager(mock_config_file[0])
        auth = GitAuthor(name="username", email="user1@test.com")
        ds = inv_manager.create_dataset("test", "test", "dataset1", "gigantum_object_v1",
                                        description="my first dataset",
                                        author=auth)
        dataset_dir = ds.root_dir

        assert dataset_dir == os.path.join(mock_config_file[1], "test", "test", "datasets", "dataset1")
        assert type(ds) == Dataset

        # Validate directory structure
        assert os.path.isdir(os.path.join(dataset_dir, "metadata")) is True
        assert os.path.isdir(os.path.join(dataset_dir, "manifest")) is True
        assert os.path.isdir(os.path.join(dataset_dir, ".gigantum")) is True
        assert os.path.isdir(os.path.join(dataset_dir, ".gigantum", "activity")) is True
        assert os.path.isdir(os.path.join(dataset_dir, ".gigantum", "favorites")) is True
        assert os.path.isdir(os.path.join(dataset_dir, ".gigantum", "activity", "log")) is True

        # Validate dataset data file
        with open(os.path.join(dataset_dir, ".gigantum", "gigantum.yaml"), "rt") as data_file:
            data = yaml.safe_load(data_file)

        assert data["name"] == "dataset1"
        assert data["description"] == "my first dataset"
        assert data["storage_type"] == "gigantum_object_v1"
        assert "id" in data
        assert ds.build_details is not None

        log_data = ds.git.log()
        assert log_data[0]['author']['name'] == "username"
        assert log_data[0]['author']['email'] == "user1@test.com"
        assert log_data[0]['committer']['name'] == "Gigantum AutoCommit"
        assert log_data[0]['committer']['email'] == "noreply@gigantum.io"

        assert os.path.exists(os.path.join(ds.root_dir, '.gigantum', 'backend.json')) is True

    def test_dataset_attributes(self, mock_config_file):
        inv_manager = InventoryManager(mock_config_file[0])
        auth = GitAuthor(name="username", email="user1@test.com")
        ds = inv_manager.create_dataset("test", "test", "dataset1", "gigantum_object_v1",
                                        description="my first dataset",
                                        author=auth)
        root_dir = ds.root_dir
        assert "dataset1" in root_dir
        assert "datasets" in root_dir

        assert ds.name == 'dataset1'
        assert ds.namespace == 'test'
        assert ds.description == 'my first dataset'
        assert isinstance(ds.creation_date, datetime.datetime)
        assert ds.build_details is not None

        assert ds.storage_type == "gigantum_object_v1"

        assert ds.backend_config == {}
        ds.backend_config = {"my_config": 123}
        assert ds.backend_config == {"my_config": 123}

    def test_delete_dataset(self, mock_config_file):
        inv_manager = InventoryManager(mock_config_file[0])
        auth = GitAuthor(name="username", email="user1@test.com")
        ds = inv_manager.create_dataset("test", "test", "dataset1", "gigantum_object_v1",
                                        description="my first dataset",
                                        author=auth)
        root_dir = ds.root_dir
        assert os.path.exists(root_dir) is True

        inv_manager.delete_dataset("test", "test", "dataset1")
        assert os.path.exists(root_dir) is False

    def test_change_dataset_name(self, mock_config_file):
        inv_manager = InventoryManager(mock_config_file[0])
        auth = GitAuthor(name="username", email="user1@test.com")
        ds = inv_manager.create_dataset("test", "test", "dataset1", "gigantum_object_v1",
                                        description="my first dataset",
                                        author=auth)
        root_dir1 = ds.root_dir
        assert ds.name == 'dataset1'

        ds.name = 'dataset-updated'
        root_dir2 = ds.root_dir

        parts1 = root_dir1.split(os.path.sep)
        parts2 = root_dir2.split(os.path.sep)

        assert parts1[0] == parts2[0]
        assert parts1[1] == parts2[1]
        assert parts1[2] == parts2[2]
        assert parts1[3] == parts2[3]
        assert parts1[4] == parts2[4]
        assert parts1[5] == parts2[5]
        assert parts1[6] == 'dataset1'
        assert parts2[6] == 'dataset-updated'

    def test_change_dataset_name_errors(self, mock_config_file):
        inv_manager = InventoryManager(mock_config_file[0])
        auth = GitAuthor(name="username", email="user1@test.com")
        ds = inv_manager.create_dataset("test", "test", "dataset1", "gigantum_object_v1",
                                        description="my first dataset",
                                        author=auth)

        with pytest.raises(ValueError):
            ds.name = 'dataset_updated'

        ds.name = 'd' * 100
        with pytest.raises(ValueError):
            ds.name = 'd' * 101

    def test_create_dataset_that_exists(self, mock_config_file):
        """Test trying to create a labbook with a name that already exists locally"""
        inv_manager = InventoryManager(mock_config_file[0])
        auth = GitAuthor(name="username", email="user1@test.com")
        ds = inv_manager.create_dataset("test", "test", "dataset1", "gigantum_object_v1",
                                        description="my first dataset",
                                        author=auth)
        with pytest.raises(ValueError):
            inv_manager.create_dataset("test", "test", "dataset1", "gigantum_object_v1",
                                       description="my first dataset",
                                       author=auth)

    def test_load_dataset_from_file(self, mock_config_file):
        inv_manager = InventoryManager(mock_config_file[0])
        auth = GitAuthor(name="username", email="user1@test.com")
        ds = inv_manager.create_dataset("test", "test", "dataset1", "gigantum_object_v1",
                                        description="my first dataset",
                                        author=auth)

        with tempfile.TemporaryDirectory() as tempdir:
            r = shutil.move(ds.root_dir, tempdir)
            ds_loaded_from_file = inv_manager.load_dataset_from_directory(r)

        # Test failing case - invalid dir
        with pytest.raises(InventoryException):
            r = inv_manager.load_dataset_from_directory('/tmp')

    def test_put_dataset(self, mock_config_file):
        inv_manager = InventoryManager(mock_config_file[0])
        auth = GitAuthor(name="username", email="user1@test.com")
        ds = inv_manager.create_dataset("test", "test", "dataset1", "gigantum_object_v1",
                                        description="my first dataset",
                                        author=auth)

        orig_location = ds.root_dir
        with tempfile.TemporaryDirectory() as tempdir:
            r = shutil.move(ds.root_dir, tempdir)
            ds_loaded_from_file = inv_manager.load_dataset_from_directory(r)
            assert not os.path.exists(orig_location)
            assert orig_location not in [d.root_dir for d in inv_manager.list_datasets('test')]
            placed_ds = inv_manager.put_dataset(r, 'test', 'test')
            assert placed_ds.root_dir in [d.root_dir for d in inv_manager.list_datasets('test')]

    def test_list_datasets_empty(self, mock_labbook):
        """Test list datasets when no dataset directory exists for the user"""
        inv_manager = InventoryManager(mock_labbook[0])
        datasets = inv_manager.list_datasets(username="test")
        assert len(datasets) == 0

    def test_list_datasets_az(self, create_datasets_to_list):
        """Test list az datasets"""
        inv_manager = InventoryManager(create_datasets_to_list[0])
        datasets = inv_manager.list_datasets(username="user1")
        assert len(datasets) == 3
        assert datasets[0].name == 'a-dataset3'
        assert datasets[1].name == 'dataset2'
        assert datasets[2].name == 'dataset12'

        datasets = inv_manager.list_datasets(username="user2")
        assert len(datasets) == 1
        assert datasets[0].name == 'dataset1'

    def test_list_datasets_created_on(self, create_datasets_to_list):
        """Test list az datasets"""
        inv_manager = InventoryManager(create_datasets_to_list[0])

        datasets = inv_manager.list_datasets(username="user1", sort_mode="created_on")
        assert len(datasets) == 3
        assert datasets[0].name == 'dataset2'
        assert datasets[1].name == 'a-dataset3'
        assert datasets[2].name == 'dataset12'

    def test_list_datasets_modified_on(self, mock_config_file):
        """Test list az datasets"""
        inv_manager = InventoryManager(mock_config_file[0])
        inv_manager.create_dataset("user1", "user1", "dataset2", "gigantum_object_v1", description="my dataset")
        time.sleep(1)
        inv_manager.create_dataset("user1", "user2", "a-dataset3", "gigantum_object_v1", description="my dataset")
        time.sleep(1)
        inv_manager.create_dataset("user1", "user1", "dataset12", "gigantum_object_v1", description="my dataset")
        time.sleep(1)
        inv_manager.create_dataset("user2", "user1", "dataset1", "gigantum_object_v1", description="my dataset")

        datasets = inv_manager.list_datasets(username="user1", sort_mode="modified_on")
        assert len(datasets) == 3
        assert datasets[0].name == 'dataset2'
        assert datasets[1].name == 'a-dataset3'
        assert datasets[2].name == 'dataset12'

        # modify a repo
        time.sleep(1.2)
        ds = inv_manager.load_dataset('user1', 'user1', 'dataset2')
        with open(os.path.join(ds.root_dir, "manifest", "test.txt"), 'wt') as tf:
            tf.write("asdfasdf")
        ds.git.add_all()
        ds.git.commit("Changing the repo")

        datasets = inv_manager.list_datasets(username="user1", sort_mode="modified_on")
        assert len(datasets) == 3
        assert datasets[0].name == 'a-dataset3'
        assert datasets[1].name == 'dataset12'
        assert datasets[2].name == 'dataset2'

    def test_list_datasets_invalid(self, create_datasets_to_list):
        """Test list az datasets"""
        inv_manager = InventoryManager(create_datasets_to_list[0])

        with pytest.raises(InventoryException):
            _ = inv_manager.list_datasets(username="user1", sort_mode="created_atasdf")

    def test_create_dataset_invalid_storage_type(self, mock_config_file):
        inv_manager = InventoryManager(mock_config_file[0])
        auth = GitAuthor(name="username", email="user1@test.com")
        with pytest.raises(ValueError):
            inv_manager.create_dataset("test", "test", "dataset1", "asdfdfgh",
                                       description="my first dataset",
                                       author=auth)

    def test_link_unlink_dataset(self, mock_labbook):
        inv_manager = InventoryManager(mock_labbook[0])
        lb = mock_labbook[2]
        ds = inv_manager.create_dataset("test", "test", "dataset100", "gigantum_object_v1", description="my dataset")

        # Fake publish to a local bare repo
        _MOCK_create_remote_repo2(ds, 'test', None, None)

        assert os.path.exists(os.path.join(lb.root_dir, '.gitmodules')) is False

        inv_manager.link_dataset_to_labbook(ds.remote, 'test', 'dataset100', lb)

        assert os.path.exists(os.path.join(lb.root_dir, '.gitmodules')) is True
        dataset_submodule_dir = os.path.join(lb.root_dir, '.gigantum', 'datasets', 'test', 'dataset100')
        assert os.path.exists(dataset_submodule_dir) is True
        assert os.path.exists(os.path.join(dataset_submodule_dir, '.gigantum')) is True

        inv_manager.unlink_dataset_from_labbook('test', 'dataset100', lb)

        dataset_submodule_dir = os.path.join(lb.root_dir, '.gigantum', 'datasets', 'test', 'dataset100')
        assert os.path.exists(dataset_submodule_dir) is False
        assert os.path.exists(os.path.join(dataset_submodule_dir, '.gigantum')) is False
        with open(os.path.join(lb.root_dir, '.gitmodules'), 'rt') as mf:
            data = mf.read()

        assert len(data) == 0

