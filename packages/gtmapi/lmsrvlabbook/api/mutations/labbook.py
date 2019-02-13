# Copyright (c) 2018 FlashX, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import base64
import os
import shutil

import flask
import graphene
import requests

from gtmcore.configuration import Configuration
from gtmcore.container.container import ContainerOperations
from gtmcore.dispatcher import (Dispatcher, jobs)
from gtmcore.labbook import LabBook

from gtmcore.inventory import loaders
from gtmcore.inventory.inventory import InventoryManager
from gtmcore.exceptions import GigantumException
from gtmcore.logging import LMLogger
from gtmcore.files import FileOperations
from gtmcore.activity import ActivityStore, ActivityDetailRecord, ActivityDetailType, ActivityRecord, ActivityType
from gtmcore.gitlib.gitlab import GitLabManager
from gtmcore.environment import ComponentManager

from lmsrvcore.api.mutations import ChunkUploadMutation, ChunkUploadInput
from lmsrvcore.api.connections import ListBasedConnection
from lmsrvcore.auth.user import get_logged_in_username, get_logged_in_author
from lmsrvcore.auth.identity import parse_token

from lmsrvlabbook.api.connections.labbookfileconnection import LabbookFavoriteConnection
from lmsrvlabbook.api.connections.labbookfileconnection import LabbookFileConnection
from lmsrvlabbook.api.connections.labbook import LabbookConnection
from lmsrvlabbook.api.objects.labbook import Labbook
from lmsrvlabbook.api.objects.labbookfile import LabbookFavorite, LabbookFile
from lmsrvlabbook.dataloader.labbook import LabBookLoader


logger = LMLogger.get_logger()


class CreateLabbook(graphene.relay.ClientIDMutation):
    """Mutation for creation of a new Labbook on disk"""

    class Input:
        name = graphene.String(required=True)
        description = graphene.String(required=True)
        repository = graphene.String(required=True)
        base_id = graphene.String(required=True)
        revision = graphene.Int(required=True)
        is_untracked = graphene.Boolean(required=False)

    # Return the LabBook instance
    labbook = graphene.Field(lambda: Labbook)

    @classmethod
    def mutate_and_get_payload(cls, root, info, name, description, repository, base_id, revision,
                               is_untracked=False, client_mutation_id=None):
        username = get_logged_in_username()
        inv_manager = InventoryManager()
        if is_untracked:
            lb = inv_manager.create_labbook_disabled_lfs(username=username,
                                                         owner=username,
                                                         labbook_name=name,
                                                         description=description,
                                                         author=get_logged_in_author())
        else:
            lb = inv_manager.create_labbook(username=username,
                                            owner=username,
                                            labbook_name=name,
                                            description=description,
                                            author=get_logged_in_author())

        if is_untracked:
            FileOperations.set_untracked(lb, 'input')
            FileOperations.set_untracked(lb, 'output')
            input_set = FileOperations.is_set_untracked(lb, 'input')
            output_set = FileOperations.is_set_untracked(lb, 'output')
            if not (input_set and output_set):
                raise ValueError(f'{str(lb)} untracking for input/output in malformed state')
            if not lb.is_repo_clean:
                raise ValueError(f'{str(lb)} should have clean Git state after setting for untracked')

        adr = ActivityDetailRecord(ActivityDetailType.LABBOOK, show=False, importance=0)
        adr.add_value('text/plain', f"Created new LabBook: {username}/{name}")

        # Create activity record
        ar = ActivityRecord(ActivityType.LABBOOK,
                            message=f"Created new LabBook: {username}/{name}",
                            show=True,
                            importance=255,
                            linked_commit=lb.git.commit_hash)
        ar.add_detail_object(adr)

        store = ActivityStore(lb)
        store.create_activity_record(ar)

        cm = ComponentManager(lb)
        cm.add_base(repository, base_id, revision)

        return CreateLabbook(labbook=Labbook(owner=username, name=lb.name))


class DeleteLabbook(graphene.ClientIDMutation):
    """Delete a labbook from disk. """
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        confirm = graphene.Boolean(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, confirm, client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())
        if confirm:
            logger.info(f"Deleting {str(lb)}...")
            try:
                lb, stopped = ContainerOperations.stop_container(labbook=lb, username=username)
            except OSError as e:
                logger.warning(e)

            lb, docker_removed = ContainerOperations.delete_image(labbook=lb, username=username)
            if not docker_removed:
                raise ValueError(f'Cannot delete docker image for {str(lb)} - unable to delete LB from disk')

            # TODO - gtmcore should contain routine to properly delete a labbook
            shutil.rmtree(lb.root_dir, ignore_errors=True)

            if os.path.exists(lb.root_dir):
                logger.error(f'Deleted {str(lb)} but root directory {lb.root_dir} still exists!')
                return DeleteLabbook(success=False)
            else:
                return DeleteLabbook(success=True)
        else:
            logger.info(f"Dry run in deleting {str(lb)} -- not deleted.")
            return DeleteLabbook(success=False)


class DeleteRemoteLabbook(graphene.ClientIDMutation):
    """Delete a labbook from the remote repository."""
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        confirm = graphene.Boolean(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, confirm, client_mutation_id=None):
        if confirm is True:
            # Load config data
            configuration = Configuration().config

            # Extract valid Bearer token
            token = None
            if hasattr(info.context.headers, 'environ'):
                if "HTTP_AUTHORIZATION" in info.context.headers.environ:
                    token = parse_token(info.context.headers.environ["HTTP_AUTHORIZATION"])
            if not token:
                raise ValueError("Authorization header not provided. Cannot perform remote delete operation.")

            # Get remote server configuration
            default_remote = configuration['git']['default_remote']
            admin_service = None
            for remote in configuration['git']['remotes']:
                if default_remote == remote:
                    admin_service = configuration['git']['remotes'][remote]['admin_service']
                    index_service = configuration['git']['remotes'][remote]['index_service']
                    break

            if not admin_service:
                raise ValueError('admin_service could not be found')

            # Perform delete operation
            mgr = GitLabManager(default_remote, admin_service, access_token=token)
            mgr.remove_labbook(owner, labbook_name)
            logger.info(f"Deleted {owner}/{labbook_name} from the remote repository {default_remote}")

            # Call Index service to remove project from cloud index and search
            # Don't raise an exception if the index delete fails, since this can be handled relatively gracefully
            # for now, but do return success=false
            success = True
            access_token = flask.g.get('access_token', None)
            id_token = flask.g.get('id_token', None)
            repo_id = mgr.get_repository_id(owner, labbook_name)
            response = requests.delete(f"https://{index_service}/index/{repo_id}",
                                       headers={"Authorization": f"Bearer {access_token}",
                                                "Identity": id_token}, timeout=10)

            if response.status_code != 204:
                logger.error(f"Failed to remove project from cloud index. "
                             f"Status Code: {response.status_code}")
                logger.error(response.json())
            else:
                logger.info(f"Deleted remote repository {owner}/{labbook_name} from cloud index")


            # Remove locally any references to that cloud repo that's just been deleted.
            try:
                username = get_logged_in_username()
                lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                                     author=get_logged_in_author())
                lb.remove_remote()
                lb.remove_lfs_remotes()
            except GigantumException as e:
                logger.warning(e)

            return DeleteLabbook(success=True)
        else:
            logger.info(f"Dry run deleting {labbook_name} from remote repository -- not deleted.")
            return DeleteLabbook(success=False)


class ExportLabbook(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)

    job_key = graphene.String()

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, client_mutation_id=None):
        username = get_logged_in_username()
        working_directory = Configuration().config['git']['working_directory']
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())

        job_metadata = {'method': 'export_labbook_as_zip',
                        'labbook': lb.key}
        job_kwargs = {'labbook_path': lb.root_dir,
                      'lb_export_directory': os.path.join(working_directory, 'export')}
        dispatcher = Dispatcher()
        job_key = dispatcher.dispatch_task(jobs.export_labbook_as_zip,
                                           kwargs=job_kwargs,
                                           metadata=job_metadata)

        return ExportLabbook(job_key=job_key.key_str)


class ImportLabbook(graphene.relay.ClientIDMutation, ChunkUploadMutation):
    class Input:
        chunk_upload_params = ChunkUploadInput(required=True)

    import_job_key = graphene.String()

    @classmethod
    def mutate_and_wait_for_chunks(cls, info, **kwargs):
        return ImportLabbook()

    @classmethod
    def mutate_and_process_upload(cls, info, upload_file_path, upload_filename, **kwargs):
        if not upload_file_path:
            logger.error('No file uploaded')
            raise ValueError('No file uploaded')

        username = get_logged_in_username()
        job_metadata = {'method': 'import_labbook_from_zip'}
        job_kwargs = {
            'archive_path': upload_file_path,
            'username': username,
            'owner': username
        }
        dispatcher = Dispatcher()
        job_key = dispatcher.dispatch_task(jobs.import_labboook_from_zip,
                                           kwargs=job_kwargs,
                                           metadata=job_metadata)

        return ImportLabbook(import_job_key=job_key.key_str)


class ImportRemoteLabbook(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        remote_url = graphene.String(required=True)

    new_labbook_edge = graphene.Field(LabbookConnection.Edge)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, remote_url, client_mutation_id=None):
        username = get_logged_in_username()
        logger.info(f"Importing remote labbook from {remote_url}")
        lb = LabBook(author=get_logged_in_author())
        default_remote = lb.client_config.config['git']['default_remote']
        admin_service = None
        for remote in lb.client_config.config['git']['remotes']:
            if default_remote == remote:
                admin_service = lb.client_config.config['git']['remotes'][remote]['admin_service']
                break

        # Extract valid Bearer token
        if hasattr(info.context, 'headers') and "HTTP_AUTHORIZATION" in info.context.headers.environ:
            token = parse_token(info.context.headers.environ["HTTP_AUTHORIZATION"])
        else:
            raise ValueError("Authorization header not provided. Must have a valid session to query for collaborators")

        mgr = GitLabManager(default_remote, admin_service, token)
        mgr.configure_git_credentials(default_remote, username)
        try:
            collaborators = [collab[1] for collab in mgr.get_collaborators(owner, labbook_name) or []]
            is_collab = any([username == c for c in collaborators])
        except:
            is_collab = username == owner

        # IF user is collaborator, then clone in order to support collaboration
        # ELSE, this means we are cloning a public repo and can't push back
        #       so we change to owner to the given user so they can (re)publish
        #       and do whatever with it.
        make_owner = not is_collab
        logger.info(f"Getting from remote, make_owner = {make_owner}")
        lb = loaders.labbook_from_remote(remote_url, username, owner, labbook=lb,
                                         make_owner=make_owner)
        import_owner = InventoryManager().query_owner(lb)
        # TODO: Fix cursor implementation, this currently doesn't make sense
        cursor = base64.b64encode(f"{0}".encode('utf-8'))
        lbedge = LabbookConnection.Edge(node=Labbook(owner=import_owner, name=labbook_name),
                                        cursor=cursor)
        return ImportRemoteLabbook(new_labbook_edge=lbedge)


class AddLabbookRemote(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        remote_name = graphene.String(required=True)
        remote_url = graphene.String(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name,
                               remote_name, remote_url,
                               client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())
        with lb.lock():
            lb.add_remote(remote_name, remote_url)
        return AddLabbookRemote(success=True)


class SetLabbookDescription(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        description_content = graphene.String(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name,
                               description_content, client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())
        lb.description = description_content
        with lb.lock():
            lb.git.add(os.path.join(lb.root_dir, '.gigantum/labbook.yaml'))
            commit = lb.git.commit('Updating description')

            adr = ActivityDetailRecord(ActivityDetailType.LABBOOK, show=False)
            adr.add_value('text/plain', "Updated description of Project")
            ar = ActivityRecord(ActivityType.LABBOOK,
                                message="Updated description of Project",
                                linked_commit=commit.hexsha,
                                tags=["labbook"],
                                show=False)
            ar.add_detail_object(adr)
            ars = ActivityStore(lb)
            ars.create_activity_record(ar)
        return SetLabbookDescription(success=True)


class CompleteBatchUploadTransaction(graphene.relay.ClientIDMutation):

    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        transaction_id = graphene.String(required=True)
        cancel = graphene.Boolean()
        rollback = graphene.Boolean()

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name,
                               transaction_id, cancel=False, rollback=False,
                               client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())
        with lb.lock():
            FileOperations.complete_batch(lb, transaction_id, cancel=cancel,
                                          rollback=rollback)
        return CompleteBatchUploadTransaction(success=True)


class AddLabbookFile(graphene.relay.ClientIDMutation, ChunkUploadMutation):
    """Mutation to add a file to a labbook. File should be sent in the
    `uploadFile` key as a multi-part/form upload.
    file_path is the relative path from the labbook section specified."""
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        section = graphene.String(required=True)
        file_path = graphene.String(required=True)
        chunk_upload_params = ChunkUploadInput(required=True)
        transaction_id = graphene.String(required=True)

    new_labbook_file_edge = graphene.Field(LabbookFileConnection.Edge)

    @classmethod
    def mutate_and_wait_for_chunks(cls, info, **kwargs):
        return AddLabbookFile(new_labbook_file_edge=LabbookFileConnection.Edge(node=None, cursor="null"))

    @classmethod
    def mutate_and_process_upload(cls, info, upload_file_path, upload_filename, **kwargs):
        if not upload_file_path:
            logger.error('No file uploaded')
            raise ValueError('No file uploaded')

        owner = kwargs.get('owner')
        labbook_name = kwargs.get('labbook_name')
        section = kwargs.get('section')
        transaction_id = kwargs.get('transaction_id')
        file_path = kwargs.get('file_path')

        try:
            username = get_logged_in_username()
            lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                                 author=get_logged_in_author())
            dst_path = os.path.join(os.path.dirname(file_path), upload_filename)
            with lb.lock():
                fops = FileOperations.put_file(labbook=lb,
                                               section=section,
                                               src_file=upload_file_path,
                                               dst_path=dst_path,
                                               txid=transaction_id)
        finally:
            try:
                logger.debug(f"Removing temp file {upload_file_path}")
                os.remove(upload_file_path)
            except FileNotFoundError:
                pass

        # Create data to populate edge
        create_data = {'owner': owner,
                       'name': labbook_name,
                       'section': section,
                       'key': fops['key'],
                       '_file_info': fops}

        # TODO: Fix cursor implementation..this currently doesn't make sense when adding edges without a refresh
        cursor = base64.b64encode(f"{0}".encode('utf-8'))
        return AddLabbookFile(new_labbook_file_edge=LabbookFileConnection.Edge(node=LabbookFile(**create_data),
                                                                               cursor=cursor))


class DeleteLabbookFiles(graphene.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        section = graphene.String(required=True)
        file_paths = graphene.List(graphene.String, required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, section, file_paths, client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())

        with lb.lock():
            FileOperations.delete_files(lb, section, file_paths)

        return DeleteLabbookFiles(success=True)


class MoveLabbookFile(graphene.ClientIDMutation):
    """Method to move/rename a file or directory. If file, both src_path and dst_path should contain the file name.
    If a directory, be sure to include the trailing slash"""
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        section = graphene.String(required=True)
        src_path = graphene.String(required=True)
        dst_path = graphene.String(required=True)

    updated_edges = graphene.List(LabbookFileConnection.Edge)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, section, src_path, dst_path,
                               client_mutation_id=None, **kwargs):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())

        with lb.lock():
            mv_results = FileOperations.move_file(lb, section, src_path, dst_path)

        file_edges = list()
        for file_dict in mv_results:
            file_edges.append(LabbookFile(owner=owner,
                                          name=labbook_name,
                                          section=section,
                                          key=file_dict['key'],
                                          is_dir=file_dict['is_dir'],
                                          is_favorite=file_dict['is_favorite'],
                                          modified_at=file_dict['modified_at'],
                                          size=str(file_dict['size'])))

        cursors = [base64.b64encode("{}".format(cnt).encode("UTF-8")).decode("UTF-8")
                   for cnt, x in enumerate(file_edges)]

        edge_objs = [LabbookFileConnection.Edge(node=e, cursor=c) for e, c in zip(file_edges, cursors)]

        return MoveLabbookFile(updated_edges=edge_objs)


class MakeLabbookDirectory(graphene.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        section = graphene.String(required=True)
        directory = graphene.String(required=True)

    new_labbook_file_edge = graphene.Field(LabbookFileConnection.Edge)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, section, directory,
                               client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())
        with lb.lock():
            FileOperations.makedir(lb, os.path.join(section, directory), create_activity_record=True)

        # Prime dataloader with labbook you already loaded
        dataloader = LabBookLoader()
        dataloader.prime(f"{owner}&{labbook_name}&{lb.name}", lb)

        # Create data to populate edge
        file_info = FileOperations.get_file_info(lb, section, directory)
        create_data = {'owner': owner,
                       'name': labbook_name,
                       'section': section,
                       'key': file_info['key'],
                       '_file_info': file_info}

        # TODO: Fix cursor implementation, this currently doesn't make sense
        cursor = base64.b64encode(f"{0}".encode('utf-8'))

        return MakeLabbookDirectory(
            new_labbook_file_edge=LabbookFileConnection.Edge(
                node=LabbookFile(**create_data),
                cursor=cursor))


class AddLabbookFavorite(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        section = graphene.String(required=True)
        key = graphene.String(required=True)
        description = graphene.String(required=False)
        is_dir = graphene.Boolean(required=False)

    new_favorite_edge = graphene.Field(LabbookFavoriteConnection.Edge)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, section, key, description=None, is_dir=False,
                               client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())

        # Add Favorite
        if is_dir:
            is_dir = is_dir

            # Make sure trailing slashes are always present when favoriting a dir
            if key[-1] != "/":
                key = f"{key}/"

        with lb.lock():
            new_favorite = lb.create_favorite(section, key, description=description, is_dir=is_dir)

        # Create data to populate edge
        create_data = {"id": f"{owner}&{labbook_name}&{section}&{key}",
                       "owner": owner,
                       "section": section,
                       "name": labbook_name,
                       "key": key,
                       "index": new_favorite['index'],
                       "_favorite_data": new_favorite}

        # Create cursor
        cursor = base64.b64encode(f"{str(new_favorite['index'])}".encode('utf-8'))

        return AddLabbookFavorite(new_favorite_edge=LabbookFavoriteConnection.Edge(node=LabbookFavorite(**create_data),
                                                                                   cursor=cursor))


class UpdateLabbookFavorite(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        section = graphene.String(required=True)
        key = graphene.String(required=True)
        updated_index = graphene.Int(required=False)
        updated_description = graphene.String(required=False)

    updated_favorite_edge = graphene.Field(LabbookFavoriteConnection.Edge)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, section, key, updated_index=None,
                               updated_description=None, client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())

        with lb.lock():
            new_favorite = lb.update_favorite(section, key,
                                              new_description=updated_description,
                                              new_index=updated_index)

        # Create data to populate edge
        create_data = {"id": f"{owner}&{labbook_name}&{section}&{key}",
                       "owner": owner,
                       "section": section,
                       "key": key,
                       "_favorite_data": new_favorite}

        # Create dummy cursor
        cursor = base64.b64encode(f"{str(new_favorite['index'])}".encode('utf-8'))

        return UpdateLabbookFavorite(updated_favorite_edge=LabbookFavoriteConnection.Edge(node=LabbookFavorite(**create_data),
                                                                                          cursor=cursor))


class RemoveLabbookFavorite(graphene.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        section = graphene.String(required=True)
        key = graphene.String(required=True)

    success = graphene.Boolean()
    removed_node_id = graphene.String()

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, section, key, client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())

        # Manually generate the Node ID for now. This simplifies the connection between the file browser and favorites
        # widgets in the UI
        favorite_node_id = f"LabbookFavorite:{owner}&{labbook_name}&{section}&{key}"
        favorite_node_id = base64.b64encode(favorite_node_id.encode()).decode()

        with lb.lock():
            lb.remove_favorite(section, key)

        return RemoveLabbookFavorite(success=True, removed_node_id=favorite_node_id)


class AddLabbookCollaborator(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        username = graphene.String(required=True)

    updated_labbook = graphene.Field(Labbook)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, username,
                               client_mutation_id=None):
        #TODO(billvb/dmk) - Here "username" refers to the intended recipient username.
        # it should probably be renamed here and in the frontend to "collaboratorUsername"
        logged_in_username = get_logged_in_username()
        lb = InventoryManager().load_labbook(logged_in_username, owner, labbook_name,
                                             author=get_logged_in_author())

        # TODO: Future work will look up remote in LabBook data, allowing user to select remote.
        default_remote = lb.client_config.config['git']['default_remote']
        admin_service = None
        for remote in lb.client_config.config['git']['remotes']:
            if default_remote == remote:
                admin_service = lb.client_config.config['git']['remotes'][remote]['admin_service']
                break

        # Extract valid Bearer token
        if "HTTP_AUTHORIZATION" in info.context.headers.environ:
            token = parse_token(info.context.headers.environ["HTTP_AUTHORIZATION"])
        else:
            raise ValueError("Authorization header not provided. "
                             "Must have a valid session to query for collaborators")

        # Add collaborator to remote service
        mgr = GitLabManager(default_remote, admin_service, token)
        mgr.add_collaborator(owner, labbook_name, username)

        # Prime dataloader with labbook you just created
        dataloader = LabBookLoader()
        dataloader.prime(f"{logged_in_username}&{owner}&{lb.name}", lb)

        create_data = {"owner": owner,
                       "name": labbook_name}

        return AddLabbookCollaborator(updated_labbook=Labbook(**create_data))


class DeleteLabbookCollaborator(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        username = graphene.String(required=True)

    updated_labbook = graphene.Field(Labbook)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, username, client_mutation_id=None):
        logged_in_username = get_logged_in_username()
        lb = InventoryManager().load_labbook(logged_in_username, owner, labbook_name,
                                             author=get_logged_in_author())

        # TODO: Future work will look up remote in LabBook data, allowing user to select remote.
        default_remote = lb.client_config.config['git']['default_remote']
        admin_service = None
        for remote in lb.client_config.config['git']['remotes']:
            if default_remote == remote:
                admin_service = lb.client_config.config['git']['remotes'][remote]['admin_service']
                break

        # Extract valid Bearer token
        if "HTTP_AUTHORIZATION" in info.context.headers.environ:
            token = parse_token(info.context.headers.environ["HTTP_AUTHORIZATION"])
        else:
            raise ValueError("Authorization header not provided. Must have a valid session to query for collaborators")

        # Add collaborator to remote service
        mgr = GitLabManager(default_remote, admin_service, token)
        mgr.delete_collaborator(owner, labbook_name, username)

        create_data = {"owner": owner,
                       "name": labbook_name}

        return DeleteLabbookCollaborator(updated_labbook=Labbook(**create_data))


class WriteLabbookReadme(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        content = graphene.String(required=True)

    updated_labbook = graphene.Field(Labbook)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, content, client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())

        # Write data
        with lb.lock():
            lb.write_readme(content)

        return WriteLabbookReadme(updated_labbook=Labbook(owner=owner, name=labbook_name))


class FetchLabbookEdge(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)

    new_labbook_edge = graphene.Field(LabbookConnection.Edge)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())

        cursor = base64.b64encode(f"{0}".encode('utf-8'))
        lbedge = LabbookConnection.Edge(node=Labbook(owner=owner, name=labbook_name),
                                        cursor=cursor)

        return FetchLabbookEdge(new_labbook_edge=lbedge)
