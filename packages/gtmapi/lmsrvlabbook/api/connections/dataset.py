import graphene
from lmsrvlabbook.api.objects.dataset import Dataset


class DatasetConnection(graphene.relay.Connection):
    """A Connection for paging through datasets that exist locally. """
    class Meta:
        node = Dataset


