import graphene
import os
import base64
import shutil
import pathlib
import flask

from gtmcore.inventory.inventory import InventoryManager
from gtmcore.logging import LMLogger
from gtmcore.dataset.io.manager import IOManager

from lmsrvcore.auth.user import get_logged_in_username, get_logged_in_author
from lmsrvcore.api.mutations import ChunkUploadMutation, ChunkUploadInput

from gtmcore.dataset.manifest import Manifest
from lmsrvlabbook.api.connections.datasetfile import DatasetFile, DatasetFileConnection


logger = LMLogger.get_logger()


class AddDatasetFile(graphene.relay.ClientIDMutation, ChunkUploadMutation):
    """Mutation to add a file to a labbook. File should be sent in the
    `uploadFile` key as a multi-part/form upload.
    file_path is the relative path in the dataset."""
    class Input:
        owner = graphene.String(required=True)
        dataset_name = graphene.String(required=True)
        file_path = graphene.String(required=True)
        chunk_upload_params = ChunkUploadInput(required=True)
        transaction_id = graphene.String(required=True)

    new_dataset_file_edge = graphene.Field(DatasetFileConnection.Edge)

    @classmethod
    def mutate_and_wait_for_chunks(cls, info, **kwargs):
        return AddDatasetFile(new_dataset_file_edge=DatasetFileConnection.Edge(node=None, cursor="null"))

    @classmethod
    def mutate_and_process_upload(cls, info, upload_file_path, upload_filename, **kwargs):
        if not upload_file_path:
            logger.error('No file uploaded')
            raise ValueError('No file uploaded')

        username = get_logged_in_username()
        owner = kwargs.get('owner')
        dataset_name = kwargs.get('dataset_name')
        file_path = kwargs.get('file_path')

        try:
            ds = InventoryManager().load_dataset(username, owner, dataset_name,
                                                 author=get_logged_in_author())
            with ds.lock():
                if not os.path.abspath(upload_file_path):
                    raise ValueError(f"Source file `{upload_file_path}` not an absolute path")

                if not os.path.isfile(upload_file_path):
                    raise ValueError(f"Source file does not exist at `{upload_file_path}`")

                manifest = Manifest(ds, username)
                full_dst = manifest.get_abs_path(file_path)

                # If file (hard link) already exists, remove it first so you don't write to all files with same content
                if os.path.isfile(full_dst):
                    os.remove(full_dst)

                full_dst_base = os.path.dirname(full_dst)
                if not os.path.isdir(full_dst_base):
                    pathlib.Path(full_dst_base).mkdir(parents=True, exist_ok=True)

                shutil.move(upload_file_path, full_dst)
                file_info = manifest.gen_file_info(file_path)

        finally:
            try:
                logger.debug(f"Removing temp file {upload_file_path}")
                os.remove(upload_file_path)
            except FileNotFoundError:
                pass

        # Create data to populate edge
        create_data = {'owner': owner,
                       'name': dataset_name,
                       'key': file_info['key'],
                       '_file_info': file_info}

        # TODO: Fix cursor implementation. this currently doesn't make sense when adding edges
        cursor = base64.b64encode(f"{0}".encode('utf-8'))
        return AddDatasetFile(new_dataset_file_edge=DatasetFileConnection.Edge(node=DatasetFile(**create_data),
                                                                               cursor=cursor))


class CompleteDatasetUploadTransaction(graphene.relay.ClientIDMutation):

    class Input:
        owner = graphene.String(required=True)
        dataset_name = graphene.String(required=True)
        transaction_id = graphene.String(required=True)
        cancel = graphene.Boolean()
        rollback = graphene.Boolean()

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, dataset_name,
                               transaction_id, cancel=False, rollback=False,
                               client_mutation_id=None):
        username = get_logged_in_username()
        ds = InventoryManager().load_dataset(username, owner, dataset_name,
                                             author=get_logged_in_author())
        with ds.lock():
            if cancel and rollback:
                logger.warning(f"Cancelled tx {transaction_id}, doing git reset")
                # TODO: Add ability to reset
            else:
                logger.info(f"Done batch upload {transaction_id}, cancelled={cancel}")
                if cancel:
                    logger.warning("Sweeping aborted batch upload.")

                m = "Cancelled upload `{transaction_id}`. " if cancel else ''

                # Sweep up and process all files added during upload
                manifest = Manifest(ds, username)
                manifest.sweep_all_changes(upload=True, extra_msg=m)

        return CompleteDatasetUploadTransaction(success=True)


class DownloadDatasetFiles(graphene.relay.ClientIDMutation):
    class Input:
        dataset_owner = graphene.String(required=True)
        dataset_name = graphene.String(required=True)
        labbook_owner = graphene.String()
        labbook_name = graphene.String()
        all_keys = graphene.Boolean()
        keys = graphene.List(graphene.String)

    updated_file_edges = graphene.List(DatasetFileConnection.Edge)
    status_message = graphene.String()

    @classmethod
    def mutate_and_get_payload(cls, root, info, dataset_owner, dataset_name, labbook_name=None, labbook_owner=None,
                               all_keys=None, keys=None, client_mutation_id=None):
        logged_in_username = get_logged_in_username()

        if labbook_name:
            # This is a linked dataset, load repo from the Project
            lb = InventoryManager().load_labbook(logged_in_username, labbook_owner, labbook_name)
            dataset_dir = os.path.join(lb.root_dir, '.gigantum', 'datasets', dataset_owner, dataset_name)
            ds = InventoryManager().load_dataset_from_directory(dataset_dir, author=get_logged_in_author())
        else:
            # this is a normal dataset. Load repo from working dir
            ds = InventoryManager().load_dataset(logged_in_username, dataset_owner, dataset_name,
                                                 author=get_logged_in_author())
        ds.namespace = dataset_owner
        ds.backend.set_default_configuration(logged_in_username, flask.g.access_token, flask.g.id_token)
        m = Manifest(ds, logged_in_username)
        iom = IOManager(ds, m)

        if all_keys:
            result = iom.pull_all()
        else:
            result = iom.pull_objects(keys=keys)

        edge_objs = list()
        # Prime the dataset loader with the dataset object. This handles making sure if loaded from the Project it
        # is the correct repository.
        info.context.dataset_loader.prime(f"{get_logged_in_username()}&{dataset_owner}&{dataset_name}", ds)
        for cnt, r in enumerate(result.success):
            create_data = {"owner": dataset_owner,
                           "name": dataset_name,
                           "key": r.dataset_path}
            cursor = base64.b64encode("{}".format(cnt).encode("UTF-8")).decode("UTF-8")
            edge_objs.append(DatasetFileConnection.Edge(node=DatasetFile(**create_data), cursor=cursor))

        return DownloadDatasetFiles(updated_file_edges=edge_objs, status_message=result.message)


class DeleteDatasetFiles(graphene.ClientIDMutation):
    class Input:
        dataset_owner = graphene.String(required=True)
        dataset_name = graphene.String(required=True)
        keys = graphene.List(graphene.String, required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, dataset_owner, dataset_name, keys, client_mutation_id=None):
        logged_in_username = get_logged_in_username()
        ds = InventoryManager().load_dataset(logged_in_username, dataset_owner, dataset_name,
                                             author=get_logged_in_author())
        ds.namespace = dataset_owner
        m = Manifest(ds, logged_in_username)

        with ds.lock():
            m.delete(keys)

        return DeleteDatasetFiles(success=True)


class MoveDatasetFile(graphene.ClientIDMutation):
    class Input:
        dataset_owner = graphene.String(required=True)
        dataset_name = graphene.String(required=True)
        src_path = graphene.String(required=True)
        dst_path = graphene.String(required=True)

    updated_edges = graphene.List(DatasetFileConnection.Edge)

    @classmethod
    def mutate_and_get_payload(cls, root, info, dataset_owner, dataset_name, src_path, dst_path,
                               client_mutation_id=None):
        logged_in_username = get_logged_in_username()
        ds = InventoryManager().load_dataset(logged_in_username, dataset_owner, dataset_name,
                                             author=get_logged_in_author())
        ds.namespace = dataset_owner
        m = Manifest(ds, logged_in_username)

        with ds.lock():
            edge_data = m.move(src_path, dst_path)

        file_edges = list()
        for edge_dict in edge_data:
            file_edges.append(DatasetFile(owner=dataset_owner,
                                          name=dataset_name,
                                          key=edge_dict['key'],
                                          is_dir=edge_dict['is_dir'],
                                          is_favorite=edge_dict['is_favorite'],
                                          modified_at=edge_dict['modified_at'],
                                          is_local=edge_dict['is_local'],
                                          size=str(edge_dict['size'])))

        cursors = [base64.b64encode("{}".format(cnt).encode("UTF-8")).decode("UTF-8")
                   for cnt, x in enumerate(file_edges)]

        edge_objs = [DatasetFileConnection.Edge(node=e, cursor=c) for e, c in zip(file_edges, cursors)]
        return MoveDatasetFile(updated_edges=edge_objs)


class MakeDatasetDirectory(graphene.ClientIDMutation):
    class Input:
        dataset_owner = graphene.String(required=True)
        dataset_name = graphene.String(required=True)
        key = graphene.String(required=True)

    new_dataset_file_edge = graphene.Field(DatasetFileConnection.Edge)

    @classmethod
    def mutate_and_get_payload(cls, root, info, dataset_owner, dataset_name, key,
                               client_mutation_id=None):
        logged_in_username = get_logged_in_username()
        ds = InventoryManager().load_dataset(logged_in_username, dataset_owner, dataset_name,
                                             author=get_logged_in_author())
        ds.namespace = dataset_owner
        m = Manifest(ds, logged_in_username)

        if key[-1] != '/':
            raise ValueError("Provided relative path must end in `/` to indicate it is a directory")

        with ds.lock():
            file_info = m.create_directory(key)

        create_data = {'owner': dataset_owner,
                       'name': dataset_name,
                       'key': file_info['key'],
                       '_file_info': file_info}

        # TODO: Fix cursor implementation, this currently doesn't make sense
        cursor = base64.b64encode(f"{0}".encode('utf-8'))

        return MakeDatasetDirectory(new_dataset_file_edge=DatasetFileConnection.Edge(node=DatasetFile(**create_data),
                                                                                     cursor=cursor))

