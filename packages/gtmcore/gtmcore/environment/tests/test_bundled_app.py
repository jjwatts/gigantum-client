import pytest
import os
from collections import OrderedDict

from gtmcore.fixtures import mock_labbook
from gtmcore.environment.bundledapp import BundledAppManager

from gtmcore.environment.tests import ENV_SKIP_MSG, ENV_SKIP_TEST


@pytest.mark.skipif(ENV_SKIP_TEST, reason=ENV_SKIP_MSG)
class TestBundledApps(object):
    def test_invalid_name(self, mock_labbook):
        """Test creating an app with invalid name"""
        bam = BundledAppManager(mock_labbook[2])
        with pytest.raises(ValueError):
            bam.add_bundled_app(1000, '', 'asdf', 'cmd')
        with pytest.raises(ValueError):
            bam.add_bundled_app(1000, 'asdfghjklasdfghjhfdd', 'asdf', 'cmd')
        with pytest.raises(ValueError):
            bam.add_bundled_app(1000, 'jupyter', 'asdf', 'cmd')
        with pytest.raises(ValueError):
            bam.add_bundled_app(1000, 'notebook', 'asdf', 'cmd')
        with pytest.raises(ValueError):
            bam.add_bundled_app(1000, 'jupyterlab', 'asdf', 'cmd')
        with pytest.raises(ValueError):
            bam.add_bundled_app(1000, 'rstudio', 'asdf', 'cmd')

    def test_invalid_port(self, mock_labbook):
        """Test creating an app with invalid name"""
        bam = BundledAppManager(mock_labbook[2])

        assert os.path.exists(bam.bundled_app_file) is False

        with pytest.raises(ValueError):
            bam.add_bundled_app(8888, 'myapp', 'asdf', 'cmd')
        with pytest.raises(ValueError):
            bam.add_bundled_app(8787, 'myapp', 'asdf', 'cmd')
        with pytest.raises(ValueError):
            bam.add_bundled_app(8686, 'myapp', 'asdf', 'cmd')
        with pytest.raises(ValueError):
            bam.add_bundled_app(8585, 'myapp', 'asdf', 'cmd')
        with pytest.raises(ValueError):
            bam.add_bundled_app(8484, 'myapp', 'asdf', 'cmd')
        with pytest.raises(ValueError):
            bam.add_bundled_app(8383, 'myapp', 'asdf', 'cmd')

        assert os.path.exists(bam.bundled_app_file) is False
        bam.add_bundled_app(8050, 'dash 1', 'a demo dash app', 'python app.py')
        assert os.path.exists(bam.bundled_app_file) is True

        with pytest.raises(ValueError):
            bam.add_bundled_app(8050, 'myapp', 'asdf', 'cmd')

    def test_invalid_props(self, mock_labbook):
        """Test creating an app with invalid props"""
        bam = BundledAppManager(mock_labbook[2])
        with pytest.raises(ValueError):
            bam.add_bundled_app(8050, 'dash 1', '12345' * 100, 'python app.py')
        with pytest.raises(ValueError):
            bam.add_bundled_app(8050, 'dash 1', 'a demo dash app', 'python app.py' * 100)

    def test_add_app_get_app(self, mock_labbook):
        """Test adding an app"""
        bam = BundledAppManager(mock_labbook[2])

        assert os.path.exists(bam.bundled_app_file) is False

        result = bam.add_bundled_app(8050, 'dash 1', 'a demo dash app', 'python app.py')

        assert os.path.exists(bam.bundled_app_file) is True
        assert 'dash 1' in result
        assert result['dash 1']['port'] == 8050
        assert result['dash 1']['description'] == 'a demo dash app'
        assert result['dash 1']['command'] == 'python app.py'

        loaded_apps = bam.get_bundled_apps()

        assert result == loaded_apps

    def test_add_app_exists(self, mock_labbook):
        """Test adding an app that already exists (update it)"""
        bam = BundledAppManager(mock_labbook[2])

        assert os.path.exists(bam.bundled_app_file) is False

        result = bam.add_bundled_app(8050, 'dash 1', 'a demo dash app', 'python app.py')

        assert os.path.exists(bam.bundled_app_file) is True
        assert 'dash 1' in result
        assert result['dash 1']['port'] == 8050
        assert result['dash 1']['description'] == 'a demo dash app'
        assert result['dash 1']['command'] == 'python app.py'

        result2 = bam.add_bundled_app(9000, 'dash 1', 'updated demo dash app', 'python app.py')
        assert 'dash 1' in result
        assert result2['dash 1']['port'] == 9000
        assert result2['dash 1']['description'] == 'updated demo dash app'
        assert result2['dash 1']['command'] == 'python app.py'

        loaded_apps = bam.get_bundled_apps()

        assert result2 != result
        assert result2 == loaded_apps

    def test_remove_app_errors(self, mock_labbook):
        """Test errors when removing"""
        bam = BundledAppManager(mock_labbook[2])

        with pytest.raises(ValueError):
            bam.remove_bundled_app("fake")

    def test_remove_app(self, mock_labbook):
        """Test removing a bundled app"""
        bam = BundledAppManager(mock_labbook[2])

        assert os.path.exists(bam.bundled_app_file) is False

        bam.add_bundled_app(8050, 'dash 1', 'a demo dash app 1', 'python app1.py')
        bam.add_bundled_app(9000, 'dash 2', 'a demo dash app 2', 'python app2.py')
        bam.add_bundled_app(9001, 'dash 3', 'a demo dash app 3', 'python app3.py')

        apps = bam.get_bundled_apps()

        assert os.path.exists(bam.bundled_app_file) is True
        assert 'dash 1' in apps
        assert apps['dash 1']['port'] == 8050
        assert apps['dash 1']['description'] == 'a demo dash app 1'
        assert apps['dash 1']['command'] == 'python app1.py'

        assert 'dash 2' in apps
        assert apps['dash 2']['port'] == 9000
        assert apps['dash 2']['description'] == 'a demo dash app 2'
        assert apps['dash 2']['command'] == 'python app2.py'

        assert 'dash 3' in apps
        assert apps['dash 3']['port'] == 9001
        assert apps['dash 3']['description'] == 'a demo dash app 3'
        assert apps['dash 3']['command'] == 'python app3.py'

        bam.remove_bundled_app('dash 2')
        apps = bam.get_bundled_apps()
        assert 'dash 1' in apps
        assert 'dash 2' not in apps
        assert 'dash 3' in apps

        bam.remove_bundled_app('dash 3')
        apps = bam.get_bundled_apps()
        assert 'dash 1' in apps
        assert 'dash 2' not in apps
        assert 'dash 3' not in apps

        bam.remove_bundled_app('dash 1')
        apps = bam.get_bundled_apps()
        assert len(apps.keys()) == 0
        assert isinstance(apps, OrderedDict)

    def test_get_docker_lines(self, mock_labbook):
        """Test getting docker lines"""
        bam = BundledAppManager(mock_labbook[2])

        assert os.path.exists(bam.bundled_app_file) is False

        bam.add_bundled_app(8050, 'dash 1', 'a demo dash app 1', 'python app1.py')
        bam.add_bundled_app(9000, 'dash 2', 'a demo dash app 2', 'python app2.py')
        bam.add_bundled_app(9001, 'dash 3', 'a demo dash app 3', 'python app3.py')

        docker_lines = bam.get_docker_lines()
        assert docker_lines[0] == "EXPOSE 8050"
        assert docker_lines[1] == "EXPOSE 9000"
        assert docker_lines[2] == "EXPOSE 9001"
