import os
import shutil
import docker.errors
import pytest
import pprint

from mock import patch

from gtmcore.configuration import get_docker_client, Configuration
from gtmcore.container.container import ContainerOperations
from gtmcore.environment import ComponentManager
from gtmcore.inventory.inventory  import InventoryManager
from gtmcore.imagebuilder import ImageBuilder
from gtmcore.fixtures.fixtures import mock_config_with_repo, ENV_UNIT_TEST_REPO, ENV_UNIT_TEST_BASE, ENV_UNIT_TEST_REV


@pytest.fixture(scope='function')
def build_lb_image_for_jupyterlab(mock_config_with_repo):
    with patch.object(Configuration, 'find_default_config', lambda self: mock_config_with_repo[0]):
        im = InventoryManager(mock_config_with_repo[0])
        lb = im.create_labbook('unittester', 'unittester', "containerunittestbook")

        # Create Component Manager
        cm = ComponentManager(lb)
        # Add a component
        cm.add_base(ENV_UNIT_TEST_REPO, ENV_UNIT_TEST_BASE, ENV_UNIT_TEST_REV)
        cm.add_packages("pip", [{"manager": "pip", "package": "requests", "version": "2.18.4"}])

        ib = ImageBuilder(lb)
        docker_lines = ib.assemble_dockerfile(write=True)
        assert 'RUN pip install requests==2.18.4' in docker_lines
        assert all(['==None' not in l for l in docker_lines.split()])
        assert all(['=None' not in l for l in docker_lines.split()])
        client = get_docker_client()
        client.containers.prune()

        assert os.path.exists(os.path.join(lb.root_dir, '.gigantum', 'env', 'entrypoint.sh'))

        try:
            lb, docker_image_id = ContainerOperations.build_image(labbook=lb, username="unittester")
            lb, container_id = ContainerOperations.start_container(lb, username="unittester")

            assert isinstance(container_id, str)
            yield lb, ib, client, docker_image_id, container_id, None, 'unittester'

            try:
                _, s = ContainerOperations.stop_container(labbook=lb, username="unittester")
            except docker.errors.APIError:
                client.containers.get(container_id=container_id).stop(timeout=2)
                s = False
        finally:
            shutil.rmtree(lb.root_dir)
            # Stop and remove container if it's still there
            try:
                client.containers.get(container_id=container_id).stop(timeout=2)
                client.containers.get(container_id=container_id).remove()
            except:
                pass

            # Remove image if it's still there
            try:
                ContainerOperations.delete_image(labbook=lb, username='unittester')
                client.images.remove(docker_image_id, force=True, noprune=False)
            except:
                pass

            try:
                client.images.remove(docker_image_id, force=True, noprune=False)
            except:
                pass


@pytest.fixture(scope='class')
def build_lb_image_for_env(mock_config_with_repo):
    # Create a labook
    im = InventoryManager(mock_config_with_repo[0])
    lb = im.create_labbook('unittester', 'unittester', "containerunittestbookenv",
                           description="Testing environment functions.")

    # Create Component Manager
    cm = ComponentManager(lb)
    # Add a component
    cm.add_base(ENV_UNIT_TEST_REPO, ENV_UNIT_TEST_BASE, ENV_UNIT_TEST_REV)

    ib = ImageBuilder(lb)
    ib.assemble_dockerfile(write=True)
    client = get_docker_client()
    client.containers.prune()

    try:
        lb, docker_image_id = ContainerOperations.build_image(labbook=lb, username="unittester")

        yield lb, 'unittester'

    finally:
        shutil.rmtree(lb.root_dir)

        # Remove image if it's still there
        try:
            client.images.remove(docker_image_id, force=True, noprune=False)
        except:
            pass


@pytest.fixture(scope='class')
def build_lb_image_for_env_conda(mock_config_with_repo):
    """A fixture that installs an old version of matplotlib and latest version of requests to increase code coverage"""
    im = InventoryManager(mock_config_with_repo[0])
    lb = im.create_labbook('unittester', 'unittester', "containerunittestbookenvconda",
                           description="Testing environment functions.")
    cm = ComponentManager(lb)
    cm.add_base(ENV_UNIT_TEST_REPO, ENV_UNIT_TEST_BASE, ENV_UNIT_TEST_REV)
    cm.add_packages('conda3', [{'package': 'python-coveralls', 'version': '2.7.0'}])

    ib = ImageBuilder(lb)
    ib.assemble_dockerfile(write=True)
    client = get_docker_client()
    client.containers.prune()

    try:
        lb, docker_image_id = ContainerOperations.build_image(labbook=lb, username="unittester")

        yield lb, 'unittester'

    finally:
        shutil.rmtree(lb.root_dir)
        try:
            client.images.remove(docker_image_id, force=True, noprune=False)
        except:
            pass
