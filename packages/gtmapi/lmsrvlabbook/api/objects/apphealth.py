import graphene

from gtmcore.logging import LMLogger
from lmsrvcore.telemetry import service_telemetry

logger = LMLogger.get_logger()


class AppHealthMonitor(graphene.ObjectType, interfaces=(graphene.relay.Node,)):
    """A type that represents a Base Image Environment Component"""

    # Representation of how many GBs are free
    disk_available_gb = graphene.Float()

    # Representation of total size in GB
    disk_total_gb = graphene.Float()

    # Warning if space is too low.
    disk_use_warning = graphene.Boolean()

    _telemetry_dict = None

    @classmethod
    def get_node(cls, info, id):
        return AppHealthMonitor(id=None)

    def _get_cached_telemetry(self):
        # Only fetch telemetry once, as it can take a nontrivial amount of time
        if self._telemetry_dict is None:
            self._telemetry_dict = service_telemetry()
        return self._telemetry_dict

    def resolve_disk_available_gb(self, info):
        return self._get_cached_telemetry()['disk']['available']

    def resolve_disk_total_gb(self, info):
        return self._get_cached_telemetry()['disk']['total']

    def resolve_disk_use_warning(self, info):
        return self._get_cached_telemetry()['disk']['lowDiskWarning']
