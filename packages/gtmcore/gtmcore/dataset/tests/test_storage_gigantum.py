import pytest
from aioresponses import aioresponses
import aiohttp
import snappy
import shutil

import os
import uuid

from gtmcore.dataset.storage import get_storage_backend
from gtmcore.dataset.storage.gigantum import GigantumObjectStore, PresignedS3Download, PresignedS3Upload
from gtmcore.fixtures.datasets import mock_dataset_with_cache_dir, helper_compress_file
from gtmcore.dataset.io import PushResult, PushObject, PullResult, PullObject


def helper_write_object(directory, object_id, contents):
    object_file = os.path.join(directory, object_id)
    with open(object_file, 'wt') as temp:
        temp.write(f'dummy data: {contents}')

    return object_file


def updater(msg):
    print(msg)


@pytest.fixture()
def temp_directories():
    object_dir = f'/tmp/{uuid.uuid4().hex}'
    compressed_dir = f'/tmp/{uuid.uuid4().hex}'
    os.makedirs(object_dir)
    os.makedirs(compressed_dir)
    yield object_dir, compressed_dir,
    shutil.rmtree(object_dir)
    shutil.rmtree(compressed_dir)


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

    def test_client_should_dedup_on_push(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]

        assert sb.client_should_dedup_on_push is True

    def test_backend_config(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]

        assert sb.is_configured is False

        missing = sb.missing_configuration
        assert len(missing) == 3
        assert missing[0]['parameter'] == "username"

        # Configure 1 param
        sb.configuration['username'] = "test"

        assert sb.is_configured is False
        missing = sb.missing_configuration
        assert len(missing) == 2
        assert missing[0]['parameter'] == "gigantum_bearer_token"

        # Configure all
        sb.set_default_configuration('test', 'asdf', '1234')
        assert sb.is_configured is True

        assert sb.confirm_configuration(ds, lambda x: print(x)) is None

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

    def test_push_objects(self, mock_dataset_with_cache_dir, temp_directories):
        with aioresponses() as mocked_responses:
            sb = get_storage_backend("gigantum_object_v1")

            ds = mock_dataset_with_cache_dir[0]

            sb.set_default_configuration(ds.namespace, "abcd", '1234')

            object_dir, compressed_dir = temp_directories

            obj1_id = uuid.uuid4().hex
            obj2_id = uuid.uuid4().hex

            obj1_src_path = helper_write_object(object_dir, obj1_id, 'abcd')
            obj2_src_path = helper_write_object(object_dir, obj2_id, '1234')
            assert os.path.isfile(obj1_src_path) is True
            assert os.path.isfile(obj2_src_path) is True

            objects = [PushObject(object_path=obj1_src_path,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile1.txt'),
                       PushObject(object_path=obj2_src_path,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile2.txt')
                       ]

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj1_id}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj1_id}?params=1",
                                         "namespace": ds.namespace,
                                         "key_id": "hghghg",
                                         "obj_id": obj1_id,
                                         "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put(f"https://dummyurl.com/{obj1_id}?params=1",
                                 payload={},
                                 status=200)

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj2_id}',
                                 payload={
                                            "presigned_url": f"https://dummyurl.com/{obj2_id}?params=1",
                                            "namespace": ds.namespace,
                                            "key_id": "hghghg",
                                            "obj_id": obj2_id,
                                            "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put(f"https://dummyurl.com/{obj2_id}?params=1",
                                 payload={},
                                 status=200)

            result = sb.push_objects(ds, objects, updater)
            assert len(result.success) == 2
            assert len(result.failure) == 0
            assert isinstance(result, PushResult) is True
            assert isinstance(result.success[0], PushObject) is True
            assert result.success[0].object_path != result.success[1].object_path
            assert result.success[0].object_path in [obj1_src_path, obj2_src_path]
            assert result.success[1].object_path in [obj1_src_path, obj2_src_path]

    def test_push_objects_with_existing(self, mock_dataset_with_cache_dir, temp_directories):
        with aioresponses() as mocked_responses:
            sb = get_storage_backend("gigantum_object_v1")

            ds = mock_dataset_with_cache_dir[0]

            sb.set_default_configuration(ds.namespace, "abcd", '1234')

            object_dir, compressed_dir = temp_directories

            obj1_id = uuid.uuid4().hex
            obj2_id = uuid.uuid4().hex

            obj1_src_path = helper_write_object(object_dir, obj1_id, 'abcd')
            obj2_src_path = helper_write_object(object_dir, obj2_id, '1234')
            assert os.path.isfile(obj1_src_path) is True
            assert os.path.isfile(obj2_src_path) is True

            objects = [PushObject(object_path=obj1_src_path,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile1.txt'),
                       PushObject(object_path=obj2_src_path,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile2.txt')
                       ]

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj1_id}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj1_id}?params=1",
                                         "namespace": ds.namespace,
                                         "key_id": "hghghg",
                                         "obj_id": obj1_id,
                                         "dataset": ds.name
                                 },
                                 status=403)

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj2_id}',
                                 payload={
                                            "presigned_url": f"https://dummyurl.com/{obj2_id}?params=1",
                                            "namespace": ds.namespace,
                                            "key_id": "hghghg",
                                            "obj_id": obj2_id,
                                            "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put(f"https://dummyurl.com/{obj2_id}?params=1",
                                 payload={},
                                 status=200)

            result = sb.push_objects(ds, objects, updater)
            assert len(result.success) == 2
            assert len(result.failure) == 0
            assert isinstance(result, PushResult) is True
            assert isinstance(result.success[0], PushObject) is True
            assert result.success[0].object_path != result.success[1].object_path
            assert result.success[0].object_path in [obj1_src_path, obj2_src_path]
            assert result.success[1].object_path in [obj1_src_path, obj2_src_path]

    def test_push_objects_fail_url(self, mock_dataset_with_cache_dir, temp_directories):
        with aioresponses() as mocked_responses:
            sb = get_storage_backend("gigantum_object_v1")

            ds = mock_dataset_with_cache_dir[0]

            sb.set_default_configuration(ds.namespace, "abcd", '1234')

            object_dir, compressed_dir = temp_directories

            obj1_id = uuid.uuid4().hex
            obj2_id = uuid.uuid4().hex

            obj1_src_path = helper_write_object(object_dir, obj1_id, 'abcd')
            obj2_src_path = helper_write_object(object_dir, obj2_id, '1234')
            assert os.path.isfile(obj1_src_path) is True
            assert os.path.isfile(obj2_src_path) is True

            objects = [PushObject(object_path=obj1_src_path,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile1.txt'),
                       PushObject(object_path=obj2_src_path,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile2.txt')
                       ]

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj1_id}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj1_id}?params=1",
                                         "namespace": ds.namespace,
                                         "key_id": "hghghg",
                                         "obj_id": obj1_id,
                                         "dataset": ds.name
                                 },
                                 status=400)

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj2_id}',
                                 payload={
                                            "presigned_url": f"https://dummyurl.com/{obj2_id}?params=1",
                                            "namespace": ds.namespace,
                                            "key_id": "hghghg",
                                            "obj_id": obj2_id,
                                            "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put(f"https://dummyurl.com/{obj2_id}?params=1",
                                 payload={},
                                 status=200)

            result = sb.push_objects(ds, objects, updater)
            assert len(result.success) == 1
            assert len(result.failure) == 1
            assert isinstance(result, PushResult) is True
            assert isinstance(result.success[0], PushObject) is True
            assert result.success[0].object_path == obj2_src_path
            assert result.failure[0].object_path == obj1_src_path

    def test_push_objects_fail_upload(self, mock_dataset_with_cache_dir, temp_directories):
        with aioresponses() as mocked_responses:
            sb = get_storage_backend("gigantum_object_v1")

            ds = mock_dataset_with_cache_dir[0]

            sb.set_default_configuration(ds.namespace, "abcd", '1234')

            object_dir, compressed_dir = temp_directories

            obj1_id = uuid.uuid4().hex
            obj2_id = uuid.uuid4().hex

            obj1_src_path = helper_write_object(object_dir, obj1_id, 'abcd')
            obj2_src_path = helper_write_object(object_dir, obj2_id, '1234')
            assert os.path.isfile(obj1_src_path) is True
            assert os.path.isfile(obj2_src_path) is True

            objects = [PushObject(object_path=obj1_src_path,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile1.txt'),
                       PushObject(object_path=obj2_src_path,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile2.txt')
                       ]

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj1_id}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj1_id}?params=1",
                                         "namespace": ds.namespace,
                                         "key_id": "hghghg",
                                         "obj_id": obj1_id,
                                         "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put(f"https://dummyurl.com/{obj1_id}?params=1",
                                 payload={},
                                 status=200)

            mocked_responses.put(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj2_id}',
                                 payload={
                                            "presigned_url": f"https://dummyurl.com/{obj2_id}?params=1",
                                            "namespace": ds.namespace,
                                            "key_id": "hghghg",
                                            "obj_id": obj2_id,
                                            "dataset": ds.name
                                 },
                                 status=200)
            mocked_responses.put(f"https://dummyurl.com/{obj2_id}?params=1",
                                 payload={},
                                 status=500)

            result = sb.push_objects(ds, objects, updater)
            assert len(result.success) == 1
            assert len(result.failure) == 1
            assert isinstance(result, PushResult) is True
            assert isinstance(result.success[0], PushObject) is True
            assert result.success[0].object_path == obj1_src_path
            assert result.failure[0].object_path == obj2_src_path

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

    def test_pull_objects(self, mock_dataset_with_cache_dir, temp_directories):
        with aioresponses() as mocked_responses:
            sb = get_storage_backend("gigantum_object_v1")
            ds = mock_dataset_with_cache_dir[0]
            sb.set_default_configuration(ds.namespace, "abcd", '1234')

            object_dir, compressed_dir = temp_directories

            obj1_id = uuid.uuid4().hex
            obj2_id = uuid.uuid4().hex

            obj1_src_path = helper_write_object(object_dir, obj1_id, 'abcd')
            obj2_src_path = helper_write_object(object_dir, obj2_id, '1234')
            assert os.path.isfile(obj1_src_path) is True
            assert os.path.isfile(obj2_src_path) is True

            obj1_compressed_path = os.path.join(compressed_dir, obj1_id)
            obj2_compressed_path = os.path.join(compressed_dir, obj2_id)
            helper_compress_file(obj1_src_path, obj1_compressed_path)
            helper_compress_file(obj2_src_path, obj2_compressed_path)

            assert os.path.isfile(obj1_src_path) is False
            assert os.path.isfile(obj2_src_path) is False
            assert os.path.isfile(obj1_compressed_path) is True
            assert os.path.isfile(obj2_compressed_path) is True

            check_info = {obj1_src_path: obj1_compressed_path,
                          obj2_src_path: obj2_compressed_path}

            objects = [PullObject(object_path=obj1_src_path,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile1.txt'),
                       PullObject(object_path=obj2_src_path,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile2.txt')
                       ]

            mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj1_id}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj1_id}?params=1",
                                         "namespace": ds.namespace,
                                         "obj_id": obj1_id,
                                         "dataset": ds.name
                                 },
                                 status=200)

            with open(obj1_compressed_path, 'rb') as data1:
                mocked_responses.get(f"https://dummyurl.com/{obj1_id}?params=1",
                                     body=data1.read(), status=200,
                                     content_type='application/octet-stream')

            mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj2_id}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj2_id}?params=1",
                                         "namespace": ds.namespace,
                                         "obj_id": obj2_id,
                                         "dataset": ds.name
                                 },
                                 status=200)

            with open(obj2_compressed_path, 'rb') as data2:
                mocked_responses.get(f"https://dummyurl.com/{obj2_id}?params=1",
                                     body=data2.read(), status=200,
                                     content_type='application/octet-stream')

            result = sb.pull_objects(ds, objects, updater)
            assert len(result.success) == 2
            assert len(result.failure) == 0
            assert isinstance(result, PullResult) is True
            assert isinstance(result.success[0], PullObject) is True
            assert result.success[0].object_path != result.success[1].object_path
            assert result.success[0].object_path in [obj1_src_path, obj2_src_path]
            assert result.success[1].object_path in [obj1_src_path, obj2_src_path]

            assert os.path.isfile(obj1_src_path) is True
            assert os.path.isfile(obj2_src_path) is True

            decompressor = snappy.StreamDecompressor()
            for r in result.success:
                with open(check_info[r.object_path], 'rb') as dd:
                    source1 = decompressor.decompress(dd.read())
                    source1 += decompressor.flush()
                with open(r.object_path, 'rt') as dd:
                    dest1 = dd.read()
                assert source1.decode("utf-8") == dest1

    def test_pull_objects_fail_download(self, mock_dataset_with_cache_dir, temp_directories):
        with aioresponses() as mocked_responses:
            sb = get_storage_backend("gigantum_object_v1")
            ds = mock_dataset_with_cache_dir[0]
            sb.set_default_configuration(ds.namespace, "abcd", '1234')

            object_dir, compressed_dir = temp_directories

            obj1_id = uuid.uuid4().hex
            obj2_id = uuid.uuid4().hex

            obj1_src_path = helper_write_object(object_dir, obj1_id, 'abcd')
            obj2_src_path = helper_write_object(object_dir, obj2_id, '1234')
            assert os.path.isfile(obj1_src_path) is True
            assert os.path.isfile(obj2_src_path) is True

            obj1_compressed_path = os.path.join(compressed_dir, obj1_id)
            obj2_compressed_path = os.path.join(compressed_dir, obj2_id)
            helper_compress_file(obj1_src_path, obj1_compressed_path)
            helper_compress_file(obj2_src_path, obj2_compressed_path)

            assert os.path.isfile(obj1_src_path) is False
            assert os.path.isfile(obj2_src_path) is False
            assert os.path.isfile(obj1_compressed_path) is True
            assert os.path.isfile(obj2_compressed_path) is True

            check_info = {obj1_src_path: obj1_compressed_path,
                          obj2_src_path: obj2_compressed_path}

            objects = [PullObject(object_path=obj1_src_path,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile1.txt'),
                       PullObject(object_path=obj2_src_path,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile2.txt')
                       ]

            mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj1_id}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj1_id}?params=1",
                                         "namespace": ds.namespace,
                                         "obj_id": obj1_id,
                                         "dataset": ds.name
                                 },
                                 status=200)

            mocked_responses.get(f"https://dummyurl.com/{obj1_id}?params=1", status=500,
                                 content_type='application/octet-stream')

            mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj2_id}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj2_id}?params=1",
                                         "namespace": ds.namespace,
                                         "obj_id": obj2_id,
                                         "dataset": ds.name
                                 },
                                 status=200)

            with open(obj2_compressed_path, 'rb') as data2:
                mocked_responses.get(f"https://dummyurl.com/{obj2_id}?params=1",
                                     body=data2.read(), status=200,
                                     content_type='application/octet-stream')

            result = sb.pull_objects(ds, objects, updater)
            assert len(result.success) == 1
            assert len(result.failure) == 1
            assert isinstance(result, PullResult) is True
            assert isinstance(result.success[0], PullObject) is True
            assert result.success[0].object_path == obj2_src_path
            assert result.failure[0].object_path == obj1_src_path

            assert os.path.isfile(result.success[0].object_path) is True
            assert os.path.isfile(result.failure[0].object_path) is False

            decompressor = snappy.StreamDecompressor()
            with open(check_info[result.success[0].object_path], 'rb') as dd:
                source1 = decompressor.decompress(dd.read())
                source1 += decompressor.flush()
            with open(result.success[0].object_path, 'rt') as dd:
                dest1 = dd.read()
            assert source1.decode("utf-8") == dest1

    def test_pull_objects_fail_signing(self, mock_dataset_with_cache_dir, temp_directories):
        with aioresponses() as mocked_responses:
            sb = get_storage_backend("gigantum_object_v1")
            ds = mock_dataset_with_cache_dir[0]
            sb.set_default_configuration(ds.namespace, "abcd", '1234')

            object_dir, compressed_dir = temp_directories

            obj1_id = uuid.uuid4().hex
            obj2_id = uuid.uuid4().hex

            obj1_src_path = helper_write_object(object_dir, obj1_id, 'abcd')
            obj2_src_path = helper_write_object(object_dir, obj2_id, '1234')
            assert os.path.isfile(obj1_src_path) is True
            assert os.path.isfile(obj2_src_path) is True

            obj1_compressed_path = os.path.join(compressed_dir, obj1_id)
            obj2_compressed_path = os.path.join(compressed_dir, obj2_id)
            helper_compress_file(obj1_src_path, obj1_compressed_path)
            helper_compress_file(obj2_src_path, obj2_compressed_path)

            assert os.path.isfile(obj1_src_path) is False
            assert os.path.isfile(obj2_src_path) is False
            assert os.path.isfile(obj1_compressed_path) is True
            assert os.path.isfile(obj2_compressed_path) is True

            check_info = {obj1_src_path: obj1_compressed_path,
                          obj2_src_path: obj2_compressed_path}

            objects = [PullObject(object_path=obj1_src_path,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile1.txt'),
                       PullObject(object_path=obj2_src_path,
                                  revision=ds.git.repo.head.commit.hexsha,
                                  dataset_path='myfile2.txt')
                       ]

            mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj1_id}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj1_id}?params=1",
                                         "namespace": ds.namespace,
                                         "obj_id": obj1_id,
                                         "dataset": ds.name
                                 },
                                 status=400)

            mocked_responses.get(f'https://api.gigantum.com/object-v1/{ds.namespace}/{ds.name}/{obj2_id}',
                                 payload={
                                         "presigned_url": f"https://dummyurl.com/{obj2_id}?params=1",
                                         "namespace": ds.namespace,
                                         "obj_id": obj2_id,
                                         "dataset": ds.name
                                 },
                                 status=200)

            with open(obj2_compressed_path, 'rb') as data2:
                mocked_responses.get(f"https://dummyurl.com/{obj2_id}?params=1",
                                     body=data2.read(), status=200,
                                     content_type='application/octet-stream')

            result = sb.pull_objects(ds, objects, updater)
            assert len(result.success) == 1
            assert len(result.failure) == 1
            assert isinstance(result, PullResult) is True
            assert isinstance(result.success[0], PullObject) is True
            assert result.success[0].object_path == obj2_src_path
            assert result.failure[0].object_path == obj1_src_path

            assert os.path.isfile(result.success[0].object_path) is True
            assert os.path.isfile(result.failure[0].object_path) is False

            decompressor = snappy.StreamDecompressor()
            with open(check_info[result.success[0].object_path], 'rb') as dd:
                source1 = decompressor.decompress(dd.read())
                source1 += decompressor.flush()
            with open(result.success[0].object_path, 'rt') as dd:
                dest1 = dd.read()
            assert source1.decode("utf-8") == dest1

    def test_finalize_pull(self, mock_dataset_with_cache_dir):
        sb = get_storage_backend("gigantum_object_v1")
        ds = mock_dataset_with_cache_dir[0]

        def check_updater(msg):
            assert msg == f"Done pulling objects from tester/dataset-1"

        sb.finalize_pull(ds, check_updater)
