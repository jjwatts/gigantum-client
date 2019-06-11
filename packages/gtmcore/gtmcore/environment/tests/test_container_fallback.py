import pytest
import shutil

from gtmcore.environment.pip import PipPackageManager
from gtmcore.fixtures import mock_config_with_repo, ENV_UNIT_TEST_REPO, ENV_UNIT_TEST_BASE, ENV_UNIT_TEST_REV
from gtmcore.configuration import get_docker_client

from gtmcore.environment import ComponentManager
from gtmcore.inventory.inventory  import InventoryManager
from gtmcore.imagebuilder import ImageBuilder
from gtmcore.container.container import ContainerOperations

from gtmcore.environment.tests import ENV_SKIP_MSG, ENV_SKIP_TEST


@pytest.mark.skipif(ENV_SKIP_TEST, reason=ENV_SKIP_MSG)
class TestContainerFallback(object):
    def test_list_versions_from_fallback(self, mock_config_with_repo):
        """Test list_versions command"""
        username = "unittest"
        im = InventoryManager(mock_config_with_repo[0])
        lb = im.create_labbook('unittest', 'unittest', 'labbook-unittest-01',
                               description="From mock_config_from_repo fixture")

        # Create Component Manager
        cm = ComponentManager(lb)
        # Add a component
        cm.add_base(ENV_UNIT_TEST_REPO, ENV_UNIT_TEST_BASE, ENV_UNIT_TEST_REV)

        ib = ImageBuilder(lb)
        ib.assemble_dockerfile(write=True)
        client = get_docker_client()

        try:
            lb, docker_image_id = ContainerOperations.build_image(labbook=lb, username=username)

            # Test lookup
            mrg = PipPackageManager()
            result = mrg.search("peppercorn", lb, username)
            assert len(result) == 2

            result = mrg.search("gigantum", lb, username)
            assert len(result) == 4
            assert result[0] == "gigantum"

            # Delete image
            client.images.remove(docker_image_id, force=True, noprune=False)

            # Test lookup still works
            mrg = PipPackageManager()
            result = mrg.search("peppercorn", lb, username)
            assert len(result) == 2

            result = mrg.search("gigantum", lb, username)
            assert len(result) == 4
            assert result[0] == "gigantum"

        finally:
            shutil.rmtree(lb.root_dir)

            # Remove image if it's still there
            try:
                client.images.remove(docker_image_id, force=True, noprune=False)
            except:
                pass




