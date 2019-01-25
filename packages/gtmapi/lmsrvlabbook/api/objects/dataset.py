import graphene
import base64

from gtmcore.activity import ActivityStore

from lmsrvcore.auth.identity import parse_token
from lmsrvcore.auth.user import get_logged_in_username
from lmsrvcore.api.interfaces import GitRepository
from lmsrvcore.api.connections import ListBasedConnection

from gtmcore.dataset.manifest import Manifest
from gtmcore.gitlib.gitlab import GitLabManager
from gtmcore.inventory.inventory import InventoryManager

from lmsrvlabbook.api.objects.datasettype import DatasetType
from lmsrvlabbook.api.connections.activity import ActivityConnection
from lmsrvlabbook.api.objects.activity import ActivityDetailObject, ActivityRecordObject
from lmsrvlabbook.api.connections.datasetfile import DatasetFileConnection, DatasetFile


class Dataset(graphene.ObjectType, interfaces=(graphene.relay.Node, GitRepository)):
    """A type representing a Dataset and all of its contents

    Datasets are uniquely identified by both the "owner" and the "name" of the Dataset

    """
    # A short description of the dataset limited to 140 UTF-8 characters
    description = graphene.String()

    # The DatasetType for this dataset
    dataset_type = graphene.Field(DatasetType)

    # Data schema version of this dataset. It may be behind the most recent version and need
    # to be upgraded.
    schema_version = graphene.Int()

    # Creation date/timestamp in UTC in ISO format
    created_on_utc = graphene.types.datetime.DateTime()

    # Store collaborator data so it is only fetched once per request
    _collaborators = None

    # List of collaborators
    collaborators = graphene.List(graphene.String)

    # A boolean indicating if the current user can manage collaborators
    can_manage_collaborators = graphene.Boolean()

    # Last modified date/timestamp in UTC in ISO format
    modified_on_utc = graphene.types.datetime.DateTime()

    # Connection to Activity Entries
    activity_records = graphene.relay.ConnectionField(ActivityConnection)

    # List of all files and directories within the section
    all_files = graphene.relay.ConnectionField(DatasetFileConnection)

    # Access a detail record directly, which is useful when fetching detail items
    detail_record = graphene.Field(ActivityDetailObject, key=graphene.String())
    detail_records = graphene.List(ActivityDetailObject, keys=graphene.List(graphene.String))

    visibility = graphene.String()

    # Get the URL of the remote origin
    default_remote = graphene.String()

    @classmethod
    def get_node(cls, info, id):
        """Method to resolve the object based on it's Node ID"""
        # Parse the key
        owner, name = id.split("&")

        return Dataset(id="{}&{}".format(owner, name),
                       name=name, owner=owner)

    def resolve_id(self, info):
        """Resolve the unique Node id for this object"""
        if not self.id:
            if not self.owner or not self.name:
                raise ValueError("Resolving a Dataset Node ID requires owner and name to be set")
            self.id = f"{self.owner}&{self.name}"

        return self.id

    def resolve_description(self, info):
        """Get number of commits the active_branch is behind its remote counterpart.
        Returns 0 if up-to-date or if local only."""
        if not self.description:
            return info.context.dataset_loader.load(f"{get_logged_in_username()}&{self.owner}&{self.name}").then(
                lambda dataset: dataset.description)

        return self.description

    def resolve_schema_version(self, info):
        """Get number of commits the active_branch is behind its remote counterpart.
        Returns 0 if up-to-date or if local only."""
        return info.context.dataset_loader.load(f"{get_logged_in_username()}&{self.owner}&{self.name}").then(
            lambda dataset: dataset.schema)

    def resolve_created_on_utc(self, info):
        """Return the creation timestamp (if available - otherwise empty string)

        Args:
            info:

        Returns:

        """
        return info.context.dataset_loader.load(f"{get_logged_in_username()}&{self.owner}&{self.name}").then(
            lambda dataset: dataset.creation_date)

    def _fetch_collaborators(self, dataset, info):
        """Helper method to fetch this dataset's collaborators

        Args:
            info: The graphene info object for this requests

        """
        # TODO: Future work will look up remote in Dataset data, allowing user to select remote.
        default_remote = dataset.client_config.config['git']['default_remote']
        admin_service = None
        for remote in dataset.client_config.config['git']['remotes']:
            if default_remote == remote:
                admin_service = dataset.client_config.config['git']['remotes'][remote]['admin_service']
                break

        # Extract valid Bearer token
        if "HTTP_AUTHORIZATION" in info.context.headers.environ:
            token = parse_token(info.context.headers.environ["HTTP_AUTHORIZATION"])
        else:
            raise ValueError("Authorization header not provided. Must have a valid session to query for collaborators")

        # Get collaborators from remote service
        mgr = GitLabManager(default_remote, admin_service, token)
        try:
            self._collaborators = mgr.get_collaborators(self.owner, self.name)
        except ValueError:
            # If ValueError Raised, assume repo doesn't exist yet
            self._collaborators = []

    def helper_resolve_collaborators(self, dataset, info):
        """Helper method to fetch this dataset's collaborators and generate the resulting list of collaborators

        Args:
            info: The graphene info object for this requests

        """
        self._fetch_collaborators(dataset, info)

        return [x[1] for x in self._collaborators]

    def resolve_collaborators(self, info):
        """Method to get the list of collaborators for a dataset

        Args:
            info:

        Returns:

        """
        if self._collaborators is None:
            # If here, put the fetch for collaborators in the promise
            return info.context.dataset_loader.load(f"{get_logged_in_username()}&{self.owner}&{self.name}").then(
                lambda dataset: self.helper_resolve_collaborators(dataset, info))

        # If here, you've already fetched the collaborators once and it's already saved in this Dataset object
        return [x[1] for x in self._collaborators]

    def helper_resolve_can_manage_collaborators(self, dataset, info):
        """Helper method to fetch this dataset's collaborators and check if user can manage collaborators

        Args:
            info: The graphene info object for this requests

        """
        self._fetch_collaborators(dataset, info)

        can_manage = False
        username = get_logged_in_username()
        for c in self._collaborators:
            if c[1] == username:
                if c[2] is True:
                    can_manage = True

        return can_manage

    def resolve_can_manage_collaborators(self, info):
        """Method to check if the user is the "owner" of the dataset and can manage collaborators

        Args:
            info:

        Returns:

        """
        if self._collaborators is None:
            # If here, put the fetch for collaborators in the promise
            return info.context.dataset_loader.load(f"{get_logged_in_username()}&{self.owner}&{self.name}").then(
                lambda dataset: self.helper_resolve_can_manage_collaborators(dataset, info))

        can_manage = False
        username = get_logged_in_username()
        for c in self._collaborators:
            if c[1] == username:
                if c[2] is True:
                    can_manage = True

        return can_manage

    def resolve_modified_on_utc(self, info):
        """Return the creation timestamp (if available - otherwise empty string)

        Args:
            args:
            context:
            info:

        Returns:

        """
        return info.context.dataset_loader.load(f"{get_logged_in_username()}&{self.owner}&{self.name}").then(
            lambda dataset: dataset.modified_on)

    def helper_resolve_activity_records(self, dataset, kwargs):
        """Helper method to generate ActivityRecord objects and populate the connection"""
        # Create instance of ActivityStore for this dataset
        store = ActivityStore(dataset)

        if kwargs.get('before') or kwargs.get('last'):
            raise ValueError("Only `after` and `first` arguments are supported when paging activity records")

        # Get edges and cursors
        edges = store.get_activity_records(after=kwargs.get('after'), first=kwargs.get('first'))
        if edges:
            cursors = [x.commit for x in edges]
        else:
            cursors = []

        # Get ActivityRecordObject instances
        edge_objs = []
        for edge, cursor in zip(edges, cursors):
            edge_objs.append(
                ActivityConnection.Edge(node=ActivityRecordObject(id=f"dataset&{self.owner}&{self.name}&{edge.commit}",
                                                                  owner=self.owner,
                                                                  name=self.name,
                                                                  _repository_type='dataset',
                                                                  commit=edge.commit,
                                                                  _activity_record=edge),
                                        cursor=cursor))

        # Create page info based on first commit. Since only paging backwards right now, just check for commit
        if edges:
            has_next_page = True

            # Get the message of the linked commit and check if it is the non-activity record dataset creation commit
            if edges[-1].linked_commit != "no-linked-commit":
                linked_msg = dataset.git.log_entry(edges[-1].linked_commit)['message']
                if linked_msg == f"Creating new empty Dataset: {dataset.name}" and "_GTM_ACTIVITY_" not in linked_msg:
                    # if you get here, this is the first activity record
                    has_next_page = False

            end_cursor = cursors[-1]
        else:
            has_next_page = False
            end_cursor = None

        page_info = graphene.relay.PageInfo(has_next_page=has_next_page, has_previous_page=False, end_cursor=end_cursor)

        return ActivityConnection(edges=edge_objs, page_info=page_info)

    def resolve_activity_records(self, info, **kwargs):
        """Method to page through branch Refs

        Args:
            kwargs:
            info:

        Returns:

        """
        return info.context.dataset_loader.load(f"{get_logged_in_username()}&{self.owner}&{self.name}").then(
            lambda dataset: self.helper_resolve_activity_records(dataset, kwargs))

    def resolve_detail_record(self, info, key):
        """Method to resolve the detail record object

        Args:
            args:
            info:

        Returns:

        """
        return ActivityDetailObject(id=f"dataset&{self.owner}&{self.name}&{key}",
                                    owner=self.owner,
                                    name=self.name,
                                    _repository_type='dataset',
                                    key=key)

    def resolve_detail_records(self, info, keys):
        """Method to resolve multiple detail record objects

        Args:
            args:
            info:

        Returns:

        """
        return [ActivityDetailObject(id=f"dataset&{self.owner}&{self.name}&{key}",
                                     owner=self.owner,
                                     name=self.name,
                                     _repository_type='dataset',
                                     key=key) for key in keys]

    def resolve_dataset_type(self, info, **kwargs):
        """Method to resolve a DatasetType object for the Dataset

        Args:
            args:
            info:

        Returns:

        """
        return info.context.dataset_loader.load(f"{get_logged_in_username()}&{self.owner}&{self.name}").then(
            lambda dataset: DatasetType(id=dataset.storage_type, storage_type=dataset.storage_type))

    def helper_resolve_all_files(self, dataset, kwargs):
        """Helper method to populate the DatasetFileConnection"""
        manifest = Manifest(dataset, get_logged_in_username())

        # Generate naive cursors
        # TODO: Use manifest pagination interface
        edges = manifest.list()
        cursors = [base64.b64encode("{}".format(cnt).encode("UTF-8")).decode("UTF-8") for cnt, x in enumerate(edges)]

        # Process slicing and cursor args
        lbc = ListBasedConnection(edges, cursors, kwargs)
        lbc.apply()

        edge_objs = []
        for edge, cursor in zip(lbc.edges, lbc.cursors):
            create_data = {"owner": self.owner,
                           "name": self.name,
                           "key": edge['key'],
                           "_file_info": edge}
            edge_objs.append(DatasetFileConnection.Edge(node=DatasetFile(**create_data), cursor=cursor))

        return DatasetFileConnection(edges=edge_objs, page_info=lbc.page_info)

    def resolve_all_files(self, info, **kwargs):
        """Resolver for getting all files in a Dataset"""
        return info.context.dataset_loader.load(f"{get_logged_in_username()}&{self.owner}&{self.name}").then(
            lambda dataset: self.helper_resolve_all_files(dataset, kwargs))

    @staticmethod
    def helper_resolve_visibility(dataset, info):
        # TODO: Future work will look up remote in Dataset data, allowing user to select remote.
        default_remote = dataset.client_config.config['git']['default_remote']
        admin_service = None
        for remote in dataset.client_config.config['git']['remotes']:
            if default_remote == remote:
                admin_service = dataset.client_config.config['git']['remotes'][remote]['admin_service']
                break

        # Extract valid Bearer token
        if "HTTP_AUTHORIZATION" in info.context.headers.environ:
            token = parse_token(info.context.headers.environ["HTTP_AUTHORIZATION"])
        else:
            raise ValueError("Authorization header not provided. Must have a valid session to query for collaborators")

        # Get collaborators from remote service
        mgr = GitLabManager(default_remote, admin_service, token)
        try:
            owner = InventoryManager().query_owner(dataset)
            d = mgr.repo_details(namespace=owner, repository_name=dataset.name)
            return d.get('visibility')
        except ValueError:
            return "local"

    def resolve_visibility(self, info):
        """ Return string indicating visibility of project from GitLab:
         "public", "private", or "internal". """

        return info.context.dataset_loader.load(f"{get_logged_in_username()}&{self.owner}&{self.name}").then(
            lambda dataset: self.helper_resolve_visibility(dataset, info))

    @staticmethod
    def helper_resolve_default_remote(dataset):
        """Helper to extract the default remote from a dataset"""
        remotes = dataset.git.list_remotes()
        if remotes:
            url = [x['url'] for x in remotes if x['name'] == 'origin']
            if url:
                return url[0]
            else:
                dataset.warning(f"There exist remotes in {str(dataset)}, but no origin found.")
        return None

    def resolve_default_remote(self, info):
        """Return True if no untracked files and no uncommitted changes (i.e., Git repo clean)

        Args:
            args:
            context:
            info:

        Returns:

        """
        return info.context.dataset_loader.load(f"{get_logged_in_username()}&{self.owner}&{self.name}").then(
            lambda dataset: self.helper_resolve_default_remote(dataset))
