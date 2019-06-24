import asyncio
import aiohttp
import aiofiles
import copy
import shutil
import zlib
import snappy
import tempfile
import requests

from gtmcore.dataset import Dataset
from gtmcore.dataset.storage.backend import ManagedStorageBackend
from typing import Optional, List, Dict, Callable, Tuple
import os

from gtmcore.dataset.io import PushResult, PushObject, PullResult, PullObject
from gtmcore.logging import LMLogger
from gtmcore.dataset.manifest.eventloop import get_event_loop

logger = LMLogger.get_logger()


class PresignedS3Upload(object):
    def __init__(self, object_service_root: str, object_service_headers: dict, upload_chunk_size: int,
                 object_details: PushObject) -> None:
        self.service_root = object_service_root
        self.object_service_headers = object_service_headers
        self.upload_chunk_size = upload_chunk_size

        self.object_details = object_details
        self.skip_object = False

        self.presigned_s3_url = ""
        self.s3_headers: Dict = dict()

    @property
    def is_presigned(self) -> bool:
        """Method to check if this upload request has successfully been presigned

        Returns:
            bool
        """
        return self.presigned_s3_url != ""

    def set_s3_headers(self, encryption_key_id: str) -> None:
        """Method to set the header property for S3

        Args:
            encryption_key_id: The encryption key id returned from the object service. This is required so the request
                               made to s3 is consistent with what was signed

        Returns:
            None
        """
        self.s3_headers = {'x-amz-server-side-encryption': 'aws:kms',
                           'x-amz-server-side-encryption-aws-kms-key-id': encryption_key_id}

    async def get_presigned_s3_url(self, session: aiohttp.ClientSession) -> None:
        """Method to make a request to the object service and pre-sign an S3 PUT

        Args:
            session: The current aiohttp session

        Returns:
            None
        """
        # Get the object id from the object path
        _, obj_id = self.object_details.object_path.rsplit('/', 1)

        async with session.put(f"{self.service_root}/{obj_id}", headers=self.object_service_headers) as response:
            if response.status == 200:
                # Successfully signed the request
                response_data = await response.json()
                self.presigned_s3_url = response_data.get("presigned_url")
                self.set_s3_headers(response_data.get("key_id"))
            elif response.status == 403:
                # Forbidden indicates Object already exists, don't need to re-push since we deduplicate so mark it skip
                self.skip_object = True
            else:
                # Something when wrong while trying to pre-sign the URL.
                body = await response.json()
                raise IOError(f"Failed to get pre-signed URL for PUT at {self.object_details.dataset_path}:{obj_id}."
                              f" Status: {response.status}. Response: {body}")

    async def _file_loader(self, filename: str, progress_update_fn: Callable):
        """Method to provide non-blocking chunked reads of files, useful if large.

        Args:
            filename: absolute path to the file to upload
            progress_update_fn: A callable with arg "completed_bytes" (int) indicating how many bytes have been
                                uploaded in since last called
        """
        async with aiofiles.open(filename, 'rb') as f:
            chunk = await f.read(self.upload_chunk_size)
            while chunk:
                progress_update_fn(completed_bytes=len(chunk))
                yield chunk
                chunk = await f.read(self.upload_chunk_size)

    async def put_object(self, session: aiohttp.ClientSession, progress_update_fn: Callable) -> None:
        """Method to put the object in S3 after the pre-signed URL has been obtained

        Args:
            session: The current aiohttp session
            progress_update_fn: A callable with arg "completed_bytes" (int) indicating how many bytes have been
                                uploaded in since last called

        Returns:
            None
        """
        # Set the Content-Length of the PUT explicitly since it won't happen automatically due to streaming IO
        headers = copy.deepcopy(self.s3_headers)

        # Detect file type if possible
        _, object_id = self.object_details.object_path.rsplit("/", 1)
        temp_compressed_path = os.path.join(tempfile.gettempdir(), object_id)

        # compress object before upload
        try:
            with open(self.object_details.object_path, "rb") as src_file:
                with open(temp_compressed_path, "wb") as compressed_file:
                    snappy.stream_compress(src_file, compressed_file)

            headers['Content-Length'] = str(os.path.getsize(temp_compressed_path))

            # Stream the file up to S3
            async with session.put(self.presigned_s3_url, headers=headers,
                                   data=self._file_loader(filename=temp_compressed_path,
                                                          progress_update_fn=progress_update_fn)) as response:
                if response.status != 200:
                    # An error occurred
                    body = await response.text()
                    raise IOError(f"Failed to push {self.object_details.dataset_path} to storage backend."
                                  f" Status: {response.status}. Response: {body}")
        finally:
            try:
                os.remove(temp_compressed_path)
            except FileNotFoundError:
                # Temp file never got created
                pass


class PresignedS3Download(object):
    def __init__(self, object_service_root: str, object_service_headers: dict, download_chunk_size: int,
                 object_details: PullObject) -> None:
        self.service_root = object_service_root
        self.object_service_headers = object_service_headers
        self.download_chunk_size = download_chunk_size

        self.object_details = object_details

        self.presigned_s3_url = ""

    @property
    def is_presigned(self) -> bool:
        """Method to check if this upload request has successfully been presigned

        Returns:
            bool
        """
        return self.presigned_s3_url != ""

    async def get_presigned_s3_url(self, session: aiohttp.ClientSession) -> None:
        """Method to make a request to the object service and pre-sign an S3 GET

        Args:
            session: The current aiohttp session

        Returns:
            None
        """
        # Get the object id from the object path
        _, obj_id = self.object_details.object_path.rsplit('/', 1)

        async with session.get(f"{self.service_root}/{obj_id}", headers=self.object_service_headers) as response:
            if response.status == 200:
                # Successfully signed the request
                response_data = await response.json()
                self.presigned_s3_url = response_data.get("presigned_url")
            else:
                # Something when wrong while trying to pre-sign the URL.
                body = await response.json()
                raise IOError(f"Failed to get pre-signed URL for GET at {self.object_details.dataset_path}:{obj_id}."
                              f" Status: {response.status}. Response: {body}")

    async def get_object(self, session: aiohttp.ClientSession, progress_update_fn: Callable) -> None:
        """Method to get the object from S3 after the pre-signed URL has been obtained

        Args:
            session: The current aiohttp session
            progress_update_fn: A callable with arg "completed_bytes" (int) indicating how many bytes have been
                                downloaded in since last called

        Returns:
            None
        """
        try:
            decompressor = snappy.StreamDecompressor()
            async with session.get(self.presigned_s3_url) as response:
                if response.status != 200:
                    # An error occurred
                    body = await response.text()
                    raise IOError(f"Failed to get {self.object_details.dataset_path} to storage backend."
                                  f" Status: {response.status}. Response: {body}")

                async with aiofiles.open(self.object_details.object_path, 'wb') as fd:
                    while True:
                        chunk = await response.content.read(self.download_chunk_size)
                        if not chunk:
                            fd.write(decompressor.flush())
                            break

                        decompressed_chunk = decompressor.decompress(chunk)
                        await fd.write(decompressed_chunk)
                        progress_update_fn(completed_bytes=len(decompressed_chunk))
        except Exception as err:
            logger.exception(err)
            raise IOError(f"Failed to get {self.object_details.dataset_path} from storage backend. {err}")


class GigantumObjectStore(ManagedStorageBackend):

    def __init__(self) -> None:
        # Additional attributes to track processed requests
        self.successful_requests: List = list()
        self.failed_requests: List = list()

        super().__init__()

    def _backend_metadata(self) -> dict:
        """Method to specify Storage Backend metadata for each implementation. This is used to render the UI

        Simply implement this method in a child class. Note, 'icon' should be the name of the icon file saved in the
        thumbnails directory. It should be a 128x128 px PNG image.

        Returns:
            dict
        """
        return {"storage_type": "gigantum_object_v1",
                "name": "Gigantum Cloud",
                "description": "Dataset storage provided by your Gigantum account supporting files up to 5GB in size",
                "tags": ["gigantum"],
                "icon": "gigantum_object_storage.png",
                "url": "https://docs.gigantum.com",
                "readme": """Gigantum Cloud Datasets are backed by a scalable object storage service that is linked to
your Gigantum account and credentials. It provides efficient storage at the file level and works seamlessly with the
Client.

This dataset type is fully managed. That means as you modify data, each version will be tracked independently. Syncing
to Gigantum Cloud will count towards your storage quota and include all versions of files.
"""}

    @property
    def client_should_dedup_on_push(self) -> bool:
        return True

    def _required_configuration(self) -> List[Dict[str, str]]:
        """A private method to return a list of keys that must be set for a backend to be fully configured

        The format is a dict of keys and descriptions. E.g.

        {
          "server": "The host name for the remote server",
          "username": "The current logged in username"

        }

        There are 3 keys that are always automatically populated:
           - username: the gigantum username for the logged in user
           - gigantum_bearer_token: the gigantum bearer token for the current session
           - gigantum_id_token: the gigantum id token for the current session

        Returns:

        """
        # No additional config required beyond defaults
        return list()

    def confirm_configuration(self, dataset) -> Optional[str]:
        """Method to verify a configuration and optionally allow the user to confirm before proceeding

        Should return the desired confirmation message if there is one. If no confirmation is required/possible,
        return None

        """
        return None

    @staticmethod
    def _object_service_endpoint(dataset: Dataset) -> str:
        """

        Args:
            dataset:

        Returns:

        """
        default_remote = dataset.client_config.config['git']['default_remote']
        obj_service = None
        for remote in dataset.client_config.config['git']['remotes']:
            if default_remote == remote:
                obj_service = dataset.client_config.config['git']['remotes'][remote]['object_service']
                break

        if not obj_service:
            raise ValueError('Object Service endpoint not configured.')

        return f"https://{obj_service}"

    def _object_service_headers(self) -> dict:
        """Method to generate the request headers, including authorization information

        Returns:

        """
        return {'Authorization': f"Bearer {self.configuration.get('gigantum_bearer_token')}",
                'Identity': self.configuration.get("gigantum_id_token"),
                'Content-Type': 'application/json',
                'Accept': 'application/json'}

    def prepare_push(self, dataset, objects: List[PushObject]) -> None:
        """Gigantum Object Service only requires that the user's tokens have been set

        Args:
            dataset: The current dataset instance
            objects: A list of PushObjects to be pushed

        Returns:
            None
        """
        if 'username' not in self.configuration.keys():
            raise ValueError("Username must be set to push objects to Gigantum Cloud")

        if 'gigantum_bearer_token' not in self.configuration.keys():
            raise ValueError("User must have valid session to push objects to Gigantum Cloud")

        if 'gigantum_id_token' not in self.configuration.keys():
            raise ValueError("User must have valid session to push objects to Gigantum Cloud")

    def finalize_push(self, dataset) -> None:
        pass

    def prepare_pull(self, dataset, objects: List[PullObject]) -> None:
        """Gigantum Object Service only requires that the user's tokens have been set

        Args:
            dataset: The current dataset instance
            objects: A list of PushObjects to be pulled

        Returns:
            None
        """
        if 'username' not in self.configuration.keys():
            raise ValueError("Username must be set to push objects to Gigantum Cloud")

        if 'gigantum_bearer_token' not in self.configuration.keys():
            raise ValueError("User must have valid session to push objects to Gigantum Cloud")

        if 'gigantum_id_token' not in self.configuration.keys():
            raise ValueError("User must have valid session to push objects to Gigantum Cloud")

    def finalize_pull(self, dataset) -> None:
        pass

    async def _push_object_consumer(self, queue: asyncio.LifoQueue, session: aiohttp.ClientSession,
                                    progress_update_fn: Callable) -> None:
        """Async Queue consumer worker for pushing objects to the object service/s3

        Args:
            queue: The current work queue
            session: The current aiohttp session
            progress_update_fn: A callable with arg "completed_bytes" (int) indicating how many bytes have been
                                uploaded in since last called

        Returns:
            None
        """
        while True:
            presigned_request: PresignedS3Upload = await queue.get()

            try:
                if presigned_request.skip_object is False:
                    if not presigned_request.is_presigned:
                        # Fetch the signed URL
                        await presigned_request.get_presigned_s3_url(session)
                        queue.put_nowait(presigned_request)
                    else:
                        # Process S3 Upload
                        await presigned_request.put_object(session, progress_update_fn)
                        self.successful_requests.append(presigned_request)
                else:
                    # Object skipped because it already exists in the backend (de-duplicating)
                    logger.info(f"Skipping duplicate download {presigned_request.object_details.dataset_path}")
                    progress_update_fn(os.path.getsize(presigned_request.object_details.object_path))
                    self.successful_requests.append(presigned_request)

            except Exception as err:
                logger.exception(err)
                self.failed_requests.append(presigned_request)

            # Notify the queue that the item has been processed
            queue.task_done()

    @staticmethod
    async def _push_object_producer(queue: asyncio.LifoQueue, object_service_root: str, object_service_headers: dict,
                                    upload_chunk_size: int, objects: List[PushObject]) -> None:
        """Async method to populate the queue with upload requests

        Args:
            queue: The current work queue
            object_service_root: The root URL to use for all objects, including the namespace and dataset name
            object_service_headers: The headers to use when requesting signed urls, including auth info
            upload_chunk_size: Size in bytes for streaming IO chunks
            objects: A list of PushObjects to push

        Returns:
            None
        """
        for obj in objects:
            presigned_request = PresignedS3Upload(object_service_root,
                                                  object_service_headers,
                                                  upload_chunk_size,
                                                  obj)
            await queue.put(presigned_request)

    async def _run_push_pipeline(self, object_service_root: str, object_service_headers: dict,
                                 objects: List[PushObject], progress_update_fn: Callable,
                                 upload_chunk_size: int = 4194304, num_workers: int = 4) -> None:
        """Method to run the async upload pipeline

        Args:
            object_service_root: The root URL to use for all objects, including the namespace and dataset name
            object_service_headers: The headers to use when requesting signed urls, including auth info
            objects: A list of PushObjects to push
            progress_update_fn: A callable with arg "completed_bytes" (int) indicating how many bytes have been
                                uploaded in since last called
            upload_chunk_size: Size in bytes for streaming IO chunks
            num_workers: the number of consumer workers to start

        Returns:

        """
        # We use a LifoQueue to ensure S3 uploads start as soon as they are ready to help ensure pre-signed urls do
        # not timeout before they can be used if there are a lot of files.
        queue: asyncio.LifoQueue = asyncio.LifoQueue()

        async with aiohttp.ClientSession() as session:
            # Start workers
            workers = []
            for i in range(num_workers):
                task = asyncio.ensure_future(self._push_object_consumer(queue, session, progress_update_fn))
                workers.append(task)

            # Populate the work queue
            await self._push_object_producer(queue,
                                             object_service_root,
                                             object_service_headers,
                                             upload_chunk_size,
                                             objects)

            # wait until the consumer has processed all items
            await queue.join()

            # the workers are still awaiting for work so close them
            for worker in workers:
                worker.cancel()

    def push_objects(self, dataset: Dataset, objects: List[PushObject],
                     progress_update_fn: Callable) -> PushResult:
        """High-level method to push objects to the object service/s3

        Args:
            dataset: The current dataset
            objects: A list of PushObjects the enumerate objects to push
            progress_update_fn: A callable with arg "completed_bytes" (int) indicating how many bytes have been
                                uploaded in since last called

        Returns:
            PushResult
        """
        # Clear lists
        self.successful_requests = list()
        self.failed_requests = list()
        message = "Successfully synced all objects"

        backend_config = dataset.client_config.config['datasets']['backends']['gigantum_object_v1']
        upload_chunk_size = backend_config['upload_chunk_size']
        num_workers = backend_config['num_workers']

        object_service_root = f"{self._object_service_endpoint(dataset)}/{dataset.namespace}/{dataset.name}"

        loop = get_event_loop()
        loop.run_until_complete(self._run_push_pipeline(object_service_root, self._object_service_headers(), objects,
                                                        progress_update_fn=progress_update_fn,
                                                        upload_chunk_size=upload_chunk_size,
                                                        num_workers=num_workers))

        successes = [x.object_details for x in self.successful_requests]

        failures = list()
        for f in self.failed_requests:
            # An exception was raised during task processing
            logger.error(f"Failed to push {f.object_details.dataset_path}:{f.object_details.object_path}")
            message = "Some objects failed to upload and will be retried on the next sync operation. Check results."
            failures.append(f.object_details)

        return PushResult(success=successes, failure=failures, message=message)

    async def _pull_object_consumer(self, queue: asyncio.LifoQueue, session: aiohttp.ClientSession,
                                    progress_update_fn: Callable) -> None:
        """Async Queue consumer worker for downloading objects from the object service/s3

        Args:
            queue: The current work queue
            session: The current aiohttp session
            progress_update_fn: A callable with arg "completed_bytes" (int) indicating how many bytes have been
                                downloaded in since last called

        Returns:
            None
        """
        while True:
            presigned_request: PresignedS3Download = await queue.get()

            try:
                if not presigned_request.is_presigned:
                    # Fetch the signed URL
                    await presigned_request.get_presigned_s3_url(session)
                    queue.put_nowait(presigned_request)
                else:
                    # Process S3 Download
                    await presigned_request.get_object(session, progress_update_fn)
                    self.successful_requests.append(presigned_request)

            except Exception as err:
                logger.exception(err)
                self.failed_requests.append(presigned_request)

            # Notify the queue that the item has been processed
            queue.task_done()

    @staticmethod
    async def _pull_object_producer(queue: asyncio.LifoQueue, object_service_root: str, object_service_headers: dict,
                                    download_chunk_size: int, objects: List[PullObject]) -> None:
        """Async method to populate the queue with download requests

        Args:
            queue: The current work queue
            object_service_root: The root URL to use for all objects, including the namespace and dataset name
            object_service_headers: The headers to use when requesting signed urls, including auth info
            download_chunk_size: Size in bytes for streaming IO chunks
            objects: A list of PullObjects to push

        Returns:
            None
        """
        for obj in objects:
            # Create object destination dir if needed
            obj_dir, _ = obj.object_path.rsplit('/', 1)
            os.makedirs(obj_dir, exist_ok=True)  # type: ignore

            # Populate queue with item for object
            presigned_request = PresignedS3Download(object_service_root,
                                                    object_service_headers,
                                                    download_chunk_size,
                                                    obj)
            await queue.put(presigned_request)

    async def _run_pull_pipeline(self, object_service_root: str, object_service_headers: dict,
                                 objects: List[PullObject], progress_update_fn: Callable,
                                 download_chunk_size: int = 4194304, num_workers: int = 4) -> None:
        """Method to run the async download pipeline

        Args:
            object_service_root: The root URL to use for all objects, including the namespace and dataset name
            object_service_headers: The headers to use when requesting signed urls, including auth info
            objects: A list of PushObjects to push
            progress_update_fn: A callable with arg "completed_bytes" (int) indicating how many bytes have been
                                downloaded in since last called
            download_chunk_size: Size in bytes for streaming IO chunks
            num_workers: the number of consumer workers to start

        Returns:

        """
        # We use a LifoQueue to ensure S3 uploads start as soon as they are ready to help ensure pre-signed urls do
        # not timeout before they can be used if there are a lot of files.
        queue: asyncio.LifoQueue = asyncio.LifoQueue()

        async with aiohttp.ClientSession() as session:
            workers = []
            for i in range(num_workers):
                task = asyncio.ensure_future(self._pull_object_consumer(queue, session, progress_update_fn))
                workers.append(task)

            # Populate the work queue
            await self._pull_object_producer(queue,
                                             object_service_root,
                                             object_service_headers,
                                             download_chunk_size,
                                             objects)

            # wait until the consumer has processed all items
            await queue.join()

            # the workers are still awaiting for work so close them
            for worker in workers:
                worker.cancel()

    def pull_objects(self, dataset: Dataset, objects: List[PullObject],
                     progress_update_fn: Callable) -> PullResult:
        """High-level method to pull objects from the object service/s3

        Args:
            dataset: The current dataset
            objects: A list of PullObjects the enumerate objects to push
            progress_update_fn: A callable with arg "completed_bytes" (int) indicating how many bytes have been
                                downloaded in since last called
        Returns:
            PushResult
        """
        # Clear lists
        self.successful_requests = list()
        self.failed_requests = list()
        message = "Successfully synced all objects"

        backend_config = dataset.client_config.config['datasets']['backends']['gigantum_object_v1']
        download_chunk_size = backend_config['download_chunk_size']
        num_workers = backend_config['num_workers']

        object_service_root = f"{self._object_service_endpoint(dataset)}/{dataset.namespace}/{dataset.name}"

        loop = get_event_loop()
        loop.run_until_complete(self._run_pull_pipeline(object_service_root, self._object_service_headers(), objects,
                                                        progress_update_fn=progress_update_fn,
                                                        download_chunk_size=download_chunk_size,
                                                        num_workers=num_workers))

        successes = [x.object_details for x in self.successful_requests]

        failures = list()
        for f in self.failed_requests:
            # An exception was raised during task processing
            logger.error(f"Failed to pull {f.object_details.dataset_path}:{f.object_details.object_path}")
            message = "Some objects failed to download and will be retried on the next sync operation. Check results."
            failures.append(f.object_details)

        return PullResult(success=successes, failure=failures, message=message)

    def delete_contents(self, dataset) -> None:
        """Method to remove the contents of a dataset from the storage backend, should only work if managed

        Args:
            dataset: Dataset object

        Returns:
            None
        """
        url = f"{self._object_service_endpoint(dataset)}/{dataset.namespace}/{dataset.name}"
        response = requests.delete(url, headers=self._object_service_headers(), timeout=30)

        if response.status_code != 200:
            logger.error(f"Failed to remove {dataset.namespace}/{dataset.name} from cloud index. "
                         f"Status Code: {response.status_code}")
            logger.error(response.json())
            raise IOError("Failed to invoke dataset delete in the dataset backend service.")
        else:
            logger.info(f"Deleted remote repository {dataset.namespace}/{dataset.name} from cloud index")
