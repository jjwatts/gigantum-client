import base64
import graphene

from lmsrvlabbook.api.connections.dataset import Dataset, DatasetConnection

from gtmcore.inventory.inventory import InventoryManager

from lmsrvcore.auth.user import get_logged_in_username
from lmsrvcore.api.connections import ListBasedConnection


class DatasetList(graphene.ObjectType, interfaces=(graphene.relay.Node,)):
    """A type simply used as a container to group local and remote Datasets for better relay support

    Dataset and RemoteDataset objects are uniquely identified by both the "owner" and the "name" of the Dataset

    NOTE: RemoteDatasets require all fields to be explicitly set as there is no current way to asynchronously retrieve
          the data
    """
    # List of specific local datasets based on Node ID
    local_by_id = graphene.List(Dataset, ids=graphene.List(graphene.String))

    # Connection to locally available datasets
    local_datasets = graphene.relay.ConnectionField(DatasetConnection,
                                                    order_by=graphene.String(default_value="name"),
                                                    sort=graphene.String(default_value="asc"))

    @classmethod
    def get_node(cls, info, id):
        """Method to resolve the object based on it's Node ID"""
        # This object doesn't really have a node because it's simply container
        return DatasetList(id=id)

    def resolve_id(self, info):
        """Resolve the unique Node id for this object"""
        # This object doesn't really have a node because it's simply container
        return ""

    def resolve_local_by_id(self, info, ids):
        """Method to return graphene Dataset instances based on a list of Global Node IDs

        Uses the "currently logged in" user

        Args:
            ids(list): List of Node IDs for the local datasets to return

        Returns:
            list(Dataset)
        """
        return [graphene.Node.get_node_from_global_id(info, x) for x in ids]

    def resolve_local_datasets(self, info, order_by: str, sort: str, **kwargs):
        """Method to return all graphene Dataset instances for the logged in user available locally

        Uses the "currently logged in" user

        Args:
            order_by(str): String specifying how datasets should be sorted
            sort(str): 'desc' for descending, 'asc' for ascending (default)

        Returns:
            list(Dataset)
        """
        username = get_logged_in_username()

        if sort == "desc":
            reverse = True
        elif sort == "asc":
            reverse = False
        else:
            raise ValueError(f"Unsupported sort_str: {sort}. Use `desc`, `asc`")

        # Collect all datasets for all owners
        local_datasets = InventoryManager().list_datasets(username=username, sort_mode=order_by)
        if reverse:
            local_datasets.reverse()

        edges = [(ds.namespace, ds.name) for ds in local_datasets]
        cursors = [base64.b64encode("{}".format(cnt).encode("UTF-8")).decode("UTF-8") for cnt, x in enumerate(edges)]

        # Process slicing and cursor args
        lbc = ListBasedConnection(edges, cursors, kwargs)
        lbc.apply()

        # Get Dataset instances
        edge_objs = []
        for edge, cursor in zip(lbc.edges, lbc.cursors):
            create_data = {"id": "{}&{}".format(edge[0], edge[1]),
                           "name": edge[1],
                           "owner": edge[0]}

            edge_objs.append(DatasetConnection.Edge(node=Dataset(**create_data),
                                                    cursor=cursor))

        return DatasetConnection(edges=edge_objs, page_info=lbc.page_info)
