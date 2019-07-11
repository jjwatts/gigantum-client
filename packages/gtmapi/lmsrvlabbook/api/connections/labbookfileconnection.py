import graphene
from lmsrvlabbook.api.objects.labbookfile import LabbookFile


class LabbookFileConnection(graphene.relay.Connection):
    """A connection for paging through labbook files. """
    class Meta:
        node = LabbookFile
