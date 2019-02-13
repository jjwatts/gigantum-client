import pytest
import os
import glob
import yaml

from gtmcore.fixtures.fixtures import mock_config_with_repo, ENV_UNIT_TEST_REPO, ENV_UNIT_TEST_BASE, ENV_UNIT_TEST_REV
from gtmcore.environment import ComponentManager
from gtmcore.inventory.inventory import InventoryManager

from gtmcore.container.cuda import should_launch_with_cuda_support


@pytest.fixture()
def driver_version_fixture():
    old_driver_version = os.environ.get('NVIDIA_DRIVER_VERSION')
    yield

    if old_driver_version:
        os.environ['NVIDIA_DRIVER_VERSION'] = old_driver_version
    else:
        del os.environ['NVIDIA_DRIVER_VERSION']


class TestCUDAVersion(object):
    def test_should_launch_with_cuda_support(self, driver_version_fixture):
        """ Check that all version checking logic works """

        """10: {0: (410, 58)},
            9: {0: (384, 81),
                1: (387, 26),
                2: (396, 26)},
            8: {0: (375, 51)}}"""   

        # For CUDA 8
        os.environ['NVIDIA_DRIVER_VERSION'] = '375.51'
        assert(should_launch_with_cuda_support('8.0')[0]) is True
        os.environ['NVIDIA_DRIVER_VERSION'] = '374.51'
        assert(should_launch_with_cuda_support('8.0')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '375.50'
        assert(should_launch_with_cuda_support('8.0')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '374.52'
        assert(should_launch_with_cuda_support('8.0')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '376.8'
        assert(should_launch_with_cuda_support('8.0')[0]) is True

        # For CUDA 9.0
        os.environ['NVIDIA_DRIVER_VERSION'] = '384.81'
        assert(should_launch_with_cuda_support('9.0')[0]) is True
        os.environ['NVIDIA_DRIVER_VERSION'] = '383.81'
        assert(should_launch_with_cuda_support('9.0')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '384.80'
        assert(should_launch_with_cuda_support('9.0')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '383.82'
        assert(should_launch_with_cuda_support('9.0')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '385.8'
        assert(should_launch_with_cuda_support('9.0')[0]) is True

        # For CUDA 9.1
        os.environ['NVIDIA_DRIVER_VERSION'] = '387.26'
        assert(should_launch_with_cuda_support('9.1')[0]) is True
        os.environ['NVIDIA_DRIVER_VERSION'] = '386.26'
        assert(should_launch_with_cuda_support('9.1')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '387.25'
        assert(should_launch_with_cuda_support('9.1')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '386.27'
        assert(should_launch_with_cuda_support('9.1')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '388.8'
        assert(should_launch_with_cuda_support('9.1')[0]) is True

        # For CUDA 9.2
        os.environ['NVIDIA_DRIVER_VERSION'] = '396.26'
        assert(should_launch_with_cuda_support('9.2')[0]) is True
        os.environ['NVIDIA_DRIVER_VERSION'] = '395.26'
        assert(should_launch_with_cuda_support('9.2')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '396.25'
        assert(should_launch_with_cuda_support('9.2')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '395.27'
        assert(should_launch_with_cuda_support('9.2')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '397.8'
        assert(should_launch_with_cuda_support('9.2')[0]) is True

        # For CUDA 10
        os.environ['NVIDIA_DRIVER_VERSION'] = '410.58'
        assert(should_launch_with_cuda_support('10.0')[0]) is True
        os.environ['NVIDIA_DRIVER_VERSION'] = '409.58'
        assert(should_launch_with_cuda_support('11.0')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '410.57'
        assert(should_launch_with_cuda_support('10.0')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '409.59'
        assert(should_launch_with_cuda_support('10.0')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '411.8'
        assert(should_launch_with_cuda_support('10.0')[0]) is True

    def test_should_launch_with_cuda_support_bad_input(self):
        """ Check that all version checking logic works """

        """10: {0: (410, 58)},
            9: {0: (384, 81),
                1: (387, 26),
                2: (396, 26)},
            8: {0: (375, 51)}}"""
        # no host support
        assert (should_launch_with_cuda_support('10.0')[0]) is False

        os.environ['NVIDIA_DRIVER_VERSION'] = '410.58'
        assert(should_launch_with_cuda_support('2.17')[0]) is False
        assert(should_launch_with_cuda_support('10.0.1')[0]) is False
        assert(should_launch_with_cuda_support('asdf')[0]) is False
        assert(should_launch_with_cuda_support('ab.cd')[0]) is False

        os.environ['NVIDIA_DRIVER_VERSION'] = 'foo.bar'
        assert(should_launch_with_cuda_support('10.0')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = 'fooasdf'
        assert(should_launch_with_cuda_support('10.0')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '100'
        assert(should_launch_with_cuda_support('10.0')[0]) is False
        os.environ['NVIDIA_DRIVER_VERSION'] = '410.58.8'
        assert(should_launch_with_cuda_support('10.0')[0]) is False

    def test_should_launch_with_cuda_support_reason(self):
        launch, reason = should_launch_with_cuda_support('10.0')
        assert launch is False
        assert reason == "Host does not have NVIDIA drivers configured"

        os.environ['NVIDIA_DRIVER_VERSION'] = '410.58.1'
        launch, reason = should_launch_with_cuda_support('10.0')
        assert launch is False
        assert reason == "Host does not have NVIDIA drivers configured"

        os.environ['NVIDIA_DRIVER_VERSION'] = '410.58'
        launch, reason = should_launch_with_cuda_support(None)
        assert launch is False
        assert reason == "Project is not GPU enabled"

        os.environ['NVIDIA_DRIVER_VERSION'] = '410.58'
        launch, reason = should_launch_with_cuda_support('10.0.1')
        assert launch is False
        assert reason == "Failed to parse required CUDA version from Project configuration"

        os.environ['NVIDIA_DRIVER_VERSION'] = '410.58'
        launch, reason = should_launch_with_cuda_support('4.0')
        assert launch is False
        assert reason == "Project CUDA version (4.0) not supported"

        os.environ['NVIDIA_DRIVER_VERSION'] = '410.58'
        launch, reason = should_launch_with_cuda_support('10.6')
        assert launch is False
        assert reason == "Project CUDA version (10.6) not supported"

        os.environ['NVIDIA_DRIVER_VERSION'] = '396.26'
        launch, reason = should_launch_with_cuda_support('10.0')
        assert launch is False
        assert reason == f"Project CUDA version (10.0) is not compatible with host" \
            f" driver version (396.26)"

        os.environ['NVIDIA_DRIVER_VERSION'] = '410.58'
        launch, reason = should_launch_with_cuda_support('10.0')
        assert launch is True
        assert reason == f"Project CUDA version (10.0) is compatible with host" \
            f" driver version (410.58)"

    def test_cuda_version_property(self, mock_config_with_repo):
        """Test getting the cuda version"""
        im = InventoryManager(mock_config_with_repo[0])
        lb = im.create_labbook('test', 'test', 'labbook1', description="my first labbook")

        assert lb.cuda_version is None

        # Add base without GPU support
        cm = ComponentManager(lb)
        cm.add_base(ENV_UNIT_TEST_REPO, ENV_UNIT_TEST_BASE, ENV_UNIT_TEST_REV)
        base_yaml_file = glob.glob(os.path.join(lb.root_dir, '.gigantum', 'env', 'base', '*.yaml'))[0]

        assert lb.cuda_version is None

        # Fake a version
        with open(base_yaml_file, 'rt') as bf:
            base_data = yaml.safe_load(bf)

        base_data['cuda_version'] = '10.0'

        with open(base_yaml_file, 'wt') as bf:
            yaml.safe_dump(base_data, bf)

        assert lb.cuda_version == '10.0'
