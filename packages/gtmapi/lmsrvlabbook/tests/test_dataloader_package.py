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

from lmsrvlabbook.tests.fixtures import fixture_working_dir, build_image_for_jupyterlab
from promise import Promise

from lmsrvlabbook.dataloader.package import PackageLatestVersionLoader


class TestDataloaderPackage(object):
    def test_load_one_pip(self, build_image_for_jupyterlab):
        """Test loading 1 package"""

        key = "pip&gtmunit1"
        lb, username = build_image_for_jupyterlab[0], build_image_for_jupyterlab[5]

        loader = PackageLatestVersionLoader([key], lb, username)
        promise1 = loader.load(key)
        assert isinstance(promise1, Promise)

        pkg = promise1.get()
        assert pkg == '0.12.4'

    def test_load_many_pip(self, build_image_for_jupyterlab):
        """Test loading many labbooks"""
        lb, username = build_image_for_jupyterlab[0], build_image_for_jupyterlab[5]
        keys = ["pip&gtmunit1", "pip&gtmunit2", "pip&gtmunit3"]
        loader = PackageLatestVersionLoader(keys, lb, username)
        promise1 = loader.load_many(keys)
        assert isinstance(promise1, Promise)

        version_list = promise1.get()
        assert len(version_list) == 3
        assert version_list[0] == "0.12.4"
        assert version_list[1] == "12.2"
        assert version_list[2] == "5.0"

    def test_load_many_conda(self, build_image_for_jupyterlab):
        """Test loading many labbooks"""
        lb, username = build_image_for_jupyterlab[0], build_image_for_jupyterlab[5]
        keys = ["conda3&cdutil", "conda3&python-coveralls", "conda3&nltk"]
        loader = PackageLatestVersionLoader(keys, lb, username)
        promise1 = loader.load_many(keys)
        assert isinstance(promise1, Promise)

        version_list = promise1.get()
        assert len(version_list) == 3

        assert version_list[0] == "8.0"
        assert version_list[1] == "2.9.1"
        assert version_list[2] == "3.2.5"

    def test_load_many_conda2(self, build_image_for_jupyterlab):
        """Test loading many labbooks"""
        lb, username = build_image_for_jupyterlab[0], build_image_for_jupyterlab[5]
        keys = ["conda3&cdutil", "conda3&python-coveralls", "conda3&nltk"]
        loader = PackageLatestVersionLoader(keys, lb, username)
        promise1 = loader.load_many(keys)
        assert isinstance(promise1, Promise)

        version_list = promise1.get()
        assert len(version_list) == 3
        assert version_list[0] == "8.0"
        assert version_list[1] == "2.9.1"
        assert version_list[2] == "3.2.5"

    def test_load_many_mixed(self, build_image_for_jupyterlab):
        """Test loading many labbooks"""
        lb, username = build_image_for_jupyterlab[0], build_image_for_jupyterlab[5]
        keys = ["conda3&cdutil", "pip&gtmunit1", "conda3&nltk"]
        loader = PackageLatestVersionLoader(keys, lb, username)
        promise1 = loader.load_many(keys)
        assert isinstance(promise1, Promise)

        version_list = promise1.get()
        assert len(version_list) == 3
        assert version_list[0] == "8.0"
        assert version_list[1] == "0.12.4"
        assert version_list[2] == "3.2.5"

    def test_load_invalid_package(self, build_image_for_jupyterlab):
        """Test loading many labbooks"""
        lb, username = build_image_for_jupyterlab[0], build_image_for_jupyterlab[5]
        keys = ["pip&scipysdfsdfs", "pip&numpy"]
        loader = PackageLatestVersionLoader(keys, lb, username)
        promise1 = loader.load_many(keys)
        assert isinstance(promise1, Promise)

        with pytest.raises(Exception):
            version_list = promise1.get()
