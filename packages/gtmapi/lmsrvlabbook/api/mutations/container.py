import uuid
from urllib.parse import quote_plus
import graphene

from confhttpproxy import ProxyRouter

from gtmcore.inventory.inventory import InventoryManager
from gtmcore.labbook.labbook import LabBook
from gtmcore.exceptions import GigantumException
from gtmcore.container.container import ContainerOperations
from gtmcore.mitmproxy.mitmproxy import MITMProxyOperations
from gtmcore.container.jupyter import check_jupyter_reachable, start_jupyter
from gtmcore.container.rserver import start_rserver
from gtmcore.container.bundledapp import start_bundled_app
from gtmcore.logging import LMLogger
from gtmcore.activity.services import start_labbook_monitor
from gtmcore.environment.bundledapp import BundledAppManager

from lmsrvcore.auth.user import get_logged_in_username, get_logged_in_author

logger = LMLogger.get_logger()


def unique_id() -> str:
    """This is used to, e.g., identify a specific running labbook.

    This allows us to link things like activity monitors, etc.
    It can safely be improved or changed, as consumers should only expect some "random" string."""
    return uuid.uuid4().hex[:10]


class StartDevTool(graphene.relay.ClientIDMutation):
    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        dev_tool = graphene.String(required=True)
        container_override_id = graphene.String(required=False)

    # Return the Environment instance
    path = graphene.String()

    @classmethod
    def _start_dev_tool(cls, labbook: LabBook, username: str, dev_tool: str, container_override_id: str = None):
        router = ProxyRouter.get_proxy(labbook.client_config.config['proxy'])
        bam = BundledAppManager(labbook)
        bundled_apps = bam.get_bundled_apps()
        bundled_app_names = [x for x in bundled_apps]

        if dev_tool == "rstudio":
            suffix = cls._start_rstudio(labbook, router, username)
        elif dev_tool in ["jupyterlab", "notebook"]:
            # Note that starting the dev tool is identical whether we're targeting jupyterlab or notebook
            suffix = cls._start_jupyter_tool(labbook, router, username, container_override_id)
        elif dev_tool in bundled_app_names:
            app_data = bundled_apps[dev_tool]
            app_data['name'] = dev_tool
            suffix = cls._start_bundled_app(labbook, router, username, app_data, container_override_id)
        else:
            raise GigantumException(f"'{dev_tool}' not currently supported as a Dev Tool")

        # Don't include the port in the path if running on 80
        apparent_proxy_port = labbook.client_config.config['proxy']["apparent_proxy_port"]
        if apparent_proxy_port == 80:
            path = suffix
        else:
            path = f':{apparent_proxy_port}{suffix}'

        return path

    @classmethod
    def _start_jupyter_tool(cls, labbook: LabBook, router: ProxyRouter, username: str,
                            container_override_id: str = None):
        tool_port = 8888
        labbook_ip = ContainerOperations.get_labbook_ip(labbook, username)
        labbook_endpoint = f'http://{labbook_ip}:{tool_port}'

        matched_routes = router.get_matching_routes(labbook_endpoint, 'jupyter')

        run_start_jupyter = True
        suffix = None
        if len(matched_routes) == 1:
            logger.info(f'Found existing Jupyter instance in route table for {str(labbook)}.')
            suffix = matched_routes[0]

            # wait for jupyter to be up
            try:
                check_jupyter_reachable(labbook_ip, tool_port, suffix)
                run_start_jupyter = False
            except GigantumException:
                logger.warning(f'Detected stale route. Attempting to restart Jupyter and clean up route table.')
                router.remove(suffix[1:])

        elif len(matched_routes) > 1:
            raise ValueError(f"Multiple Jupyter instances found in route table for {str(labbook)}! Restart container.")

        if run_start_jupyter:
            rt_prefix = unique_id()
            rt_prefix, _ = router.add(labbook_endpoint, f'jupyter/{rt_prefix}')

            # Start jupyterlab
            suffix = start_jupyter(labbook, username, tag=container_override_id, proxy_prefix=rt_prefix)

            # Ensure we start monitor IFF jupyter isn't already running.
            start_labbook_monitor(labbook, username, 'jupyterlab',
                                  url=f'{labbook_endpoint}/{rt_prefix}',
                                  author=get_logged_in_author())

        return suffix

    @classmethod
    def _start_rstudio(cls, labbook: LabBook, router: ProxyRouter, username: str,
                       container_override_id: str = None):
        mitm_url, pr_suffix = MITMProxyOperations.configure_mitmroute(labbook, router, username)

        # All messages will come through MITM, so we don't need to monitor rserver directly
        start_rserver(labbook, username, tag=container_override_id)

        # Ensure monitor is running
        start_labbook_monitor(labbook, username, "rstudio",
                              # the endpoint for the NGINX proxy running inside the mitmproxy container
                              # (not the rserver) which maps `/rserver/<whatever>/<foo>` to `/<foo>`.
                              # But url isn't used currently by monitor_rserver.RServerMonitor!
                              url=mitm_url,
                              author=get_logged_in_author())

        return pr_suffix

    @classmethod
    def _start_bundled_app(cls, labbook: LabBook, router: ProxyRouter, username: str, bundled_app: dict,
                           container_override_id: str = None):
        tool_port = bundled_app['port']
        labbook_ip = ContainerOperations.get_labbook_ip(labbook, username)
        endpoint = f'http://{labbook_ip}:{tool_port}'

        route_prefix = quote_plus(bundled_app['name'])

        matched_routes = router.get_matching_routes(endpoint, route_prefix)

        run_command = True
        suffix = None
        if len(matched_routes) == 1:
            logger.info(f"Found existing {bundled_app['name']} in route table for {str(labbook)}.")
            suffix = matched_routes[0]
            run_command = False

        elif len(matched_routes) > 1:
            raise ValueError(f"Multiple {bundled_app['name']} instances found in route table "
                             f"for {str(labbook)}! Restart container.")

        if run_command:
            logger.info(f"Adding {bundled_app['name']} to route table for {str(labbook)}.")
            suffix, _ = router.add(endpoint, route_prefix)
            suffix = "/" + suffix

            # Start app
            logger.info(f"Starting {bundled_app['name']} in {str(labbook)}.")
            start_bundled_app(labbook, username, bundled_app['command'], tag=container_override_id)

        return suffix

    @classmethod
    def mutate_and_get_payload(cls, root: str, info: str, owner: str, labbook_name: str, dev_tool: str,
                               container_override_id: str = None, client_mutation_id: str = None):
        username = get_logged_in_username()
        labbook = InventoryManager().load_labbook(username, owner, labbook_name,
                                                  author=get_logged_in_author())

        with labbook.lock(failfast=True):
            path = cls._start_dev_tool(labbook, username, dev_tool.lower(), container_override_id)

        return StartDevTool(path=path)
