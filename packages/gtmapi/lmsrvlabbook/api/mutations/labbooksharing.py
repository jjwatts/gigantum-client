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
import graphene
import os
import flask
import requests

from gtmcore.inventory.inventory import InventoryManager
from gtmcore.configuration import Configuration
from gtmcore.dispatcher import Dispatcher, jobs
from gtmcore.exceptions import GigantumException
from gtmcore.logging import LMLogger
from gtmcore.workflows import MergeOverride
from gtmcore.workflows.gitlab import GitLabManager, ProjectPermissions
from gtmcore.labbook import LabBook

from lmsrvcore.api import logged_mutation
from lmsrvcore.auth.identity import parse_token
from lmsrvcore.api.mutations import ChunkUploadMutation, ChunkUploadInput
from lmsrvcore.auth.user import get_logged_in_username, get_logged_in_author

from lmsrvlabbook.api.connections.labbook import LabbookConnection
from lmsrvlabbook.api.objects.labbook import Labbook as LabbookObject

logger = LMLogger.get_logger()


class PublishLabbook(graphene.relay.ClientIDMutation):

    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        set_public = graphene.Boolean(required=False)

    job_key = graphene.String()

    @classmethod
    @logged_mutation
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, set_public=False,
                               client_mutation_id=None):
        # Load LabBook
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())
        # Extract valid Bearer token
        if "HTTP_AUTHORIZATION" in info.context.headers.environ:
            token = parse_token(info.context.headers.environ["HTTP_AUTHORIZATION"])
        else:
            raise ValueError("Authorization header not provided. Must have a valid session to query for collaborators")

        job_metadata = {'method': 'publish_labbook',
                        'labbook': lb.key}
        job_kwargs = {'repository': lb,
                      'username': username,
                      'access_token': token,
                      'public': set_public}
        dispatcher = Dispatcher()
        job_key = dispatcher.dispatch_task(jobs.publish_repository, kwargs=job_kwargs, metadata=job_metadata)
        logger.info(f"Publishing LabBook {lb.root_dir} in background job with key {job_key.key_str}")

        return PublishLabbook(job_key=job_key.key_str)


class SyncLabbook(graphene.relay.ClientIDMutation):

    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        pull_only = graphene.Boolean(required=False, default=False)
        override_method = graphene.String(default="abort")

    job_key = graphene.String()

    @classmethod
    @logged_mutation
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, pull_only=False,
                               override_method="abort", client_mutation_id=None):
        # Load LabBook
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())

        # Extract valid Bearer token
        token = None
        if hasattr(info.context.headers, 'environ'):
            if "HTTP_AUTHORIZATION" in info.context.headers.environ:
                token = parse_token(info.context.headers.environ["HTTP_AUTHORIZATION"])

        if not token:
            raise ValueError("Authorization header not provided. "
                             "Must have a valid session to query for collaborators")

        default_remote = lb.client_config.config['git']['default_remote']
        admin_service = None
        for remote in lb.client_config.config['git']['remotes']:
            if default_remote == remote:
                admin_service = lb.client_config.config['git']['remotes'][remote]['admin_service']
                break

        if not admin_service:
            raise ValueError('admin_service could not be found')

        # Configure git creds
        mgr = GitLabManager(default_remote, admin_service, access_token=token)
        mgr.configure_git_credentials(default_remote, username)

        override = MergeOverride(override_method)

        job_metadata = {'method': 'sync_labbook',
                        'labbook': lb.key}
        job_kwargs = {'repository': lb,
                      'pull_only': pull_only,
                      'username': username,
                      'override': override}
        dispatcher = Dispatcher()
        job_key = dispatcher.dispatch_task(jobs.sync_repository, kwargs=job_kwargs, metadata=job_metadata)
        logger.info(f"Syncing LabBook {lb.root_dir} in background job with key {job_key.key_str}")

        return SyncLabbook(job_key=job_key.key_str)


class SetVisibility(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        visibility = graphene.String(required=True)

    new_labbook_edge = graphene.Field(LabbookConnection.Edge)

    @classmethod
    @logged_mutation
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, visibility,
                               client_mutation_id=None):
        # Load LabBook
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())
        # Extract valid Bearer token
        token = None
        if hasattr(info.context.headers, 'environ'):
            if "HTTP_AUTHORIZATION" in info.context.headers.environ:
                token = parse_token(info.context.headers.environ["HTTP_AUTHORIZATION"])

        if not token:
            raise ValueError("Authorization header not provided. Must have a valid session to query for collaborators")

        default_remote = lb.client_config.config['git']['default_remote']
        admin_service = None
        for remote in lb.client_config.config['git']['remotes']:
            if default_remote == remote:
                admin_service = lb.client_config.config['git']['remotes'][remote]['admin_service']
                break

        if not admin_service:
            raise ValueError('admin_service could not be found')

        # Configure git creds
        mgr = GitLabManager(default_remote, admin_service, access_token=token)
        mgr.configure_git_credentials(default_remote, username)

        if visibility not in ['public', 'private']:
            raise ValueError(f'Visibility must be either "public" or "private";'
                             f'("{visibility}" invalid)')
        with lb.lock():
            mgr.set_visibility(namespace=owner, repository_name=labbook_name, visibility=visibility)

        cursor = base64.b64encode(f"{0}".encode('utf-8'))
        lbedge = LabbookConnection.Edge(node=LabbookObject(owner=owner, name=labbook_name),
                                        cursor=cursor)
        return SetVisibility(new_labbook_edge=lbedge)


class ImportRemoteLabbook(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        remote_url = graphene.String(required=True)

    job_key = graphene.String()

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

        gl_mgr = GitLabManager(default_remote, admin_service=admin_service, access_token=token)
        gl_mgr.configure_git_credentials(default_remote, username)

        job_metadata = {'method': 'import_labbook_from_remote'}
        job_kwargs = {
            'remote_url': remote_url,
            'username': username
        }

        dispatcher = Dispatcher()
        job_key = dispatcher.dispatch_task(jobs.import_labbook_from_remote, metadata=job_metadata,
                                           kwargs=job_kwargs)
        logger.info(f"Dispatched import_labbook_from_remote({remote_url}) to Job {job_key}")

        return ImportRemoteLabbook(job_key=job_key.key_str)


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



class AddLabbookCollaborator(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        username = graphene.String(required=True)
        permissions = graphene.String(required=True)

    updated_labbook = graphene.Field(LabbookObject)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, username, permissions,
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

        if permissions == 'readonly':
            perm = ProjectPermissions.READ_ONLY
        elif permissions == 'readwrite':
            perm = ProjectPermissions.READ_WRITE
        elif permissions == 'owner':
            perm = ProjectPermissions.OWNER
        else:
            raise ValueError(f"Unknown permission set: {permissions}")

        mgr = GitLabManager(default_remote, admin_service, token)

        existing_collabs = mgr.get_collaborators(owner, labbook_name)

        if username not in [n[1] for n in existing_collabs]:
            logger.info(f"Adding user {username} to {owner}/{labbook_name}"
                        f"with permission {perm}")
            mgr.add_collaborator(owner, labbook_name, username, perm)
        else:
            logger.warning(f"Changing permission of {username} on"
                           f"{owner}/{labbook_name} to {perm}")
            mgr.delete_collaborator(owner, labbook_name, username)
            mgr.add_collaborator(owner, labbook_name, username, perm)

        create_data = {"owner": owner,
                       "name": labbook_name}

        return AddLabbookCollaborator(updated_labbook=LabbookObject(**create_data))


class DeleteLabbookCollaborator(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        username = graphene.String(required=True)

    updated_labbook = graphene.Field(LabbookObject)

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

        return DeleteLabbookCollaborator(updated_labbook=LabbookObject(**create_data))



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
            mgr.remove_repository(owner, labbook_name)
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
                                                "Identity": id_token}, timeout=30)

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

            return DeleteRemoteLabbook(success=True)
        else:
            logger.info(f"Dry run deleting {labbook_name} from remote repository -- not deleted.")
            return DeleteRemoteLabbook(success=False)


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
