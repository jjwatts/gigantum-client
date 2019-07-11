import pytest
import re
import os

from gtmcore.environment.apt import AptPackageManager
from gtmcore.fixtures.container import build_lb_image_for_env, mock_config_with_repo
from gtmcore.environment.tests import ENV_SKIP_MSG, ENV_SKIP_TEST


@pytest.mark.skipif(ENV_SKIP_TEST, reason=ENV_SKIP_MSG)
class TestAptPackageManager(object):
    def test_search(self, build_lb_image_for_env):
        """Test search command"""
        lb = build_lb_image_for_env[0]
        username = build_lb_image_for_env[1]
        mrg = AptPackageManager()
        result = mrg.search("libtiff", lb, username)
        assert len(result) == 7
        assert 'libtiff5' in result

    def test_list_versions(self, build_lb_image_for_env):
        """Test list_versions command"""
        mrg = AptPackageManager()
        lb = build_lb_image_for_env[0]
        username = build_lb_image_for_env[1]
        result = mrg.list_versions("libtiff5", lb, username)

        assert len(result) == 1

        # assert result == "4.0.9-5"
        assert re.match('\d.\d.\d-\d', result[0])

    def test_list_installed_packages(self, build_lb_image_for_env):
        """Test list_installed_packages command

        Note, if the contents of the container change, this test will break and need to be updated. Because of this,
        only limited asserts are made to make sure things are coming back in a reasonable format
        """
        mrg = AptPackageManager()
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
        mrg = AptPackageManager()
        packages = [{'name': 'mypackage', 'version': '3.1.4'}]

        result = mrg.generate_docker_install_snippet(packages)
        assert result == ['RUN apt-get -y --no-install-recommends install mypackage']

        result = mrg.generate_docker_install_snippet(packages, single_line=True)
        assert result == ['RUN apt-get -y --no-install-recommends install mypackage']

    def test_generate_docker_install_snippet_multiple(self):
        """Test generate_docker_install_snippet command
        """
        mrg = AptPackageManager()

        packages = [{'name': 'mypackage', 'version': '3.1.4'},
                    {'name': 'yourpackage', 'version': '2017-54.0'}]

        result = mrg.generate_docker_install_snippet(packages)
        assert result == ['RUN apt-get -y --no-install-recommends install mypackage',
                          'RUN apt-get -y --no-install-recommends install yourpackage']

        result = mrg.generate_docker_install_snippet(packages, single_line=True)
        assert result == ['RUN apt-get -y --no-install-recommends install mypackage yourpackage']

    def test_list_versions_badpackage(self, build_lb_image_for_env):
        """Test list_versions command"""
        mrg = AptPackageManager()
        lb = build_lb_image_for_env[0]
        username = build_lb_image_for_env[1]

        with pytest.raises(ValueError):
            mrg.list_versions("asdfasdfasd", lb, username)

    def test_is_valid(self, build_lb_image_for_env):
        """Test list_versions command"""
        pkgs = [{"manager": "pip", "package": "libjpeg-dev", "version": ""},
                {"manager": "pip", "package": "afdgfdgshfdg", "version": ""}]

        mrg = AptPackageManager()
        lb = build_lb_image_for_env[0]
        username = build_lb_image_for_env[1]
        result = mrg.validate_packages(pkgs, lb, username)

        assert result[0].package == "libjpeg-dev"
        assert result[0].version != ""
        assert result[0].error is False

        assert result[1].package == "afdgfdgshfdg"
        assert result[1].version == ""
        assert result[1].error is True

    def test_extract_metadata(self, build_lb_image_for_env):
        """Test list_versions command"""
        mrg = AptPackageManager()
        lb = build_lb_image_for_env[0]
        username = build_lb_image_for_env[1]
        result = mrg.get_packages_metadata(['libtiff5', 'gzip', 'curl', 'gfkljhgdfskjhfdghkjfgds'], lb, username)

        assert len(result) == 4
        assert result[0].description == 'Tag Image File Format (TIFF) library'
        assert result[0].docs_url is None
        assert isinstance(result[0].latest_version, str) is True
        assert result[1].description == 'GNU compression utilities'
        assert result[1].docs_url is None
        assert isinstance(result[1].latest_version, str) is True
        assert result[2].description == 'command line tool for transferring data with URL syntax'
        assert result[2].docs_url is None
        assert isinstance(result[2].latest_version, str) is True
        assert result[3].description is None
        assert result[3].docs_url is None
        assert result[3].latest_version is None

