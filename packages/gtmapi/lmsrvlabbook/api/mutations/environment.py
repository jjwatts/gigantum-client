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
import os
import graphene
import confhttpproxy

from gtmcore.configuration import get_docker_client
from gtmcore.imagebuilder import ImageBuilder
from gtmcore.dispatcher import Dispatcher, jobs

from gtmcore.inventory.inventory import InventoryManager
from gtmcore.container.container import ContainerOperations
from gtmcore.container.utils import infer_docker_image_name
from gtmcore.workflows import GitWorkflow
from gtmcore.logging import LMLogger
from gtmcore.activity.services import stop_labbook_monitor

from lmsrvcore.auth.user import get_logged_in_username, get_logged_in_author
from lmsrvlabbook.api.objects.environment import Environment


logger = LMLogger.get_logger()


class BuildImage(graphene.relay.ClientIDMutation):
    """Mutator to build a LabBook's Docker Image"""

    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)
        no_cache = graphene.Boolean(required=False)

    # Return the Environment instance
    environment = graphene.Field(lambda: Environment)

    # The background job key, this may be None
    background_job_key = graphene.Field(graphene.String)

    @staticmethod
    def get_container_status(labbook_name: str, owner: str, username: str) -> bool:
        labbook_key = infer_docker_image_name(labbook_name=labbook_name, owner=owner,
                                              username=username)
        try:
            client = get_docker_client()
            container = client.containers.get(labbook_key)
            if container.status == "running":
                return True
            else:
                return False
        except:
            pass

        return False

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, no_cache=False, client_mutation_id=None):
        username = get_logged_in_username()

        if BuildImage.get_container_status(labbook_name, owner, username):
            raise ValueError(f'Cannot build image for running container {owner}/{labbook_name}')

        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())

        # Generate Dockerfile
        # TODO - Move to build_image ??
        ib = ImageBuilder(lb)
        ib.assemble_dockerfile(write=True)

        # Kick off building in a background thread
        d = Dispatcher()
        build_kwargs = {
            'path': lb.root_dir,
            'username': username,
            'nocache': no_cache
        }

        metadata = {'labbook': lb.key,
                    'method': 'build_image'}

        res = d.dispatch_task(jobs.build_labbook_image, kwargs=build_kwargs, metadata=metadata)

        return BuildImage(environment=Environment(owner=owner, name=labbook_name),
                          background_job_key=res.key_str)


class StartContainer(graphene.relay.ClientIDMutation):
    """Mutator to start a LabBook's Docker Image in a container"""

    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)

    # Return the Environment instance
    environment = graphene.Field(lambda: Environment)

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())

        with lb.lock():
            lb, container_id = ContainerOperations.start_container(
                labbook=lb, username=username)
        logger.info(f'Started new {lb} container ({container_id})')

        return StartContainer(environment=Environment(owner=owner, name=labbook_name))


class StopContainer(graphene.relay.ClientIDMutation):
    """Mutation to stop a Docker container. """

    class Input:
        owner = graphene.String(required=True)
        labbook_name = graphene.String(required=True)

    # Return the Environment instance
    environment = graphene.Field(lambda: Environment)

    @classmethod
    def _stop_container(cls, lb, username):
        lb_ip = ContainerOperations.get_labbook_ip(lb, username)
        stop_labbook_monitor(lb, username)
        lb, stopped = ContainerOperations.stop_container(labbook=lb, username=username)

        # Try to remove route from proxy
        lb_port = 8888
        lb_endpoint = f'http://{lb_ip}:{lb_port}'

        pr = confhttpproxy.ProxyRouter.get_proxy(lb.client_config.config['proxy'])
        routes = pr.routes
        est_target = [k for k in routes.keys()
                      if lb_endpoint in routes[k]['target']
                      and 'jupyter' in k]
        if len(est_target) == 1:
            # TODO: Why only 1? what if there's more?
            pr.remove(est_target[0][1:])

        wf = GitWorkflow(lb)
        wf.garbagecollect()

        # Clean up empty bind mount dirs from datasets if needed
        submodules = lb.git.list_submodules()
        for submodule in submodules:
            namespace, dataset_name = submodule['name'].split("&")
            bind_location = os.path.join(lb.root_dir, 'input', dataset_name)
            if os.path.isdir(bind_location):
                os.rmdir(bind_location)

        if not stopped:
            # TODO: Why would stopped=False? Should this move up??
            raise ValueError(f"Failed to stop labbook {labbook_name}")

    @classmethod
    def mutate_and_get_payload(cls, root, info, owner, labbook_name, client_mutation_id=None):
        username = get_logged_in_username()
        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())

        with lb.lock():
            cls._stop_container(lb, username)

        return StopContainer(environment=Environment(owner=owner, name=labbook_name))
