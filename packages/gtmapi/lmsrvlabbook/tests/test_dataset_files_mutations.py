import pytest
import os
import uuid
import flask
from aioresponses import aioresponses

from snapshottest import snapshot
from lmsrvlabbook.tests.fixtures import fixture_working_dir_env_repo_scoped, fixture_working_dir

from gtmcore.inventory.inventory import InventoryManager
from gtmcore.dataset.io.manager import IOManager
from gtmcore.dataset.manifest import Manifest

from gtmcore.fixtures.datasets import mock_dataset_with_cache_dir, mock_dataset_with_manifest, helper_append_file


class TestDatasetFilesMutations(object):
    def test_download_dataset_files(self, fixture_working_dir, snapshot):
        # Create a bunch of lab books
        im = InventoryManager(fixture_working_dir[0])
        ds = im.create_dataset('default', 'default', "dataset100", storage_type="gigantum_object_v1", description="100")
        m = Manifest(ds, 'default')
        iom = IOManager(ds, m)

        flask.g.access_token = "asdf"
        flask.g.id_token = "1234"

        os.makedirs(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, "other_dir"))
        helper_append_file(m.cache_mgr.cache_root, m.dataset_revision, "test1.txt", "asdfadfsdf")
        helper_append_file(m.cache_mgr.cache_root, m.dataset_revision, "test2.txt", "fdsfgfd")
        m.sweep_all_changes()

        obj_to_push = iom.objects_to_push()
        assert len(obj_to_push) == 2
        _, obj_id_1 = obj_to_push[0].object_path.rsplit('/', 1)
        _, obj_id_2 = obj_to_push[1].object_path.rsplit('/', 1)
        obj1_target = obj_to_push[0].object_path
        obj2_target = obj_to_push[1].object_path

        obj1_source = os.path.join('/tmp', uuid.uuid4().hex)
        obj2_source = os.path.join('/tmp', uuid.uuid4().hex)

        assert os.path.exists(obj1_target) is True
        assert os.path.exists(obj2_target) is True
        os.rename(obj1_target, obj1_source)
        os.rename(obj2_target, obj2_source)
        assert os.path.isfile(obj1_target) is False
        assert os.path.isfile(obj2_target) is False
        assert os.path.isfile(obj1_source) is True
        assert os.path.isfile(obj2_source) is True

        with aioresponses() as mocked_responses:
            mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj_id_1}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj_id_1}?params=1",
                                         "namespace": ds.namespace,
                                         "obj_id": obj_id_1,
                                         "dataset": ds.name
                                 },
                                 status=200)

            with open(obj1_source, 'rb') as data1:
                mocked_responses.get(f"https://dummyurl.com/{obj_id_1}?params=1",
                                     body=data1.read(), status=200,
                                     content_type='application/octet-stream')

            mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj_id_2}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj_id_2}?params=1",
                                         "namespace": ds.namespace,
                                         "obj_id": obj_id_2,
                                         "dataset": ds.name
                                 },
                                 status=200)

            with open(obj2_source, 'rb') as data2:
                mocked_responses.get(f"https://dummyurl.com/{obj_id_2}?params=1",
                                     body=data2.read(), status=200,
                                     content_type='application/octet-stream')
            iom.dataset.backend.set_default_configuration("default", "abcd", '1234')

            query = """
                       mutation myMutation {
                         downloadDatasetFiles(input: {datasetOwner: "default", datasetName: "dataset100", keys: ["test1.txt"]}) {
                             updatedFileEdges {
                               node {
                                 name
                                 key
                                 isLocal
                                 size
                               }
                             }
                         }
                       }
                       """
            snapshot.assert_match(fixture_working_dir[2].execute(query))

            assert os.path.isfile(obj1_target) is True
            assert os.path.isfile(obj2_target) is False
            with open(obj1_source, 'rt') as dd:
                source1 = dd.read()
            with open(obj1_target, 'rt') as dd:
                assert source1 == dd.read()

            query = """
                       mutation myMutation {
                         downloadDatasetFiles(input: {datasetOwner: "default", datasetName: "dataset100", keys: ["test2.txt"]}) {
                             updatedFileEdges {
                               node {
                                 id
                                 name
                                 isLocal
                                 size
                               }
                             }
                         }
                       }
                       """
            snapshot.assert_match(fixture_working_dir[2].execute(query))

            assert os.path.isfile(obj1_target) is True
            assert os.path.isfile(obj2_target) is True
            with open(obj1_source, 'rt') as dd:
                source1 = dd.read()
            with open(obj1_target, 'rt') as dd:
                assert source1 == dd.read()
            with open(obj2_source, 'rt') as dd:
                source2 = dd.read()
            with open(obj2_target, 'rt') as dd:
                assert source2 == dd.read()

    def test_delete_dataset_files(self, fixture_working_dir, snapshot):
        im = InventoryManager(fixture_working_dir[0])
        ds = im.create_dataset('default', 'default', "dataset-delete",
                               storage_type="gigantum_object_v1", description="testing delete")
        m = Manifest(ds, 'default')

        os.makedirs(os.path.join(m.cache_mgr.cache_root, m.dataset_revision, "other_dir"))
        helper_append_file(m.cache_mgr.cache_root, m.dataset_revision, "test1.txt", "asdfadfsdf")
        helper_append_file(m.cache_mgr.cache_root, m.dataset_revision, "test2.txt", "fdsfgfd")
        helper_append_file(m.cache_mgr.cache_root, m.dataset_revision, "test3.txt", "ghgdsr")
        helper_append_file(m.cache_mgr.cache_root, m.dataset_revision, "other_dir/test3.txt", "hhgf")
        helper_append_file(m.cache_mgr.cache_root, m.dataset_revision, "other_dir/test1.txt", "jkjghfg")
        m.sweep_all_changes()

        revision = m.dataset_revision
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "test1.txt")) is True
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "test2.txt")) is True
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "test3.txt")) is True
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "other_dir", "test3.txt")) is True
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "other_dir", "test1.txt")) is True

        query = """
                   mutation myMutation {
                     deleteDatasetFiles(input: {datasetOwner: "default", datasetName: "dataset-delete", 
                                                keys: ["test1.txt"]}) {
                         success
                     }
                   }
                   """
        result = fixture_working_dir[2].execute(query)
        assert 'errors' not in result
        assert result['data']['deleteDatasetFiles']['success'] is True

        revision = m.dataset_revision
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "test1.txt")) is False
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "test2.txt")) is True
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "test3.txt")) is True
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "other_dir", "test3.txt")) is True
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "other_dir", "test1.txt")) is True

        query = """
                   mutation myMutation {
                     deleteDatasetFiles(input: {datasetOwner: "default", datasetName: "dataset-delete", 
                                                keys: ["test3.txt", "other_dir/"]}) {
                         success
                     }
                   }
                   """
        result = fixture_working_dir[2].execute(query)
        assert 'errors' not in result
        assert result['data']['deleteDatasetFiles']['success'] is True

        revision = m.dataset_revision
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "test1.txt")) is False
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "test2.txt")) is True
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "test3.txt")) is False
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "other_dir", "test3.txt")) is False
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "other_dir", "test1.txt")) is False

    def test_delete_dataset_files_errors(self, fixture_working_dir, snapshot):
        im = InventoryManager(fixture_working_dir[0])
        ds = im.create_dataset('default', 'default', "dataset-delete-2",
                               storage_type="gigantum_object_v1", description="testing delete")
        m = Manifest(ds, 'default')

        helper_append_file(m.cache_mgr.cache_root, m.dataset_revision, "test1.txt", "asdfadfsdf")
        helper_append_file(m.cache_mgr.cache_root, m.dataset_revision, "test2.txt", "fdsfgfd")
        m.sweep_all_changes()

        revision = m.dataset_revision
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "test1.txt")) is True
        assert os.path.exists(os.path.join(m.cache_mgr.cache_root, revision, "test2.txt")) is True

        query = """
                   mutation myMutation {
                     deleteDatasetFiles(input: {datasetOwner: "default", datasetName: "dataset-delete-2", 
                                                keys: ["testdfdfdfdf.txt"]}) {
                         success
                     }
                   }
                   """
        result = fixture_working_dir[2].execute(query)
        assert 'errors' in result

    def test_move_dataset_file(self, fixture_working_dir, snapshot):
        im = InventoryManager(fixture_working_dir[0])
        ds = im.create_dataset('default', 'default', "dataset-move",
                               storage_type="gigantum_object_v1", description="testing move")
        m = Manifest(ds, 'default')

        revision = m.dataset_revision
        helper_append_file(m.cache_mgr.cache_root, revision, "test1.txt", "asdfasdghndfdf")
        m.sweep_all_changes()

        revision = m.dataset_revision
        cr = m.cache_mgr.cache_root
        assert os.path.exists(os.path.join(cr, revision, "test1.txt")) is True

        query = """
                   mutation myMutation {
                     moveDatasetFile(input: {datasetOwner: "default", datasetName: "dataset-move", 
                                             srcPath: "test1.txt", dstPath: "test1-renamed.txt"}) {
                         updatedEdges {
                            node {
                              id
                              key
                              isDir
                              isFavorite
                              isLocal
                              size
                            }
                         }
                     }
                   }
                   """
        result = fixture_working_dir[2].execute(query)
        assert 'errors' not in result
        snapshot.assert_match(result)

        revision = m.dataset_revision
        cr = m.cache_mgr.cache_root
        assert os.path.exists(os.path.join(cr, revision, "test1.txt")) is False
        assert os.path.exists(os.path.join(cr, revision, "test1-renamed.txt")) is True

    def test_move_dataset_dir(self, fixture_working_dir, snapshot):
        im = InventoryManager(fixture_working_dir[0])
        ds = im.create_dataset('default', 'default', "dataset-move",
                               storage_type="gigantum_object_v1", description="testing move")
        m = Manifest(ds, 'default')

        revision = m.dataset_revision
        os.makedirs(os.path.join(m.cache_mgr.cache_root, revision, "first_dir"))
        os.makedirs(os.path.join(m.cache_mgr.cache_root, revision, "other_dir"))
        os.makedirs(os.path.join(m.cache_mgr.cache_root, revision, "other_dir", "nested_dir"))
        helper_append_file(m.cache_mgr.cache_root, revision, "test1.txt", "asdfasdghndfdf")
        helper_append_file(m.cache_mgr.cache_root, revision, "test2.txt", "asdfdf")
        helper_append_file(m.cache_mgr.cache_root, revision, "first_dir/test3.txt", "4456tyfg")
        helper_append_file(m.cache_mgr.cache_root, revision, "other_dir/nested_dir/test6.txt", "4456tyfg")
        helper_append_file(m.cache_mgr.cache_root, revision, "other_dir/nested_dir/test7.txt", "fgfyytr")
        m.sweep_all_changes()

        revision = m.dataset_revision
        cr = m.cache_mgr.cache_root
        assert os.path.exists(os.path.join(cr, revision, "test1.txt")) is True
        assert os.path.exists(os.path.join(cr, revision, "test2.txt")) is True
        assert os.path.exists(os.path.join(cr, revision, "first_dir", "test3.txt")) is True
        assert os.path.exists(os.path.join(cr, revision, "other_dir", "nested_dir", "test6.txt")) is True
        assert os.path.exists(os.path.join(cr, revision, "other_dir", "nested_dir", "test7.txt")) is True

        query = """
                   mutation myMutation {
                     moveDatasetFile(input: {datasetOwner: "default", datasetName: "dataset-move", 
                                             srcPath: "first_dir/", dstPath: "other_dir/first_dir/"}) {
                         updatedEdges {
                            node {
                              id
                              key
                              isDir
                              isFavorite
                              isLocal
                              size
                            }
                         }
                     }
                   }
                   """
        result = fixture_working_dir[2].execute(query)
        assert 'errors' not in result
        snapshot.assert_match(result)

        revision = m.dataset_revision
        cr = m.cache_mgr.cache_root
        assert os.path.exists(os.path.join(cr, revision, "test1.txt")) is True
        assert os.path.exists(os.path.join(cr, revision, "test2.txt")) is True
        assert os.path.exists(os.path.join(cr, revision, "first_dir", "test3.txt")) is False
        assert os.path.exists(os.path.join(cr, revision, "other_dir", "first_dir", "test3.txt")) is True
        assert os.path.exists(os.path.join(cr, revision, "other_dir", "nested_dir", "test6.txt")) is True
        assert os.path.exists(os.path.join(cr, revision, "other_dir", "nested_dir", "test7.txt")) is True

        query = """
                   mutation myMutation {
                     moveDatasetFile(input: {datasetOwner: "default", datasetName: "dataset-move", 
                                             srcPath: "other_dir/", dstPath: "other_dir_renamed/"}) {
                         updatedEdges {
                            node {
                              id
                              key
                              isDir
                              isFavorite
                              isLocal
                              size
                            }
                         }
                     }
                   }
                   """
        result = fixture_working_dir[2].execute(query)
        assert 'errors' not in result
        snapshot.assert_match(result)

        revision = m.dataset_revision
        cr = m.cache_mgr.cache_root
        assert os.path.exists(os.path.join(cr, revision, "test1.txt")) is True
        assert os.path.exists(os.path.join(cr, revision, "test2.txt")) is True
        assert os.path.exists(os.path.join(cr, revision, "other_dir", "first_dir", "test3.txt")) is False
        assert os.path.exists(os.path.join(cr, revision, "other_dir", "nested_dir", "test6.txt")) is False
        assert os.path.exists(os.path.join(cr, revision, "other_dir", "nested_dir", "test7.txt")) is False
        assert os.path.exists(os.path.join(cr, revision, "other_dir_renamed", "first_dir", "test3.txt")) is True
        assert os.path.exists(os.path.join(cr, revision, "other_dir_renamed", "nested_dir", "test6.txt")) is True
        assert os.path.exists(os.path.join(cr, revision, "other_dir_renamed", "nested_dir", "test7.txt")) is True

    def test_make_directory(self, fixture_working_dir, snapshot):
        im = InventoryManager(fixture_working_dir[0])
        ds = im.create_dataset('default', 'default', "dataset-dir",
                               storage_type="gigantum_object_v1", description="testing move")
        m = Manifest(ds, 'default')
        m.link_revision()

        query = """
                   mutation myMutation {
                     makeDatasetDirectory(input: {datasetOwner: "default", datasetName: "dataset-dir", 
                                             key: "test_dir1/"}) {
                         newDatasetFileEdge {
                            node {
                              id
                              key
                              isDir
                              isFavorite
                              isLocal
                              size
                            }
                         }
                     }
                   }
                   """
        result = fixture_working_dir[2].execute(query)
        assert 'errors' not in result
        assert result['data']['makeDatasetDirectory']['newDatasetFileEdge']['node']['key'] == 'test_dir1/'
        assert result['data']['makeDatasetDirectory']['newDatasetFileEdge']['node']['isDir'] is True
        assert result['data']['makeDatasetDirectory']['newDatasetFileEdge']['node']['isLocal'] is True
        assert result['data']['makeDatasetDirectory']['newDatasetFileEdge']['node']['size'] == '0'

        assert os.path.isdir(os.path.join(m.cache_mgr.current_revision_dir, "test_dir1")) is True

        query = """
                   mutation myMutation {
                     makeDatasetDirectory(input: {datasetOwner: "default", datasetName: "dataset-dir", 
                                             key: "test_dir1/test_dir2/"}) {
                         newDatasetFileEdge {
                            node {
                              id
                              key
                              isDir
                              isFavorite
                              isLocal
                              size
                            }
                         }
                     }
                   }
                   """
        result = fixture_working_dir[2].execute(query)
        assert 'errors' not in result
        assert result['data']['makeDatasetDirectory']['newDatasetFileEdge']['node']['key'] == 'test_dir1/test_dir2/'
        assert result['data']['makeDatasetDirectory']['newDatasetFileEdge']['node']['isDir'] is True
        assert result['data']['makeDatasetDirectory']['newDatasetFileEdge']['node']['isLocal'] is True
        assert result['data']['makeDatasetDirectory']['newDatasetFileEdge']['node']['size'] == '0'

        assert os.path.isdir(os.path.join(m.cache_mgr.current_revision_dir, "test_dir1")) is True
        assert os.path.isdir(os.path.join(m.cache_mgr.current_revision_dir, "test_dir1", "test_dir2")) is True

    def test_make_directory_error(self, fixture_working_dir, snapshot):
        im = InventoryManager(fixture_working_dir[0])
        ds = im.create_dataset('default', 'default', "dataset-dir",
                               storage_type="gigantum_object_v1", description="testing move")
        m = Manifest(ds, 'default')

        # Test where parent dir doesnt exists (because you need to create the parent)
        query = """
                   mutation myMutation {
                     makeDatasetDirectory(input: {datasetOwner: "default", datasetName: "dataset-dir", 
                                             key: "test_dir1/test_dir2/"}) {
                         newDatasetFileEdge {
                            node {
                              id
                              key
                              isDir
                              isFavorite
                              isLocal
                              size
                            }
                         }
                     }
                   }
                   """
        result = fixture_working_dir[2].execute(query)
        assert 'errors' in result
        assert 'Parent directory' in result['errors'][0]['message']

        # Test where missing trailing slash
        query = """
                   mutation myMutation {
                     makeDatasetDirectory(input: {datasetOwner: "default", datasetName: "dataset-dir", 
                                             key: "test_dir1"}) {
                         newDatasetFileEdge {
                            node {
                              id
                              key
                              isDir
                              isFavorite
                              isLocal
                              size
                            }
                         }
                     }
                   }
                   """
        result = fixture_working_dir[2].execute(query)
        assert 'errors' in result
        assert 'Provided relative path must end in' in result['errors'][0]['message']
