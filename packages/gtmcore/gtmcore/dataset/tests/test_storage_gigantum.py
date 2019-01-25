import pytest
import responses
import os
import uuid

from gtmcore.exceptions import GigantumException
from gtmcore.dataset.storage import get_storage_backend
from gtmcore.dataset.storage.gigantum import GigantumObjectStore
from gtmcore.fixtures.datasets import mock_dataset_with_cache_dir
from gtmcore.dataset.io import PushResult, PushObject, PullResult, PullObject


def helper_write_object(object_id):
    object_file = os.path.join('/tmp', object_id)
    with open(object_file, 'wt') as temp:
        temp.write(f'dummy data: {object_id}')

    return object_file


def updater(msg):
    print(msg)


class TestStorageBackendGigantum(object):
    def test_get_storage_backend(self):
        sb = get_storage_backend("gigantum_object_v1")

        assert isinstance(sb, GigantumObjectStore)

    def test_get_service_endpoint(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]

        assert sb._get_service_endpoint(ds) == "https://api.gigantum.com/object-v1"

    def test_get_request_headers(self):
        sb = get_storage_backend("gigantum_object_v1")
        sb.set_default_configuration("test-user", "abcd", '1234')

        headers = sb._get_request_headers()

        assert headers['Authorization'] == "Bearer abcd"
        assert headers['Identity'] == "1234"
        assert headers['Accept'] == 'application/json'

    @responses.activate
    def test_gen_push_url(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]
        object_id = "abcd1234"

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={
                              "presigned_url": "https://dummyurl.com?params=1",
                              "key_id": "asdfasdf",
                              "namespace": ds.namespace,
                              "obj_id": object_id,
                              "dataset": ds.name
                      },
                      status=200)

        presigned_url, encryption_key = sb._gen_push_url(ds, object_id)

        assert presigned_url == "https://dummyurl.com?params=1"
        assert encryption_key == "asdfasdf"

    @responses.activate
    def test_gen_push_url_backoff(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]
        object_id = "abcd1234"

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={
                              "presigned_url": "https://dummyurl.com?params=1",
                              "key_id": "asdfasdf",
                              "namespace": ds.namespace,
                              "obj_id": object_id,
                              "dataset": ds.name
                      },
                      status=200)

        presigned_url, encryption_key = sb._gen_push_url(ds, object_id)

        assert presigned_url == "https://dummyurl.com?params=1"
        assert encryption_key == "asdfasdf"

    @responses.activate
    def test_gen_push_url_fail(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]
        object_id = "abcd1234"

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        with pytest.raises(IOError):
            sb._gen_push_url(ds, object_id)

    @responses.activate
    def test_gen_pull_url(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]
        object_id = "abcd1234"

        responses.add(responses.GET, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={
                              "presigned_url": "https://dummyurl.com?params=1",
                              "namespace": ds.namespace,
                              "obj_id": object_id,
                              "dataset": ds.name
                      },
                      status=200)

        assert sb._gen_pull_url(ds, object_id) == "https://dummyurl.com?params=1"

    @responses.activate
    def test_gen_push_url_backoff(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]
        object_id = "abcd1234"

        responses.add(responses.GET, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        responses.add(responses.GET, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        responses.add(responses.GET, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        responses.add(responses.GET, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={
                              "presigned_url": "https://dummyurl.com?params=1",
                              "namespace": ds.namespace,
                              "obj_id": object_id,
                              "dataset": ds.name
                      },
                      status=200)

        assert sb._gen_pull_url(ds, object_id) == "https://dummyurl.com?params=1"

    @responses.activate
    def test_gen_push_url_fail(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]
        object_id = "abcd1234"

        responses.add(responses.GET, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        responses.add(responses.GET, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        responses.add(responses.GET, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        responses.add(responses.GET, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        responses.add(responses.GET, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                      json={},
                      status=400)

        with pytest.raises(IOError):
            sb._gen_pull_url(ds, object_id)

    def test_prepare_push(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]

        with pytest.raises(ValueError):
            sb.prepare_push(ds, [], updater)

        sb.configuration['username'] = "test-user"
        with pytest.raises(ValueError):
            sb.prepare_push(ds, [], updater)

        sb.configuration['gigantum_bearer_token'] = "asdf"
        with pytest.raises(ValueError):
            sb.prepare_push(ds, [], updater)

        sb.configuration['gigantum_id_token'] = "1234"
        sb.prepare_push(ds, [], updater)

    def test_prepare_push_errors(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]

        sb.set_default_configuration("test-user", "abcd", '1234')
        sb.prepare_push(ds, [], updater)

    @responses.activate
    def test_push_objects(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]
        obj1 = helper_write_object('asdf')
        obj2 = helper_write_object('1234')

        objects = [PushObject(object_path=obj1,
                              revision=ds.git.repo.head.commit.hexsha,
                              dataset_path='myfile1.txt'),
                   PushObject(object_path=obj2,
                              revision=ds.git.repo.head.commit.hexsha,
                              dataset_path='myfile2.txt')
                   ]

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/asdf',
                      json={
                              "presigned_url": "https://dummyurl.com/asdf?params=1",
                              "namespace": ds.namespace,
                              "key_id": "hghghg",
                              "obj_id": 'asdf',
                              "dataset": ds.name
                      },
                      status=200)
        responses.add(responses.PUT, "https://dummyurl.com/asdf?params=1",
                      json={},
                      status=200)

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/1234',
                      json={
                              "presigned_url": "https://dummyurl.com/1234?params=1",
                              "namespace": ds.namespace,
                              "key_id": "hghghg",
                              "obj_id": '1234',
                              "dataset": ds.name
                      },
                      status=200)
        responses.add(responses.PUT, "https://dummyurl.com/1234?params=1",
                      json={},
                      status=200)

        result = sb.push_objects(ds, objects, updater)
        assert len(result.success) == 2
        assert len(result.failure) == 0
        assert isinstance(result, PushResult) is True
        assert isinstance(result.success[0], PushObject) is True
        assert result.success[0].object_path == obj1
        assert result.success[1].object_path == obj2

    @responses.activate
    def test_push_objects_fail_url(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]
        obj1 = helper_write_object('asdf')
        obj2 = helper_write_object('1234')

        objects = [PushObject(object_path=obj1,
                              revision=ds.git.repo.head.commit.hexsha,
                              dataset_path='myfile1.txt'),
                   PushObject(object_path=obj2,
                              revision=ds.git.repo.head.commit.hexsha,
                              dataset_path='myfile2.txt')
                   ]

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/asdf',
                      json={},
                      status=400)
        responses.add(responses.PUT, "https://dummyurl.com/asdf?params=1",
                      json={},
                      status=200)

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/1234',
                      json={
                              "presigned_url": "https://dummyurl.com/1234?params=1",
                              "namespace": ds.namespace,
                              "key_id": "hghghg",
                              "obj_id": '1234',
                              "dataset": ds.name
                      },
                      status=200)
        responses.add(responses.PUT, "https://dummyurl.com/1234?params=1",
                      json={},
                      status=200)

        result = sb.push_objects(ds, objects, updater)
        assert len(result.success) == 1
        assert len(result.failure) == 1
        assert result.failure[0].object_path == obj1
        assert result.success[0].object_path == obj2

    @responses.activate
    def test_push_objects_fail_upload(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]
        obj1 = helper_write_object('asdf')
        obj2 = helper_write_object('1234')

        objects = [PushObject(object_path=obj1,
                              revision=ds.git.repo.head.commit.hexsha,
                              dataset_path='myfile1.txt'),
                   PushObject(object_path=obj2,
                              revision=ds.git.repo.head.commit.hexsha,
                              dataset_path='myfile2.txt')
                   ]

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/asdf',
                      json={
                              "presigned_url": "https://dummyurl.com/asdf?params=1",
                              "namespace": ds.namespace,
                              "key_id": "hghghg",
                              "obj_id": 'asdf',
                              "dataset": ds.name
                      },
                      status=200)
        responses.add(responses.PUT, "https://dummyurl.com/asdf?params=1",
                      json={},
                      status=200)

        responses.add(responses.PUT, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/1234',
                      json={
                              "presigned_url": "https://dummyurl.com/1234?params=1",
                              "namespace": ds.namespace,
                              "key_id": "hghghg",
                              "obj_id": '1234',
                              "dataset": ds.name
                      },
                      status=200)
        responses.add(responses.PUT, "https://dummyurl.com/1234?params=1",
                      json={},
                      status=400)

        result = sb.push_objects(ds, objects, updater)
        assert len(result.success) == 1
        assert len(result.failure) == 1
        assert result.success[0].object_path == obj1
        assert result.failure[0].object_path == obj2

    def test_finalize_push(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]

        def check_updater(msg):
            assert msg == f"Done pushing objects to tester/dataset-1"

        sb.finalize_push(ds, check_updater)

    def test_prepare_pull(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]

        with pytest.raises(ValueError):
            sb.prepare_pull(ds, [], updater)

        sb.configuration['username'] = "test-user"
        with pytest.raises(ValueError):
            sb.prepare_pull(ds, [], updater)

        sb.configuration['gigantum_bearer_token'] = "asdf"
        with pytest.raises(ValueError):
            sb.prepare_pull(ds, [], updater)

        sb.configuration['gigantum_id_token'] = "1234"
        sb.prepare_pull(ds, [], updater)

    @responses.activate
    def test_pull_objects(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]
        obj1 = helper_write_object('asdf')
        obj2 = helper_write_object('1234')

        obj_id_1 = uuid.uuid4().hex
        obj_id_2 = uuid.uuid4().hex
        obj1_target = f'/tmp/{obj_id_1}'
        obj2_target = f'/tmp/{obj_id_2}'

        objects = [PullObject(object_path=obj1_target,
                              revision=ds.git.repo.head.commit.hexsha,
                              dataset_path='myfile1.txt'),
                   PullObject(object_path=obj2_target,
                              revision=ds.git.repo.head.commit.hexsha,
                              dataset_path='myfile2.txt')
                   ]

        responses.add(responses.GET, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj_id_1}',
                      json={
                              "presigned_url": f"https://dummyurl.com/{obj_id_1}?params=1",
                              "namespace": ds.namespace,
                              "obj_id": obj_id_1,
                              "dataset": ds.name
                      },
                      status=200)

        with open(obj1, 'rb') as data1:
            responses.add(responses.GET, f"https://dummyurl.com/{obj_id_1}?params=1",
                          body=data1.read(), status=200,
                          content_type='application/octet-stream',
                          stream=True)

        responses.add(responses.GET, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj_id_2}',
                      json={
                              "presigned_url": f"https://dummyurl.com/{obj_id_2}?params=1",
                              "namespace": ds.namespace,
                              "obj_id": obj_id_2,
                              "dataset": ds.name
                      },
                      status=200)

        with open(obj2, 'rb') as data2:
            responses.add(responses.GET, f"https://dummyurl.com/{obj_id_2}?params=1",
                          body=data2.read(), status=200,
                          content_type='application/octet-stream',
                          stream=True)

        result = sb.pull_objects(ds, objects, updater)
        assert len(result.success) == 2
        assert len(result.failure) == 0
        assert isinstance(result, PullResult) is True
        assert isinstance(result.success[0], PullObject) is True
        assert result.success[0].object_path == obj1_target
        assert result.success[1].object_path == obj2_target

        with open(obj1, 'rt') as dd:
            source1 = dd.read()
        with open(obj2, 'rt') as dd:
            source2 = dd.read()
        with open(obj1_target, 'rt') as dd:
            assert source1 == dd.read()
        with open(obj2_target, 'rt') as dd:
            assert source2 == dd.read()

    @responses.activate
    def test_pull_objects_fail_download(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]
        obj1 = helper_write_object('asdf')
        obj2 = helper_write_object('1234')

        obj_id_1 = uuid.uuid4().hex
        obj_id_2 = uuid.uuid4().hex
        obj1_target = f'/tmp/{obj_id_1}'
        obj2_target = f'/tmp/{obj_id_2}'

        objects = [PullObject(object_path=obj1_target,
                              revision=ds.git.repo.head.commit.hexsha,
                              dataset_path='myfile1.txt'),
                   PullObject(object_path=obj2_target,
                              revision=ds.git.repo.head.commit.hexsha,
                              dataset_path='myfile2.txt')
                   ]

        responses.add(responses.GET, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj_id_1}',
                      json={
                              "presigned_url": f"https://dummyurl.com/{obj_id_1}?params=1",
                              "namespace": ds.namespace,
                              "obj_id": obj_id_1,
                              "dataset": ds.name
                      },
                      status=200)

        with open(obj1, 'rb') as data1:
            responses.add(responses.GET, f"https://dummyurl.com/{obj_id_1}?params=1",
                          body=data1.read(), status=200,
                          content_type='application/octet-stream',
                          stream=True)

        responses.add(responses.GET, f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj_id_2}',
                      json={
                              "presigned_url": f"https://dummyurl.com/{obj_id_2}?params=1",
                              "namespace": ds.namespace,
                              "obj_id": obj_id_2,
                              "dataset": ds.name
                      },
                      status=200)

        with open(obj2, 'rb') as data2:
            responses.add(responses.GET, f"https://dummyurl.com/{obj_id_2}?params=1",
                          json={}, status=400,
                          content_type='application/octet-stream')

        result = sb.pull_objects(ds, objects, updater)
        assert len(result.success) == 1
        assert len(result.failure) == 1
        assert result.success[0].object_path == obj1_target
        assert result.failure[0].object_path == obj2_target

        with open(obj1, 'rt') as dd:
            source1 = dd.read()
        with open(obj1_target, 'rt') as dd:
            assert source1 == dd.read()

        assert os.path.exists(obj1_target) is True
        assert os.path.exists(obj2_target) is False

    def test_finalize_pull(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]

        def check_updater(msg):
            assert msg == f"Done pulling objects from tester/dataset-1"

        sb.finalize_pull(ds, check_updater)
