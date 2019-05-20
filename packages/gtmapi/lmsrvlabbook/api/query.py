import base64
from typing import List
import graphene
import os

from gtmcore.logging import LMLogger
from gtmcore.configuration import Configuration
from gtmcore.dispatcher import Dispatcher
from gtmcore.environment import BaseRepository
from gtmcore.labbook.schemas import CURRENT_SCHEMA
from gtmcore.dataset.storage import get_storage_backend_descriptions

from lmsrvcore.api.objects.user import UserIdentity
from lmsrvcore.api.connections import ListBasedConnection

from lmsrvlabbook.api.objects.labbook import Labbook
from lmsrvlabbook.api.objects.labbooklist import LabbookList
from lmsrvlabbook.api.objects.datasetlist import DatasetList
from lmsrvlabbook.api.objects.basecomponent import BaseComponent
from lmsrvlabbook.api.objects.jobstatus import JobStatus
from lmsrvlabbook.api.connections.environment import BaseComponentConnection
from lmsrvlabbook.api.connections.jobstatus import JobStatusConnection
from lmsrvlabbook.api.objects.datasettype import DatasetType
from lmsrvlabbook.api.objects.dataset import Dataset
from lmsrvlabbook.api.objects.apphealth import AppHealthMonitor

logger = LMLogger.get_logger()


class AppQueries(graphene.ObjectType):
    """ Queries for the info about the running app instance. """

    # Return app build date and hash
    build_info = graphene.String()

    # Return whether this has CUDA installed and can run GPU-enabled projects
    cuda_available = graphene.Boolean()

    # This indicates the most-recent labbook schema version.
    # Nominal usage of this field is to see if any given labbook is behind this version.
    # Any new labbook will be created with this schema version.
    current_labbook_schema_version = graphene.Int()

    # Used to query for specific background jobs.
    # job_id is in the format of `rq:job:uuid`, though it should never need to be parsed.
    job_status = graphene.Field(JobStatus, job_id=graphene.String())

    # All background jobs in the system: Queued, Completed, Failed, and Started.
    background_jobs = graphene.relay.ConnectionField(JobStatusConnection)

    # Get the current logged in user identity, primarily used when running offline
    user_identity = graphene.Field(UserIdentity)

    app_health = graphene.Field(AppHealthMonitor)

    def resolve_build_info(self, info):
        """Return this LabManager build info (hash, build timestamp, etc)"""
        # TODO - CUDA version should possibly go in here
        build_info = Configuration().config.get('build_info') \
                     or "Unable to retrieve version"
        return build_info

    def resolve_cuda_available(self, info):
        """Return the CUDA version of the host machine. Non-null implies GPU available"""
        if os.environ.get('NVIDIA_DRIVER_VERSION'):
            return True
        else:
            return False

    def resolve_current_labbook_schema_version(self, info):
        """Return the current LabBook schema version"""
        return CURRENT_SCHEMA

    def resolve_job_status(self, info, job_id: str):
        """Method to return a graphene Labbok instance based on the name

        Uses the "currently logged in" user

        Args:
            job_id(dict): Contains user details

        Returns:
            JobStatus
        """
        return JobStatus(job_id)

    def resolve_background_jobs(self, info, **kwargs):
        """Method to return a all background jobs the system is aware of: Queued, Started, Finished, Failed.

        Returns:
            list(JobStatus)
        """
        job_dispatcher = Dispatcher()

        edges: List[str] = [j.job_key.key_str for j in job_dispatcher.all_jobs]
        cursors = [base64.b64encode(f"{str(cnt)}".encode('utf-8')) for cnt, x in enumerate(edges)]

        # Process slicing and cursor args
        lbc = ListBasedConnection(edges, cursors, kwargs)
        lbc.apply()

        edge_objs = []
        for edge, cursor in zip(lbc.edges, lbc.cursors):
            edge_objs.append(JobStatusConnection.Edge(node=JobStatus(edge), cursor=cursor))

        return JobStatusConnection(edges=edge_objs, page_info=lbc.page_info)

    def resolve_user_identity(self, info):
        """Method to return a graphene UserIdentity instance based on the current logged (both on & offline) user

        Returns:
            UserIdentity
        """
        return UserIdentity()

    def resolve_app_health(self, info):
        return AppHealthMonitor()


class LabbookQuery(AppQueries, graphene.ObjectType):
    """Entry point for all LabBook queryable fields"""
    # Node Fields for Relay
    node = graphene.relay.Node.Field()

    # Retrieve multiple nodes for Relay
    nodes = graphene.List(graphene.relay.Node, ids=graphene.List(graphene.String))

    labbook = graphene.Field(Labbook, owner=graphene.String(), name=graphene.String())

    dataset = graphene.Field(Dataset, owner=graphene.String(), name=graphene.String())

    # A field to interact with listing labbooks locally and remote
    labbook_list = graphene.Field(LabbookList)

    # A field to interact with listing datasets locally and remote
    dataset_list = graphene.Field(DatasetList)

    # Base Image Repository Interface
    available_bases = graphene.relay.ConnectionField(BaseComponentConnection)

    # List available types of datasets
    available_dataset_types = graphene.List(DatasetType)

    def resolve_nodes(self, info, ids):
        return [graphene.relay.Node.get_node_from_global_id(info, x) for x in ids]

    def resolve_labbook(self, info, owner: str, name: str):
        """Method to return a graphene Labbook instance based on the name

        Uses the "currently logged in" user

        Args:
            owner(str): Username of the owner (aka namespace)
            name(str): Name of the LabBook

        Returns:
            Labbook
        """
        # Load the labbook data via a dataloader
        return Labbook(id="{}&{}".format(owner, name),
                       name=name, owner=owner)

    def resolve_dataset(self, info, owner: str, name: str):
        """Method to return a graphene Dataset instance based on the name

        Uses the "currently logged in" user

        Args:
            owner(str): Username of the owner (aka namespace)
            name(str): Name of the Dataset

        Returns:
            Labbook
        """
        return Dataset(id="{}&{}".format(owner, name),
                       name=name, owner=owner)

    def resolve_labbook_list(self, info):
        """Return a labbook list object, which is just a container so the id is empty"""
        return LabbookList(id="")

    def resolve_dataset_list(self, info):
        """Return a dataset list object, which is just a container so the id is empty"""
        return DatasetList(id="")

    def resolve_available_bases(self, info, **kwargs):
        """Method to return a all graphene BaseImages that are available

        Returns:
            list(Labbook)
        """
        repo = BaseRepository()
        edges = repo.get_base_list()
        cursors = [base64.b64encode("{}".format(cnt).encode("UTF-8")).decode("UTF-8") for cnt, x in enumerate(edges)]

        # Process slicing and cursor args
        lbc = ListBasedConnection(edges, cursors, kwargs)
        lbc.apply()

        # Get BaseImage instances
        edge_objs = []
        for edge, cursor in zip(lbc.edges, lbc.cursors):
            edge_objs.append(BaseComponentConnection.Edge(node=BaseComponent(repository=edge['repository'],
                                                                             component_id=edge['id'],
                                                                             revision=int(edge['revision'])),
                                                          cursor=cursor))

        return BaseComponentConnection(edges=edge_objs, page_info=lbc.page_info)

    def resolve_available_dataset_types(self, info):
        """Method to resolve a list of available dataset types

        Returns:
            list
        """
        dataset_types = list()
        for metadata in get_storage_backend_descriptions():
            d = DatasetType()
            d.id = metadata['storage_type']
            d.storage_type = metadata['storage_type']
            d.name = metadata['name']
            d.description = metadata['description']
            d.readme = metadata['readme']
            d.tags = metadata['tags']
            d.icon = metadata['icon']
            d.url = metadata['url']
            dataset_types.append(d)
        return dataset_types
