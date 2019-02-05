import pytest
import platform

from dataclasses import dataclass


class TestPythonVersion(object):
    def test_python_version(self):
        @dataclass
        class TestDataClass(object):
            x: int = 2

        python_version = platform.python_version()
        assert python_version.startswith('3.7')
