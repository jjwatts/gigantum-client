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
import os
import tempfile
from unittest.mock import PropertyMock, patch

import yaml

from gtmcore.configuration import (Configuration, _get_docker_server_api_version, get_docker_client)
from gtmcore.fixtures import mock_config_file, mock_config_file_team


@pytest.fixture(scope="module")
def mock_config_file_no_delete():
    with tempfile.NamedTemporaryFile(mode="wt", delete=False) as fp:
        # Write a temporary config file
        fp.write("""core:
  team_mode: true 
git:
  working_directory: '~/gigantum'""")
        fp.close()

        yield fp.name  # provide the fixture value

    del fp.name


@pytest.fixture(scope="module")
def mock_config_file_inherit():
    with tempfile.NamedTemporaryFile(mode="wt", delete=False) as parent_fp:
        # Write a temporary config file
        parent_fp.write("""test: 'new field'
core:
  team_mode: false""")
        parent_fp.close()

    with tempfile.NamedTemporaryFile(mode="wt", delete=False) as fp:
        # Write a temporary config file
        fp.write("""from: {}
core:
  team_mode: true 
git:
  working_directory: '~/gigantum'""".format(parent_fp.name))
        fp.close()

        yield fp.name  # provide the fixture value

    del fp.name


class TestConfiguration(object):
    def test_init(self, mock_config_file_team):
        """Test loading a config file explicitly"""
        configuration = Configuration(mock_config_file_team[0])

        assert 'core' in configuration.config
        assert 'team_mode' in configuration.config["core"]
        assert configuration.config["core"]["team_mode"] is True
        assert 'git' in configuration.config

    def test_init_inherit(self, mock_config_file_inherit):
        """Test loading a config file explicitly from a file that inherits properties"""
        configuration = Configuration(mock_config_file_inherit)

        assert 'core' in configuration.config
        assert 'team_mode' in configuration.config["core"]
        assert configuration.config["core"]["team_mode"] is False
        assert 'git' in configuration.config
        assert 'test' in configuration.config
        assert 'from' in configuration.config
        assert configuration.config["test"] == 'new field'

    def test_init_load_from_package(self):
        """Test loading the default file from the package"""
        configuration = Configuration()

        assert 'core' in configuration.config
        assert 'git' in configuration.config

    def test_init_load_from_install(self, mock_config_file):
        """Test loading the default file from the installed location"""
        with patch('gtmcore.configuration.Configuration.INSTALLED_LOCATION', new_callable=PropertyMock,
                   return_value=mock_config_file[0]):
            configuration = Configuration()

            assert 'core' in configuration.config
            assert 'git' in configuration.config

    def test_save(self, mock_config_file_no_delete):
        """Test writing changes to a config file"""
        configuration = Configuration(mock_config_file_no_delete)

        assert 'core' in configuration.config
        assert 'team_mode' in configuration.config["core"]
        assert configuration.config["core"]["team_mode"] is True
        assert 'git' in configuration.config

        configuration.config["core"]["team_mode"] = False
        configuration.config["git"]["working_directory"] = "/some/dir/now/"
        configuration.save()

        del configuration

        configuration = Configuration(mock_config_file_no_delete)

        assert 'core' in configuration.config
        assert 'team_mode' in configuration.config["core"]
        assert configuration.config["core"]["team_mode"] is False
        assert 'git' in configuration.config
        assert configuration.config["git"]["working_directory"] == "/some/dir/now/"

    def test_get_docker_version_str(self):
        """Docker API version strings are in the format of X.XX. """
        try:
            f_val = float(_get_docker_server_api_version())
            assert f_val > 1.0 and f_val < 2.0
        except ValueError:
            pass

    def test_get_docker_client(self):
        """Test no exceptions when getting docker client both for max-compatible versions and default versions. """
        docker_client = get_docker_client(check_server_version=True)
        docker_client_2 = get_docker_client(check_server_version=False)

    def test_load_user_config(self, mock_config_file):
        """ Test loading configuration override items from a user's custom config """
        with tempfile.TemporaryDirectory() as tempdir:
            override_config_path = os.path.join(tempdir, 'user-config.yaml')
            with open(override_config_path, 'w') as yf:
                override_dict = {'container': {'memory': 99}}
                yf.write(yaml.safe_dump(override_dict, default_flow_style=False))

            with patch('gtmcore.configuration.Configuration.USER_LOCATION', new_callable=PropertyMock,
                       return_value=yf.name):
                conf = Configuration()
                assert conf.USER_LOCATION == yf.name
                assert conf.user_config['container']['memory'] == 99
                assert conf.config['container']['memory'] == 99

                # If we give an explicit config file, then we IGNORE any user overrides
                conf2 = Configuration(mock_config_file[0])
                assert conf2.config['container']['memory'] is None
                assert len(conf2.user_config.keys()) == 0

    def test_get_remote_configuration(self):
        """Test get_remote_configuration"""
        configuration = Configuration()
        remote = configuration.get_remote_configuration()
        assert remote['git_remote'] == 'repo.gigantum.io'
        assert remote['remote_type'] == 'gitlab'
        assert remote['admin_service'] == 'usersrv.gigantum.io'
        assert remote['index_service'] == 'api.gigantum.com/read'
        assert remote['object_service'] == 'api.gigantum.com/object-v1'

        remote = configuration.get_remote_configuration("repo.gigantum.io")
        assert remote['git_remote'] == 'repo.gigantum.io'
        assert remote['remote_type'] == 'gitlab'
        assert remote['admin_service'] == 'usersrv.gigantum.io'
        assert remote['index_service'] == 'api.gigantum.com/read'
        assert remote['object_service'] == 'api.gigantum.com/object-v1'

    def test_get_remote_configuration_not_found(self):
        """Test get_remote_configuration"""
        configuration = Configuration()
        with pytest.raises(ValueError):
            configuration.get_remote_configuration("asdfasdf.asdfasdf.com")

    def test_get_upload_directory(self):
        """Test get upload directory"""
        configuration = Configuration()
        assert configuration.upload_dir == os.path.join(configuration.app_workdir, '.labmanager', 'upload')

    def test_download_cpu_limit(self):
        configuration = Configuration()
        assert configuration.download_cpu_limit > 0

    def test_upload_cpu_limit(self):
        configuration = Configuration()
        assert configuration.upload_cpu_limit > 0
