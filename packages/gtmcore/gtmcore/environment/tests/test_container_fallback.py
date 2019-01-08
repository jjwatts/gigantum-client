# Copyright (c) 2017 FlashX, LLC
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
import pytest
import shutil

from gtmcore.environment.pip import PipPackageManager
from gtmcore.fixtures import mock_config_with_repo, ENV_UNIT_TEST_REPO, ENV_UNIT_TEST_BASE, ENV_UNIT_TEST_REV
from gtmcore.configuration import get_docker_client

from gtmcore.environment import ComponentManager
from gtmcore.inventory.inventory  import InventoryManager
from gtmcore.imagebuilder import ImageBuilder
from gtmcore.container.container import ContainerOperations


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




