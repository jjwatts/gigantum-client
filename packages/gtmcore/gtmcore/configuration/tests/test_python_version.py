import pytest
import platform


class TestPythonVersion(object):
    def test_python_version(self):
        python_version = platform.python_version()
        assert python_version.startswith('3.7')
