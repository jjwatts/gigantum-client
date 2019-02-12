import pytest
import os
import glob
import uuid
import shutil
from aioresponses import aioresponses

from gtmcore.inventory.branching import BranchManager
from gtmcore.dataset.io.manager import IOManager
from gtmcore.fixtures.datasets import mock_dataset_with_cache_dir, mock_dataset_with_manifest, helper_append_file,\
    USERNAME
from gtmcore.dataset.io import PushResult, PushObject


class TestIOManager(object):
    def test_init(self, mock_dataset_with_manifest):
        ds, manifest, working_dir = mock_dataset_with_manifest
        iom = IOManager(ds, manifest)
        assert isinstance(iom, IOManager)
        assert isinstance(iom.push_dir, str)

    def test_objects_to_push(self, mock_dataset_with_manifest):
        ds, manifest, working_dir = mock_dataset_with_manifest
        iom = IOManager(ds, manifest)

        revision = manifest.dataset_revision
        os.makedirs(os.path.join(manifest.cache_mgr.cache_root, revision, "other_dir"))
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test1.txt", "asdfasdf")
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test2.txt", "asfdfdfasdf")
        helper_append_file(manifest.cache_mgr.cache_root, revision, "other_dir/test4.txt", "dfasdfhfgjhg")
        manifest.sweep_all_changes()

        # Modify file to have 2 objects with same key
        helper_append_file(manifest.cache_mgr.cache_root, iom.manifest.dataset_revision, "test2.txt", "fghdfghdfghdf")
        manifest.sweep_all_changes()

        obj_to_push = iom.objects_to_push()

        assert len(obj_to_push) == 4
        assert obj_to_push[0].dataset_path == "other_dir/test4.txt"
        assert obj_to_push[1].dataset_path == "test1.txt"
        assert obj_to_push[2].dataset_path == "test2.txt"
        assert obj_to_push[3].dataset_path == "test2.txt"
        assert obj_to_push[2].revision != obj_to_push[3].revision

        assert iom.num_objects_to_push() == 4

    def test_objects_to_push_deduped(self, mock_dataset_with_manifest):
        ds, manifest, working_dir = mock_dataset_with_manifest
        iom = IOManager(ds, manifest)

        revision = manifest.dataset_revision
        os.makedirs(os.path.join(manifest.cache_mgr.cache_root, revision, "other_dir"))
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test1.txt", "asdfadfsdf")
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test2.txt", "asdfadfsdf")
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test3.txt", "asdfadfsdf")
        helper_append_file(manifest.cache_mgr.cache_root, revision, "other_dir/test4.txt", "dfasdfhfgjhg")
        manifest.sweep_all_changes()

        # Write a .DS_Store file in the objects dir to make sure it gets skipped
        with open(os.path.join(manifest.cache_mgr.cache_root, 'objects', '.push', '.DS_Store'), 'wt') as ff:
            ff.write("")

        obj_to_push = iom.objects_to_push(remove_duplicates=True)

        assert len(obj_to_push) == 2
        assert obj_to_push[0].dataset_path == "other_dir/test4.txt"
        assert obj_to_push[1].dataset_path == "test1.txt"

        assert iom.num_objects_to_push(remove_duplicates=True) == 2

    def test_objects_to_push_ignore_other_branch(self, mock_dataset_with_manifest):
        ds, manifest, working_dir = mock_dataset_with_manifest
        iom = IOManager(ds, manifest)

        revision = manifest.dataset_revision
        os.makedirs(os.path.join(manifest.cache_mgr.cache_root, revision, "other_dir"))
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test1.txt", "asdfadfsdf")
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test2.txt", "fdsfgfd")
        manifest.sweep_all_changes()

        obj_to_push = iom.objects_to_push()
        assert len(obj_to_push) == 2
        assert obj_to_push[0].dataset_path == "test1.txt"
        assert obj_to_push[1].dataset_path == "test2.txt"

        # Create new branch and add a file there
        bm = BranchManager(ds, username=USERNAME)
        starting_branch = bm.active_branch
        bm.create_branch(title="test-branch")
        assert bm.active_branch == "test-branch"
        assert ds.is_repo_clean is True

        helper_append_file(manifest.cache_mgr.cache_root, iom.manifest.dataset_revision, "test3.txt", "fdsfgfd")
        manifest.sweep_all_changes()

        obj_to_push = iom.objects_to_push()
        assert len(obj_to_push) == 3
        assert obj_to_push[0].dataset_path == "test1.txt"
        assert obj_to_push[1].dataset_path == "test2.txt"
        assert obj_to_push[2].dataset_path == "test3.txt"

        # Go back to original branch, you shouldn't have to push file on other branch
        bm.workon_branch(starting_branch)

        obj_to_push = iom.objects_to_push()
        assert len(obj_to_push) == 2
        assert obj_to_push[0].dataset_path == "test1.txt"
        assert obj_to_push[1].dataset_path == "test2.txt"

    def test_push_objects(self, mock_dataset_with_manifest):
        ds, manifest, working_dir = mock_dataset_with_manifest
        iom = IOManager(ds, manifest)

        revision = manifest.dataset_revision
        os.makedirs(os.path.join(manifest.cache_mgr.cache_root, revision, "other_dir"))
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test1.txt", "asdfadfsdf")
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test2.txt", "fdsfgfd")
        manifest.sweep_all_changes()

        obj_to_push = iom.objects_to_push()
        assert len(obj_to_push) == 2
        _, obj1 = obj_to_push[0].object_path.rsplit('/', 1)
        _, obj2 = obj_to_push[1].object_path.rsplit('/', 1)

        with aioresponses() as mocked_responses:
            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj1}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj1}?params=1",
                                         "namespace": ds.namespace,
                                         "key_id": "hghghg",
                                         "obj_id": obj1,
                                         "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put(f"https://dummyurl.com/{obj1}?params=1",
                                 payload={},
                                 status=200)

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj2}',
                                 payload={
                                  "presigned_url": f"https://dummyurl.com/{obj2}?params=1",
                                  "namespace": ds.namespace,
                                  "key_id": "hghghg",
                                  "obj_id": obj2,
                                  "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put(f"https://dummyurl.com/{obj2}?params=1",
                                 payload={},
                                 status=200)

            assert len(glob.glob(f'{iom.push_dir}/*')) == 1
            iom.dataset.backend.set_default_configuration("test-user", "abcd", '1234')

            result = iom.push_objects()
            assert len(glob.glob(f'{iom.push_dir}/*')) == 0

            assert len(result.success) == 2
            assert len(result.failure) == 0
            assert isinstance(result, PushResult) is True
            assert isinstance(result.success[0], PushObject) is True
            assert result.success[0].object_path != result.success[1].object_path
            assert result.success[0].object_path in [obj_to_push[0].object_path, obj_to_push[1].object_path]
            assert result.success[1].object_path in [obj_to_push[0].object_path, obj_to_push[1].object_path]

    def test_push_objects_deduplicate(self, mock_dataset_with_manifest):
        ds, manifest, working_dir = mock_dataset_with_manifest
        iom = IOManager(ds, manifest)

        revision = manifest.dataset_revision
        os.makedirs(os.path.join(manifest.cache_mgr.cache_root, revision, "other_dir"))
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test1.txt", "asdfadfsdf")
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test2.txt", "fdsfgfd")
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test3.txt", "fdsfgfd")
        manifest.sweep_all_changes()

        obj_to_push = iom.objects_to_push()
        assert len(obj_to_push) == 3
        _, obj1 = obj_to_push[0].object_path.rsplit('/', 1)
        _, obj2 = obj_to_push[1].object_path.rsplit('/', 1)
        _, obj3 = obj_to_push[2].object_path.rsplit('/', 1)
        assert obj1 != obj2
        assert obj2 == obj3

        with aioresponses() as mocked_responses:
            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj1}',
                                 payload={
                                     "presigned_url": f"https://dummyurl.com/{obj1}?params=1",
                                     "namespace": ds.namespace,
                                     "key_id": "hghghg",
                                     "obj_id": obj1,
                                     "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put(f"https://dummyurl.com/{obj1}?params=1",
                                 payload={},
                                 status=200)

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj2}',
                                 payload={
                                     "presigned_url": f"https://dummyurl.com/{obj2}?params=1",
                                     "namespace": ds.namespace,
                                     "key_id": "hghghg",
                                     "obj_id": obj2,
                                     "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put(f"https://dummyurl.com/{obj2}?params=1",
                                 payload={},
                                 status=200)

            assert len(glob.glob(f'{iom.push_dir}/*')) == 1
            iom.dataset.backend.set_default_configuration("test-user", "abcd", '1234')

            result = iom.push_objects()
            assert len(glob.glob(f'{iom.push_dir}/*')) == 0

            assert len(result.success) == 2
            assert len(result.failure) == 0
            assert isinstance(result, PushResult) is True
            assert isinstance(result.success[0], PushObject) is True
            assert result.success[0].object_path != result.success[1].object_path
            assert result.success[0].object_path in [obj_to_push[0].object_path, obj_to_push[1].object_path]
            assert result.success[1].object_path in [obj_to_push[0].object_path, obj_to_push[1].object_path]

    def test_push_objects_with_failure(self, mock_dataset_with_manifest):
        ds, manifest, working_dir = mock_dataset_with_manifest
        iom = IOManager(ds, manifest)

        revision = manifest.dataset_revision
        os.makedirs(os.path.join(manifest.cache_mgr.cache_root, revision, "other_dir"))
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test1.txt", "asdfadfsdf")
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test2.txt", "fdsfgfd")
        manifest.sweep_all_changes()

        obj_to_push = iom.objects_to_push()
        assert len(obj_to_push) == 2
        _, obj1 = obj_to_push[0].object_path.rsplit('/', 1)
        _, obj2 = obj_to_push[1].object_path.rsplit('/', 1)

        with aioresponses() as mocked_responses:
            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj1}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj1}?params=1",
                                         "namespace": ds.namespace,
                                         "key_id": "hghghg",
                                         "obj_id": obj1,
                                         "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put(f"https://dummyurl.com/{obj1}?params=1",
                                 payload={},
                                 status=200)

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj2}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj2}?params=1",
                                         "namespace": ds.namespace,
                                         "key_id": "hghghg",
                                         "obj_id": obj2,
                                         "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put(f"https://dummyurl.com/{obj2}?params=1",
                                 payload={},
                                 status=400)
    
            assert len(glob.glob(f'{iom.push_dir}/*')) == 1
            iom.dataset.backend.set_default_configuration("test-user", "abcd", '1234')
    
            result = iom.push_objects()
            assert len(glob.glob(f'{iom.push_dir}/*')) == 1
    
            assert len(result.success) == 1
            assert len(result.failure) == 1
            assert result.success[0].object_path == obj_to_push[0].object_path
            assert result.failure[0].object_path == obj_to_push[1].object_path

    def test_pull_objects(self, mock_dataset_with_manifest):
        ds, manifest, working_dir = mock_dataset_with_manifest
        iom = IOManager(ds, manifest)

        revision = manifest.dataset_revision
        os.makedirs(os.path.join(manifest.cache_mgr.cache_root, revision, "other_dir"))
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test1.txt", "asdfadfsdf")
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test2.txt", "fdsfgfd")
        manifest.sweep_all_changes()

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

            assert len(glob.glob(f'{iom.push_dir}/*')) == 1
            iom.dataset.backend.set_default_configuration("test-user", "abcd", '1234')

            result = iom.pull_objects(keys=["test1.txt"])
            assert len(glob.glob(f'{iom.push_dir}/*')) == 1
            assert len(result.success) == 1
            assert len(result.failure) == 0
            assert result.success[0].object_path == obj_to_push[0].object_path

            assert os.path.isfile(obj1_target) is True
            assert os.path.isfile(obj2_target) is False
            with open(obj1_source, 'rt') as dd:
                source1 = dd.read()
            with open(obj1_target, 'rt') as dd:
                assert source1 == dd.read()

            result = iom.pull_objects(keys=["test2.txt"])
            assert len(glob.glob(f'{iom.push_dir}/*')) == 1
            assert len(result.success) == 1
            assert len(result.failure) == 0
            assert result.success[0].object_path == obj_to_push[1].object_path

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

    def test_pull_objects_all(self, mock_dataset_with_manifest):
        ds, manifest, working_dir = mock_dataset_with_manifest
        iom = IOManager(ds, manifest)

        revision = manifest.dataset_revision
        os.makedirs(os.path.join(manifest.cache_mgr.cache_root, revision, "other_dir"))
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test1.txt", "asdfadfsdf")
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test2.txt", "fdsfgfd")
        manifest.sweep_all_changes()

        obj_to_push = iom.objects_to_push()
        assert len(obj_to_push) == 2
        _, obj_id_1 = obj_to_push[0].object_path.rsplit('/', 1)
        _, obj_id_2 = obj_to_push[1].object_path.rsplit('/', 1)
        obj1_target = obj_to_push[0].object_path
        obj2_target = obj_to_push[1].object_path

        obj1_source = os.path.join('/tmp', uuid.uuid4().hex)
        obj2_source = os.path.join('/tmp', uuid.uuid4().hex)

        check_info = {obj1_target: obj1_source,
                      obj2_target: obj2_source}

        assert os.path.exists(obj1_target) is True
        assert os.path.exists(obj2_target) is True
        os.rename(obj1_target, obj1_source)
        os.rename(obj2_target, obj2_source)
        assert os.path.isfile(obj1_target) is False
        assert os.path.isfile(obj2_target) is False
        assert os.path.isfile(obj1_source) is True
        assert os.path.isfile(obj2_source) is True

        # remove data from the local file cache
        os.remove(os.path.join(manifest.cache_mgr.cache_root, manifest.dataset_revision, "test1.txt"))
        os.remove(os.path.join(manifest.cache_mgr.cache_root, manifest.dataset_revision, "test2.txt"))
        shutil.rmtree(os.path.join(manifest.cache_mgr.cache_root, 'objects'))
        os.makedirs(os.path.join(manifest.cache_mgr.cache_root, 'objects'))

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

            iom.dataset.backend.set_default_configuration("test-user", "abcd", '1234')

            result = iom.pull_all()
            assert len(result.success) == 2
            assert len(result.failure) == 0
            assert result.success[0].object_path != result.success[1].object_path
            assert result.success[0].object_path in [obj_to_push[0].object_path, obj_to_push[1].object_path]
            assert result.success[1].object_path in [obj_to_push[0].object_path, obj_to_push[1].object_path]

            assert os.path.isfile(obj1_target) is True
            assert os.path.isfile(obj2_target) is True

            for r in result.success:
                with open(check_info[r.object_path], 'rt') as dd:
                    source1 = dd.read()
                with open(r.object_path, 'rt') as dd:
                    dest1 = dd.read()
                assert source1 == dest1

    def test_pull_objects_all_partial_download(self, mock_dataset_with_manifest):
        ds, manifest, working_dir = mock_dataset_with_manifest
        iom = IOManager(ds, manifest)

        revision = manifest.dataset_revision
        os.makedirs(os.path.join(manifest.cache_mgr.cache_root, revision, "other_dir"))
        helper_append_file(manifest.cache_mgr.cache_root, revision, "other_dir/test3.txt", "1")
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test1.txt", "asdfadfsdf")
        helper_append_file(manifest.cache_mgr.cache_root, revision, "test2.txt", "fdsfgfd")
        manifest.sweep_all_changes()

        obj_to_push = iom.objects_to_push()
        assert len(obj_to_push) == 3
        _, obj_id_1 = obj_to_push[0].object_path.rsplit('/', 1)
        _, obj_id_2 = obj_to_push[1].object_path.rsplit('/', 1)
        _, obj_id_3 = obj_to_push[2].object_path.rsplit('/', 1)
        obj1_target = obj_to_push[0].object_path
        obj2_target = obj_to_push[1].object_path
        obj3_target = obj_to_push[2].object_path

        obj1_source = os.path.join('/tmp', uuid.uuid4().hex)

        assert "test3.txt" in obj_to_push[0].dataset_path

        assert os.path.exists(obj1_target) is True
        assert os.path.exists(obj2_target) is True
        assert os.path.exists(obj3_target) is True

        # Completely remove other_dir/test3.txt object
        os.remove(os.path.join(manifest.cache_mgr.cache_root, manifest.dataset_revision, "other_dir", "test3.txt"))
        os.rename(obj1_target, obj1_source)

        # Remove link for test1.txt
        os.remove(os.path.join(manifest.cache_mgr.cache_root, manifest.dataset_revision, "test1.txt"))

        assert os.path.isfile(obj1_target) is False
        assert os.path.isfile(obj2_target) is True
        assert os.path.isfile(obj3_target) is True

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

            iom.dataset.backend.set_default_configuration("test-user", "abcd", '1234')

            result = iom.pull_all()
            assert len(result.success) == 1
            assert len(result.failure) == 0
            assert result.success[0].object_path == obj1_target
            assert "test3.txt" in result.success[0].dataset_path

            assert os.path.isfile(obj1_target) is True
            assert os.path.isfile(obj2_target) is True
            assert os.path.isfile(obj3_target) is True

            filename = os.path.join(manifest.cache_mgr.cache_root, manifest.dataset_revision, "other_dir", "test3.txt")
            assert os.path.isfile(filename) is True
            with open(filename, 'rt') as dd:
                assert dd.read() == "1"

            filename = os.path.join(manifest.cache_mgr.cache_root, manifest.dataset_revision,  "test1.txt")
            assert os.path.isfile(filename) is True
            with open(filename, 'rt') as dd:
                assert dd.read() == "asdfadfsdf"

            filename = os.path.join(manifest.cache_mgr.cache_root, manifest.dataset_revision,  "test2.txt")
            assert os.path.isfile(filename) is True
            with open(filename, 'rt') as dd:
                assert dd.read() == "fdsfgfd"

            # Try pulling all again with nothing to pull
            result = iom.pull_all()
            assert len(result.success) == 0
            assert len(result.failure) == 0
            assert result.message == "Dataset already downloaded."
