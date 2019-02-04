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
import uuid
from typing import Optional

import graphene
from confhttpproxy import ProxyRouter

from gtmcore.inventory.inventory import InventoryManager
from gtmcore.labbook.labbook import LabBook
from gtmcore.exceptions import GigantumException
from gtmcore.container.container import ContainerOperations
from gtmcore.mitmproxy.mitmproxy import MITMProxyOperations
from gtmcore.container.jupyter import check_jupyter_reachable, start_jupyter
from gtmcore.container.rserver import start_rserver
from gtmcore.logging import LMLogger
from gtmcore.activity.services import start_labbook_monitor

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
    def _start_dev_tool(cls, lb: LabBook, username: str, dev_tool: str, container_override_id: str = None):
        pr = ProxyRouter.get_proxy(lb.client_config.config['proxy'])

        if dev_tool == "rstudio":
            suffix = cls._start_rstudio(lb, pr, username)
        elif dev_tool in ["jupyterlab", "notebook"]:
            # Note that starting the dev tool is identical whether we're targeting jupyterlab or notebook
            suffix = cls._start_jupyter_tool(lb, pr, username, container_override_id)
        else:
            raise GigantumException(f"'{dev_tool}' not currently supported as a Dev Tool")

        # Don't include the port in the path if running on 80
        apparent_proxy_port = lb.client_config.config['proxy']["apparent_proxy_port"]
        if apparent_proxy_port == 80:
            path = suffix
        else:
            path = f':{apparent_proxy_port}{suffix}'

        return path

    @classmethod
    def _start_jupyter_tool(cls, lb: LabBook, pr: ProxyRouter, username: str,
                            container_override_id: str = None):
        tool_port = 8888
        lb_ip = ContainerOperations.get_labbook_ip(lb, username)
        lb_endpoint = f'http://{lb_ip}:{tool_port}'

        matched_routes = pr.get_matching_routes(lb_endpoint, 'jupyter')

        run_start_jupyter = True
        suffix = None
        if len(matched_routes) == 1:
            logger.info(f'Found existing Jupyter instance in route table for {str(lb)}.')
            suffix = matched_routes[0]

            # wait for jupyter to be up
            try:
                check_jupyter_reachable(lb_ip, tool_port, suffix)
                run_start_jupyter = False
            except GigantumException:
                logger.warning(f'Detected stale route. Attempting to restart Jupyter and clean up route table.')
                pr.remove(suffix[1:])

        elif len(matched_routes) > 1:
            raise ValueError(f"Multiple Jupyter instances found in route table for {str(lb)}! Restart container.")

        if run_start_jupyter:
            rt_prefix = unique_id()
            rt_prefix, _ = pr.add(lb_endpoint, f'jupyter/{rt_prefix}')

            # Start jupyterlab
            suffix = start_jupyter(lb, username, tag=container_override_id, proxy_prefix=rt_prefix)

            # Ensure we start monitor IFF jupyter isn't already running.
            start_labbook_monitor(lb, username, 'jupyterlab',
                                  url=f'{lb_endpoint}/{rt_prefix}',
                                  author=get_logged_in_author())

        return suffix

    @classmethod
    def _start_rstudio(cls, lb: LabBook, pr: ProxyRouter, username: str,
                       container_override_id: str = None):
        lb_ip = ContainerOperations.get_labbook_ip(lb, username)
        lb_endpoint = f'http://{lb_ip}:8787'

        mitm_endpoint = MITMProxyOperations.get_mitmendpoint(lb_endpoint)
        # start mitm proxy if it doesn't exist
        if mitm_endpoint is None:

            # get a proxy prefix
            unique_key = unique_id()

            # start proxy
            mitm_endpoint = MITMProxyOperations.start_mitm_proxy(lb_endpoint, unique_key)

            # Ensure we start monitor when starting MITM proxy
            start_labbook_monitor(lb, username, "rstudio",
                                  # This is the endpoint for the proxy and not the rserver?
                                  url=f'{lb_endpoint}/{unique_key}',
                                  author=get_logged_in_author())

            # All messages will come through MITM, so we don't need to monitor rserver directly
            start_rserver(lb, username, tag=container_override_id)

            # add route
            rt_prefix, _ = pr.add(mitm_endpoint, f'rserver/{unique_key}/')
            # Warning: RStudio will break if there is a trailing slash!
            suffix = f'/{rt_prefix}'

        else:
            # existing route to MITM or not?
            matched_routes = pr.get_matching_routes(mitm_endpoint, 'rserver')

            if len(matched_routes) == 1:
                suffix = matched_routes[0]
            elif len(matched_routes) == 0:
                logger.warning('Creating missing route for existing RStudio mitmproxy_proxy')
                # TODO DC: This feels redundant with already getting the mitm_endpoint above
                # Can we refactor this into a more coherent single operation? Maybe an MITMProxy instance?
                unique_key = MITMProxyOperations.get_mitmkey(lb_endpoint)
                # add route
                rt_prefix, _ = pr.add(mitm_endpoint, f'rserver/{unique_key}/')
                # Warning: RStudio will break if there is a trailing slash!
                suffix = f'/{rt_prefix}'
            else:
                raise ValueError(f"Multiple RStudio proxy instances for {str(lb)}. Please restart the Project "
                                 "or manually delete stale containers.")

        return suffix

    @classmethod
    def mutate_and_get_payload(cls, root: str, info: str, owner: str, labbook_name: str, dev_tool: str,
                               container_override_id: str = None, client_mutation_id: str = None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())

        with lb.lock(failfast=True):
            path = cls._start_dev_tool(lb, username, dev_tool.lower(), container_override_id)

        return StartDevTool(path=path)
