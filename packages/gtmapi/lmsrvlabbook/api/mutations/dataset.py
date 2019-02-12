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
import graphene
import base64
import os

from gtmcore.inventory.inventory import InventoryManager
from gtmcore.logging import LMLogger
from gtmcore.gitlib.gitlab import GitLabManager

from lmsrvcore.auth.user import get_logged_in_username, get_logged_in_author
from lmsrvcore.auth.identity import parse_token
from gtmcore.activity import ActivityStore, ActivityType, ActivityAction, ActivityDetailType, ActivityRecord, \
    ActivityDetailRecord


from lmsrvlabbook.api.objects.dataset import Dataset
from gtmcore.dataset.manifest import Manifest
from lmsrvlabbook.api.connections.dataset import DatasetConnection
from lmsrvlabbook.api.connections.datasetfile import DatasetFile, DatasetFileConnection
from lmsrvlabbook.api.connections.labbook import Labbook, LabbookConnection


logger = LMLogger.get_logger()


class CreateDataset(graphene.relay.ClientIDMutation):
    """Mutation for creation of a new Dataset on disk"""

    class Input:
        name = graphene.String(required=True)
        description = graphene.String(required=True)
        storage_type = graphene.String(required=True)

    # Return the dataset instance
    dataset = graphene.Field(Dataset)

    @classmethod
    def mutate_and_get_payload(cls, root, info, name, description, storage_type, client_mutation_id=None):
        username = get_logged_in_username()
        inv_manager = InventoryManager()

        inv_manager.create_dataset(username=username,
                                   owner=username,
                                   dataset_name=name,
                                   description=description,
                                   storage_type=storage_type,
                                   author=get_logged_in_author())

        return CreateDataset(dataset=Dataset(id="{}&{}".format(username, name),
                                             name=name, owner=username))


class FetchDatasetEdge(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        dataset_name = graphene.String(required=True)

    new_dataset_edge = graphene.Field(DatasetConnection.Edge)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, dataset_name, client_mutation_id=None):
        cursor = base64.b64encode(f"{0}".encode('utf-8'))
        dsedge = DatasetConnection.Edge(node=Dataset(owner=owner, name=dataset_name),
                                        cursor=cursor)

        return FetchDatasetEdge(new_dataset_edge=dsedge)


class ModifyDatasetLink(graphene.relay.ClientIDMutation):
    """"Mutation to link and unlink Datasets from a Project"""

    class Input:
        labbook_owner = graphene.String(required=True, description="Owner of the labbook")
        labbook_name = graphene.String(required=True, description="Name of the labbook")
        dataset_owner = graphene.String(required=True, description="Owner of the dataset to link")
        dataset_name = graphene.String(required=True, description="Name of the dataset to link")
        action = graphene.String(required=True, description="Action to perform, either `link` or `unlink`")
        dataset_url = graphene.String(description="URL to the Dataset to link. Only required when `action=link`")

    new_labbook_edge = graphene.Field(LabbookConnection.Edge)

    @staticmethod
    def _get_remote_domain(dataset_url, dataset_owner, dataset_name):
        """Helper method to get the domain or return none"""
        if "http" in dataset_url:
            dataset_url, _ = dataset_url.split('.git')
            _, _, remote_domain, namespace, name = dataset_url.split("/")
            if namespace != dataset_owner:
                raise ValueError("The dataset owner does not match url")
            if name != dataset_name:
                raise ValueError("The dataset name does not match url")
        else:
            remote_domain = None

        return remote_domain

    @classmethod
    def mutate_and_get_payload(cls, root, info, labbook_owner, labbook_name, dataset_owner, dataset_name, action,
                               dataset_url=None, client_mutation_id=None):
        logged_in_username = get_logged_in_username()
        im = InventoryManager()
        lb = im.load_labbook(logged_in_username, labbook_owner, labbook_name, author=get_logged_in_author())

        with lb.lock():
            if action == 'link':
                if dataset_url:
                    remote_domain = cls._get_remote_domain(dataset_url, dataset_owner, dataset_name)

                    if remote_domain:
                        # Make sure git creds are configured for the remote
                        admin_service = None
                        for remote in lb.client_config.config['git']['remotes']:
                            if remote_domain == remote:
                                admin_service = lb.client_config.config['git']['remotes'][remote]['admin_service']
                                break
                        if "HTTP_AUTHORIZATION" in info.context.headers.environ:
                            token = parse_token(info.context.headers.environ["HTTP_AUTHORIZATION"])
                        else:
                            raise ValueError("Authorization header not provided."
                                             " Must have a valid session to query for collaborators")
                        mgr = GitLabManager(remote_domain, admin_service, token)
                        mgr.configure_git_credentials(remote_domain, logged_in_username)
                else:
                    # Link to local dataset
                    ds = im.load_dataset(logged_in_username, dataset_owner, dataset_name)
                    dataset_url = f"{ds.root_dir}/.git"

                # Link the dataset to the labbook
                ds = im.link_dataset_to_labbook(dataset_url, dataset_owner, dataset_name, lb)
                ds.namespace = dataset_owner

                # Preload the dataloaders
                info.context.dataset_loader.prime(f"{get_logged_in_username()}&{dataset_owner}&{dataset_name}", ds)
                info.context.labbook_loader.prime(f"{get_logged_in_username()}&{labbook_owner}&{labbook_name}", lb)

                # Relink the revision
                m = Manifest(ds, logged_in_username)
                m.link_revision()
            elif action == 'unlink':
                im.unlink_dataset_from_labbook(dataset_owner, dataset_name, lb)
            else:
                raise ValueError("Unsupported action. Use `link` or `unlink`")

            edge = LabbookConnection.Edge(node=Labbook(owner=labbook_owner, name=labbook_name),
                                          cursor=base64.b64encode(f"{0}".encode('utf-8')))

        return ModifyDatasetLink(new_labbook_edge=edge)


class SetDatasetDescription(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        dataset_name = graphene.String(required=True)
        description = graphene.String(required=True)

    updated_dataset = graphene.Field(Dataset)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, dataset_name,
                               description, client_mutation_id=None):
        username = get_logged_in_username()
        ds = InventoryManager().load_dataset(username, owner, dataset_name,
                                             author=get_logged_in_author())
        ds.description = description
        with ds.lock():
            ds.git.add(os.path.join(ds.root_dir, '.gigantum/gigantum.yaml'))
            commit = ds.git.commit('Updating description')

            adr = ActivityDetailRecord(ActivityDetailType.LABBOOK, show=False)
            adr.add_value('text/plain', f"Updated Dataset description: {description}")
            ar = ActivityRecord(ActivityType.LABBOOK,
                                message="Updated Dataset description",
                                linked_commit=commit.hexsha,
                                tags=["dataset"],
                                show=False)
            ar.add_detail_object(adr)
            ars = ActivityStore(ds)
            ars.create_activity_record(ar)
        return SetDatasetDescription(updated_dataset=Dataset(owner=owner, name=dataset_name))


class WriteDatasetReadme(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        dataset_name = graphene.String(required=True)
        content = graphene.String(required=True)

    updated_dataset = graphene.Field(Dataset)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, dataset_name, content, client_mutation_id=None):
        username = get_logged_in_username()
        ds = InventoryManager().load_dataset(username, owner, dataset_name,
                                             author=get_logged_in_author())

        # Write data
        with ds.lock():
            ds.write_readme(content)

        return WriteDatasetReadme(updated_dataset=Dataset(owner=owner, name=dataset_name))
