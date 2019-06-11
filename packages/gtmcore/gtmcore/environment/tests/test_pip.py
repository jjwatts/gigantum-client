import pytest

from gtmcore.environment.pip import PipPackageManager
from gtmcore.fixtures.container import mock_config_with_repo, build_lb_image_for_env

from gtmcore.environment.tests import ENV_SKIP_MSG, ENV_SKIP_TEST


@pytest.mark.skipif(ENV_SKIP_TEST, reason=ENV_SKIP_MSG)
class TestPipPackageManager(object):
    def test_search(self, mock_config_with_repo, build_lb_image_for_env):
        """Test search command"""
        mrg = PipPackageManager()
        lb = build_lb_image_for_env[0]
        username = build_lb_image_for_env[1]
        result = mrg.search("peppercorn", lb, username)
        assert len(result) == 2

        result = mrg.search("gigantum", lb, username)
        assert len(result) == 4
        assert result[0] == "gigantum"
        assert result[3] == "gtmunit3"

    def test_list_versions(self, build_lb_image_for_env):
        """Test list_versions command"""
        mrg = PipPackageManager()
        lb = build_lb_image_for_env[0]
        username = build_lb_image_for_env[1]
        result = mrg.list_versions("gtmunit1", lb, username)

        assert len(result) == 5
        assert result[0] == '0.12.4'
        assert result[1] == '0.2.4'
        assert result[2] == '0.2.1'
        assert result[3] == '0.2.0'
        assert result[4] == '0.1.0'

    def test_list_installed_packages(self, build_lb_image_for_env):
        """Test list_installed_packages command

        Note, if the contents of the container change, this test will break and need to be updated. Because of this,
        only limited asserts are made to make sure things are coming back in a reasonable format
        """
        mrg = PipPackageManager()
        lb = build_lb_image_for_env[0]
        username = build_lb_image_for_env[1]
        result = mrg.list_installed_packages(lb, username)

        assert type(result) == list
        assert len(result) > 50
        assert type(result[0]) == dict
        assert type(result[0]['name']) == str
        assert type(result[0]['version']) == str

    def test_generate_docker_install_snippet_single(self):
        """Test generate_docker_install_snippet command
        """
        mrg = PipPackageManager()

        packages = [{'name': 'mypackage', 'version': '3.1.4'}]

        result = mrg.generate_docker_install_snippet(packages)
        assert result == ['RUN pip install mypackage==3.1.4']

        result = mrg.generate_docker_install_snippet(packages, single_line=True)
        assert result == ['RUN pip install mypackage==3.1.4']

    def test_generate_docker_install_snippet_multiple(self):
        """Test generate_docker_install_snippet command
        """
        mrg = PipPackageManager()

        packages = [{'name': 'mypackage', 'version': '3.1.4'},
                    {'name': 'yourpackage', 'version': '2017-54.0'}]

        result = mrg.generate_docker_install_snippet(packages)
        assert result == ['RUN pip install mypackage==3.1.4', 'RUN pip install yourpackage==2017-54.0']

        result = mrg.generate_docker_install_snippet(packages, single_line=True)
        assert result == ['RUN pip install mypackage==3.1.4 yourpackage==2017-54.0']

    def test_list_versions_badpackage(self, build_lb_image_for_env):
        """Test list_versions command"""
        mrg = PipPackageManager()
        lb = build_lb_image_for_env[0]
        username = build_lb_image_for_env[1]
        with pytest.raises(ValueError):
            mrg.list_versions("gigantumasdfasdfasdf", lb, username)

    def test_is_valid_errors(self, build_lb_image_for_env):
        """Test list_versions command"""
        pkgs = [{"manager": "pip", "package": "gtmunit1", "version": '0.2.4'},
                {"manager": "pip", "package": "gtmunit2", "version": "100.00"},
                {"manager": "pip", "package": "gtmunit3"},
                {"manager": "pip", "package": "asdfasdfasdf", "version": ""},
                {"manager": "pip", "package": "notarealpackage"}]

        mrg = PipPackageManager()
        lb = build_lb_image_for_env[0]
        username = build_lb_image_for_env[1]
        result = mrg.validate_packages(pkgs, lb, username)

        assert result[0].package == "gtmunit1"
        assert result[0].version == "0.2.4"
        assert result[0].error is False

        assert result[1].package == "gtmunit2"
        assert result[1].version == "100.00"
        assert result[1].error is True

        assert result[2].package == "gtmunit3"
        assert result[2].version == "5.0"
        assert result[2].error is False

        assert result[3].package == "asdfasdfasdf"
        assert result[3].version == ""
        assert result[3].error is True

        assert result[4].package == "notarealpackage"
        assert result[4].version is None
        assert result[4].error is True

    def test_is_valid_good(self, build_lb_image_for_env):
        """Test valid packages command"""
        pkgs = [{"manager": "pip", "package": "gtmunit3", "version": "4.15"},
                {"manager": "pip", "package": "gtmunit2", "version": ""}]

        mrg = PipPackageManager()
        lb = build_lb_image_for_env[0]
        username = build_lb_image_for_env[1]
        result = mrg.validate_packages(pkgs, lb, username)

        assert result[0].package == "gtmunit3"
        assert result[0].version == "4.15"
        assert result[0].error is False

        assert result[1].package == "gtmunit2"
        assert result[1].version == "12.2"
        assert result[1].error is False

    def test_get_metadata(self, build_lb_image_for_env):
        """Test get_packages_metadata method"""
        mrg = PipPackageManager()
        lb = build_lb_image_for_env[0]
        username = build_lb_image_for_env[1]
        result = mrg.get_packages_metadata(['gtmunit1', 'gtmunit2', 'gtmunit3',
                                            'gigantum', 'asdfsdfgsfdgdsfgsfdg'], lb, username)

        assert len(result) == 5
        assert result[0].description == 'Package 1 for Gigantum Client unit testing.'
        assert result[0].docs_url == 'https://github.com/gigantum/gigantum-client'
        assert result[0].latest_version == "0.12.4"

        assert result[1].description == 'Package 1 for Gigantum Client unit testing.'
        assert result[1].docs_url == 'https://github.com/gigantum/gigantum-client'
        assert result[1].latest_version == "12.2"

        assert result[2].description == 'Package 1 for Gigantum Client unit testing.'
        assert result[2].docs_url == 'https://github.com/gigantum/gigantum-client'
        assert result[2].latest_version == "5.0"

        assert result[3].description == 'CLI for the Gigantum Platform'
        assert result[3].docs_url == 'https://github.com/gigantum/gigantum-cli'
        assert isinstance(result[3].latest_version, str)

        assert result[4].description is None
        assert result[4].docs_url is None
        assert result[4].latest_version is None
