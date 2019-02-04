import pytest
from aioresponses import aioresponses
import aiohttp

import os
import uuid

from gtmcore.dataset.storage import get_storage_backend
from gtmcore.dataset.storage.gigantum import GigantumObjectStore, PresignedS3Download, PresignedS3Upload
from gtmcore.fixtures.datasets import mock_dataset_with_cache_dir
from gtmcore.dataset.io import PushResult, PushObject, PullResult, PullObject
from gtmcore.dataset.manifest.eventloop import get_event_loop



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

        assert sb._object_service_endpoint(ds) == "https://api.gigantum.com/object-v1"

    def test_get_request_headers(self):
        sb = get_storage_backend("gigantum_object_v1")
        sb.set_default_configuration("test-user", "abcd", '1234')

        headers = sb._object_service_headers()

        assert headers['Authorization'] == "Bearer abcd"
        assert headers['Identity'] == "1234"
        assert headers['Accept'] == 'application/json'
        assert headers['Content-Type'] == 'application/json'

    @pytest.mark.asyncio
    async def test_presigneds3upload_get_presigned_s3_url(self, event_loop, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        sb.set_default_configuration("test-user", "abcd", '1234')
        ds = mock_dataset_with_cache_dir[0]

        object_id = "abcd1234"
        object_service_root = f"{sb._object_service_endpoint(ds)}/{ds.namespace}/{ds.name}"

        headers = sb._object_service_headers()
        upload_chunk_size = 40000
        object_details = PushObject(object_path=f"/tmp/{object_id}",
                                    revision=ds.git.repo.head.commit.hexsha,
                                    dataset_path='myfile1.txt')
        psu = PresignedS3Upload(object_service_root, headers, upload_chunk_size, object_details)

        with aioresponses() as mocked_responses:
            async with aiohttp.ClientSession() as session:
                mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                                     payload={
                                         "presigned_url": "https://dummyurl.com?params=1",
                                         "key_id": "asdfasdf",
                                         "namespace": ds.namespace,
                                         "obj_id": object_id,
                                         "dataset": ds.name
                                     },
                                     status=200)

                await psu.get_presigned_s3_url(session)

        assert psu.presigned_s3_url == "https://dummyurl.com?params=1"
        assert psu.s3_headers['x-amz-server-side-encryption-aws-kms-key-id'] == "asdfasdf"
        assert psu.skip_object is False

    @pytest.mark.asyncio
    async def test_presigneds3upload_get_presigned_s3_url_skip(self, event_loop, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        sb.set_default_configuration("test-user", "abcd", '1234')
        ds = mock_dataset_with_cache_dir[0]

        object_id = "abcd1234"
        object_service_root = f"{sb._object_service_endpoint(ds)}/{ds.namespace}/{ds.name}"

        headers = sb._object_service_headers()
        upload_chunk_size = 40000
        object_details = PushObject(object_path=f"/tmp/{object_id}",
                                    revision=ds.git.repo.head.commit.hexsha,
                                    dataset_path='myfile1.txt')
        psu = PresignedS3Upload(object_service_root, headers, upload_chunk_size, object_details)

        with aioresponses() as mocked_responses:
            async with aiohttp.ClientSession() as session:
                mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                                     payload={
                                         "presigned_url": "https://dummyurl.com?params=1",
                                         "key_id": "asdfasdf",
                                         "namespace": ds.namespace,
                                         "obj_id": object_id,
                                         "dataset": ds.name
                                     },
                                     status=403)

                await psu.get_presigned_s3_url(session)

        assert psu.presigned_s3_url == ""
        assert psu.skip_object is True

    @pytest.mark.asyncio
    async def test_presigneds3upload_get_presigned_s3_url_error(self, event_loop, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        sb.set_default_configuration("test-user", "abcd", '1234')
        ds = mock_dataset_with_cache_dir[0]

        object_id = "abcd1234"
        object_service_root = f"{sb._object_service_endpoint(ds)}/{ds.namespace}/{ds.name}"

        headers = sb._object_service_headers()
        upload_chunk_size = 40000
        object_details = PushObject(object_path=f"/tmp/{object_id}",
                                    revision=ds.git.repo.head.commit.hexsha,
                                    dataset_path='myfile1.txt')
        psu = PresignedS3Upload(object_service_root, headers, upload_chunk_size, object_details)

        with aioresponses() as mocked_responses:
            async with aiohttp.ClientSession() as session:
                mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                                     payload={
                                         "presigned_url": "https://dummyurl.com?params=1",
                                         "key_id": "asdfasdf",
                                         "namespace": ds.namespace,
                                         "obj_id": object_id,
                                         "dataset": ds.name
                                     },
                                     status=500)
                with pytest.raises(IOError):
                    await psu.get_presigned_s3_url(session)

    @pytest.mark.asyncio
    async def test_presigneds3download_get_presigned_s3_url(self, event_loop, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        sb.set_default_configuration("test-user", "abcd", '1234')
        ds = mock_dataset_with_cache_dir[0]

        object_id = "abcd1234"
        object_service_root = f"{sb._object_service_endpoint(ds)}/{ds.namespace}/{ds.name}"

        headers = sb._object_service_headers()
        download_chunk_size = 40000
        object_details = PullObject(object_path=f"/tmp/{object_id}",
                                    revision=ds.git.repo.head.commit.hexsha,
                                    dataset_path='myfile1.txt')
        psu = PresignedS3Download(object_service_root, headers, download_chunk_size, object_details)

        with aioresponses() as mocked_responses:
            async with aiohttp.ClientSession() as session:
                mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                                     payload={
                                         "presigned_url": "https://dummyurl.com?params=2",
                                         "namespace": ds.namespace,
                                         "obj_id": object_id,
                                         "dataset": ds.name
                                     },
                                     status=200)

                await psu.get_presigned_s3_url(session)

        assert psu.presigned_s3_url == "https://dummyurl.com?params=2"

    @pytest.mark.asyncio
    async def test_presigneds3download_get_presigned_s3_url_error(self, event_loop, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        sb.set_default_configuration("test-user", "abcd", '1234')
        ds = mock_dataset_with_cache_dir[0]

        object_id = "abcd1234"
        object_service_root = f"{sb._object_service_endpoint(ds)}/{ds.namespace}/{ds.name}"

        headers = sb._object_service_headers()
        download_chunk_size = 40000
        object_details = PullObject(object_path=f"/tmp/{object_id}",
                                    revision=ds.git.repo.head.commit.hexsha,
                                    dataset_path='myfile1.txt')
        psu = PresignedS3Download(object_service_root, headers, download_chunk_size, object_details)

        with aioresponses() as mocked_responses:
            async with aiohttp.ClientSession() as session:
                mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{object_id}',
                                     payload={
                                         "presigned_url": "https://dummyurl.com?params=2",
                                         "namespace": ds.namespace,
                                         "obj_id": object_id,
                                         "dataset": ds.name
                                     },
                                     status=500)
                with pytest.raises(IOError):
                    await psu.get_presigned_s3_url(session)

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

    def test_push_objects(self, mock_dataset_with_cache_dir):
        with aioresponses() as mocked_responses:
            sb = get_storage_backend("gigantum_object_v1")

            ds = mock_dataset_with_cache_dir[0]

            sb.set_default_configuration(ds.namespace, "abcd", '1234')

            obj1 = helper_write_object('asdf')
            obj2 = helper_write_object('1234')

            objects = [PushObject(object_path=obj1,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile1.txt'),
                       PushObject(object_path=obj2,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile2.txt')
                       ]

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/asdf',
                                 payload={
                                         "presigned_url": "https://dummyurl.com/asdf?params=1",
                                         "namespace": ds.namespace,
                                         "key_id": "hghghg",
                                         "obj_id": 'asdf',
                                         "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put("https://dummyurl.com/asdf?params=1",
                                 payload={},
                                 status=200)

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/1234',
                                 payload={
                                            "presigned_url": "https://dummyurl.com/1234?params=1",
                                            "namespace": ds.namespace,
                                            "key_id": "hghghg",
                                            "obj_id": '1234',
                                            "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put("https://dummyurl.com/1234?params=1",
                                 payload={},
                                 status=200)

            result = sb.push_objects(ds, objects, updater)
            assert len(result.success) == 2
            assert len(result.failure) == 0
            assert isinstance(result, PushResult) is True
            assert isinstance(result.success[0], PushObject) is True
            assert result.success[0].object_path != result.success[1].object_path
            assert result.success[0].object_path in [obj1, obj2]
            assert result.success[1].object_path in [obj1, obj2]

    def test_push_objects_with_existing(self, mock_dataset_with_cache_dir):
        with aioresponses() as mocked_responses:
            sb = get_storage_backend("gigantum_object_v1")

            ds = mock_dataset_with_cache_dir[0]

            sb.set_default_configuration(ds.namespace, "abcd", '1234')

            obj1 = helper_write_object('asdf')
            obj2 = helper_write_object('1234')

            objects = [PushObject(object_path=obj1,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile1.txt'),
                       PushObject(object_path=obj2,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile2.txt')
                       ]

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/asdf',
                                 payload={
                                         "presigned_url": "https://dummyurl.com/asdf?params=1",
                                         "namespace": ds.namespace,
                                         "key_id": "hghghg",
                                         "obj_id": 'asdf',
                                         "dataset": ds.name
                                 },
                                 status=403)

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/1234',
                                 payload={
                                            "presigned_url": "https://dummyurl.com/1234?params=1",
                                            "namespace": ds.namespace,
                                            "key_id": "hghghg",
                                            "obj_id": '1234',
                                            "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put("https://dummyurl.com/1234?params=1",
                                 payload={},
                                 status=200)

            result = sb.push_objects(ds, objects, updater)
            assert len(result.success) == 2
            assert len(result.failure) == 0
            assert isinstance(result, PushResult) is True
            assert isinstance(result.success[0], PushObject) is True
            assert result.success[0].object_path != result.success[1].object_path
            assert result.success[0].object_path in [obj1, obj2]
            assert result.success[1].object_path in [obj1, obj2]

    def test_push_objects_fail_url(self, mock_dataset_with_cache_dir):
        with aioresponses() as mocked_responses:
            sb = get_storage_backend("gigantum_object_v1")

            ds = mock_dataset_with_cache_dir[0]

            sb.set_default_configuration(ds.namespace, "abcd", '1234')

            obj1 = helper_write_object('asdf')
            obj2 = helper_write_object('1234')

            objects = [PushObject(object_path=obj1,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile1.txt'),
                       PushObject(object_path=obj2,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile2.txt')
                       ]

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/asdf',
                                 payload={
                                         "presigned_url": "https://dummyurl.com/asdf?params=1",
                                         "namespace": ds.namespace,
                                         "key_id": "hghghg",
                                         "obj_id": 'asdf',
                                         "dataset": ds.name
                                 },
                                 status=400)

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/1234',
                                 payload={
                                            "presigned_url": "https://dummyurl.com/1234?params=1",
                                            "namespace": ds.namespace,
                                            "key_id": "hghghg",
                                            "obj_id": '1234',
                                            "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put("https://dummyurl.com/1234?params=1",
                                 payload={},
                                 status=200)

            result = sb.push_objects(ds, objects, updater)
            assert len(result.success) == 1
            assert len(result.failure) == 1
            assert isinstance(result, PushResult) is True
            assert isinstance(result.success[0], PushObject) is True
            assert result.success[0].object_path == obj2
            assert result.failure[0].object_path == obj1

    def test_push_objects_fail_upload(self, mock_dataset_with_cache_dir):
        with aioresponses() as mocked_responses:
            sb = get_storage_backend("gigantum_object_v1")

            ds = mock_dataset_with_cache_dir[0]

            sb.set_default_configuration(ds.namespace, "abcd", '1234')

            obj1 = helper_write_object('asdf')
            obj2 = helper_write_object('1234')

            objects = [PushObject(object_path=obj1,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile1.txt'),
                       PushObject(object_path=obj2,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile2.txt')
                       ]

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/asdf',
                                 payload={
                                         "presigned_url": "https://dummyurl.com/asdf?params=1",
                                         "namespace": ds.namespace,
                                         "key_id": "hghghg",
                                         "obj_id": 'asdf',
                                         "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put("https://dummyurl.com/asdf?params=1",
                                 payload={},
                                 status=200)

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/1234',
                                 payload={
                                            "presigned_url": "https://dummyurl.com/1234?params=1",
                                            "namespace": ds.namespace,
                                            "key_id": "hghghg",
                                            "obj_id": '1234',
                                            "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put("https://dummyurl.com/1234?params=1",
                                 payload={},
                                 status=500)

            result = sb.push_objects(ds, objects, updater)
            assert len(result.success) == 1
            assert len(result.failure) == 1
            assert isinstance(result, PushResult) is True
            assert isinstance(result.success[0], PushObject) is True
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

    def test_pull_objects(self, mock_dataset_with_cache_dir):
        with aioresponses() as mocked_responses:
            sb = get_storage_backend("gigantum_object_v1")
            ds = mock_dataset_with_cache_dir[0]
            sb.set_default_configuration(ds.namespace, "abcd", '1234')

            obj1 = helper_write_object('asdf')
            obj2 = helper_write_object('1234')

            obj_id_1 = uuid.uuid4().hex
            obj_id_2 = uuid.uuid4().hex
            obj1_target = f'/tmp/{obj_id_1}'
            obj2_target = f'/tmp/{obj_id_2}'

            check_info = {obj1_target: obj1,
                          obj2_target: obj2}

            objects = [PullObject(object_path=obj1_target,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile1.txt'),
                       PullObject(object_path=obj2_target,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile2.txt')
                       ]

            mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj_id_1}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj_id_1}?params=1",
                                         "namespace": ds.namespace,
                                         "obj_id": obj_id_1,
                                         "dataset": ds.name
                                 },
                                 status=200)

            with open(obj1, 'rb') as data1:
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

            with open(obj2, 'rb') as data2:
                mocked_responses.get(f"https://dummyurl.com/{obj_id_2}?params=1",
                                     body=data2.read(), status=200,
                                     content_type='application/octet-stream')

            result = sb.pull_objects(ds, objects, updater)
            assert len(result.success) == 2
            assert len(result.failure) == 0
            assert isinstance(result, PullResult) is True
            assert isinstance(result.success[0], PullObject) is True
            assert result.success[0].object_path != result.success[1].object_path
            assert result.success[0].object_path in [obj1_target, obj2_target]
            assert result.success[1].object_path in [obj1_target, obj2_target]

            for r in result.success:
                with open(check_info[r.object_path], 'rt') as dd:
                    source1 = dd.read()
                with open(r.object_path, 'rt') as dd:
                    dest1 = dd.read()
                assert source1 == dest1

    def test_pull_objects_fail_download(self, mock_dataset_with_cache_dir):
        with aioresponses() as mocked_responses:
            sb = get_storage_backend("gigantum_object_v1")
            ds = mock_dataset_with_cache_dir[0]
            sb.set_default_configuration(ds.namespace, "abcd", '1234')

            obj1 = helper_write_object('asdf')
            obj2 = helper_write_object('1234')

            obj_id_1 = uuid.uuid4().hex
            obj_id_2 = uuid.uuid4().hex
            obj1_target = f'/tmp/{obj_id_1}'
            obj2_target = f'/tmp/{obj_id_2}'

            check_info = {obj1_target: obj1,
                          obj2_target: obj2}

            objects = [PullObject(object_path=obj1_target,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile1.txt'),
                       PullObject(object_path=obj2_target,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile2.txt')
                       ]

            mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj_id_1}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj_id_1}?params=1",
                                         "namespace": ds.namespace,
                                         "obj_id": obj_id_1,
                                         "dataset": ds.name
                                 },
                                 status=200)

            mocked_responses.get(f"https://dummyurl.com/{obj_id_1}?params=1", status=500,
                                 content_type='application/octet-stream')

            mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj_id_2}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj_id_2}?params=1",
                                         "namespace": ds.namespace,
                                         "obj_id": obj_id_2,
                                         "dataset": ds.name
                                 },
                                 status=200)

            with open(obj2, 'rb') as data2:
                mocked_responses.get(f"https://dummyurl.com/{obj_id_2}?params=1",
                                     body=data2.read(), status=200,
                                     content_type='application/octet-stream')

            result = sb.pull_objects(ds, objects, updater)
            assert len(result.success) == 1
            assert len(result.failure) == 1
            assert isinstance(result, PullResult) is True
            assert isinstance(result.success[0], PullObject) is True
            assert result.success[0].object_path == obj2_target
            assert result.failure[0].object_path == obj1_target

            assert os.path.isfile(result.success[0].object_path) is True
            assert os.path.isfile(result.failure[0].object_path) is False

            with open(check_info[result.success[0].object_path], 'rt') as dd:
                source1 = dd.read()
            with open(result.success[0].object_path, 'rt') as dd:
                dest1 = dd.read()
            assert source1 == dest1

    def test_pull_objects_fail_signing(self, mock_dataset_with_cache_dir):
        with aioresponses() as mocked_responses:
            sb = get_storage_backend("gigantum_object_v1")
            ds = mock_dataset_with_cache_dir[0]
            sb.set_default_configuration(ds.namespace, "abcd", '1234')

            obj1 = helper_write_object('asdf')
            obj2 = helper_write_object('1234')

            obj_id_1 = uuid.uuid4().hex
            obj_id_2 = uuid.uuid4().hex
            obj1_target = f'/tmp/{obj_id_1}'
            obj2_target = f'/tmp/{obj_id_2}'

            check_info = {obj1_target: obj1,
                          obj2_target: obj2}

            objects = [PullObject(object_path=obj1_target,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile1.txt'),
                       PullObject(object_path=obj2_target,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile2.txt')
                       ]

            mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj_id_1}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj_id_1}?params=1",
                                         "namespace": ds.namespace,
                                         "obj_id": obj_id_1,
                                         "dataset": ds.name
                                 },
                                 status=400)

            mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj_id_2}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj_id_2}?params=1",
                                         "namespace": ds.namespace,
                                         "obj_id": obj_id_2,
                                         "dataset": ds.name
                                 },
                                 status=200)

            with open(obj2, 'rb') as data2:
                mocked_responses.get(f"https://dummyurl.com/{obj_id_2}?params=1",
                                     body=data2.read(), status=200,
                                     content_type='application/octet-stream')

            result = sb.pull_objects(ds, objects, updater)
            assert len(result.success) == 1
            assert len(result.failure) == 1
            assert isinstance(result, PullResult) is True
            assert isinstance(result.success[0], PullObject) is True
            assert result.success[0].object_path == obj2_target
            assert result.failure[0].object_path == obj1_target

            assert os.path.isfile(result.success[0].object_path) is True
            assert os.path.isfile(result.failure[0].object_path) is False

            with open(check_info[result.success[0].object_path], 'rt') as dd:
                source1 = dd.read()
            with open(result.success[0].object_path, 'rt') as dd:
                dest1 = dd.read()
            assert source1 == dest1

    def test_finalize_pull(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]

        def check_updater(msg):
            assert msg == f"Done pulling objects from tester/dataset-1"

        sb.finalize_pull(ds, check_updater)
