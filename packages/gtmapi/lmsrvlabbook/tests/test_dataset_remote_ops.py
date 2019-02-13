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
import responses

from gtmcore.inventory.inventory import InventoryManager

from snapshottest import snapshot
from lmsrvlabbook.tests.fixtures import fixture_working_dir

import pytest


DUMMY_DATA = [
    {
        "environment": {
            "base": {
                "name": "Python3 Minimal",
                "os_class": "ubuntu",
                "os_release": "18.04",
                "languages": [
                    "python3"
                ],
                "development_tools": [
                    "jupyterlab"
                ],
                "description": "A minimal Base containing Python 3.6 and JupyterLab with no additional packages"
            },
            "packages": {
                "pip": 1
            }
        },
        "hashed_namespace": "26fdb6eafd356c3e4ae0303f5f39e431|tester",
        "created_at": "2018-08-30T18:01:33.312Z",
        "namespace": "tester",
        "storage_size": 122,
        "project_schema": 1,
        "indexed_at": "2018-08-30T18:01:49.165815Z",
        "visibility": "private_dataset",
        "project": "test-data-1",
        "description": "No Description",
        "modified_at": "2018-08-30T18:01:33.312Z",
        "cursor": "eyJwYWdlIjogMSwgIml0ZW0iOiAxfQ=="
    },
    {
        "environment": {
            "base": {
                "name": "Python3 Minimal",
                "os_class": "ubuntu",
                "os_release": "18.04",
                "languages": [
                    "python3"
                ],
                "development_tools": [
                    "jupyterlab"
                ],
                "description": "A minimal Base containing Python 3.6 and JupyterLab with no additional packages"
            },
            "packages": {
                "pip": 1
            }
        },
        "hashed_namespace": "26fdb6eafd356c3e4ae0303f5f39e431|tester",
        "created_at": "2018-08-29T18:01:33.312Z",
        "namespace": "tester",
        "storage_size": 122,
        "project_schema": 1,
        "indexed_at": "2018-08-30T18:01:49.165815Z",
        "visibility": "private_dataset",
        "project": "test-data-2",
        "description": "No Description",
        "modified_at": "2018-09-01T18:01:33.312Z",
        "cursor": "eyJwYWdlIjogMSwgIml0ZW0iOiAzfQ=="
    }
]


class TestDatasetRemoteOperations(object):

    def test_list_remote_datasets_invalid_args(self, fixture_working_dir, snapshot):
        """test list datasets"""
        list_query = """
                    {
                    datasetList{
                      remoteDatasets(orderBy: "asdf", sort: "desc", first: 2){
                        edges{
                          node{
                            id
                            description
                            creationDateUtc
                            modifiedDateUtc
                            name
                            owner
                            isLocal
                          }
                          cursor
                        }
                        pageInfo{
                          hasNextPage
                        }
                      }
                    }
                    }"""
        r = fixture_working_dir[2].execute(list_query)
        assert 'errors' in r
        assert r['data']['datasetList']['remoteDatasets'] is None
        assert 'Unsupported order_by' in r['errors'][0]['message']

        list_query = """
                    {
                    datasetList{
                      remoteDatasets(orderBy: "name", sort: "asdf", first: 2){
                        edges{
                          node{
                            id
                            description
                            creationDateUtc
                            modifiedDateUtc
                            name
                            owner
                            isLocal
                          }
                          cursor
                        }
                        pageInfo{
                          hasNextPage
                        }
                      }
                    }
                    }"""
        r = fixture_working_dir[2].execute(list_query)
        assert 'errors' in r
        assert r['data']['datasetList']['remoteDatasets'] is None
        assert 'Unsupported sort' in r['errors'][0]['message']

    @responses.activate
    def test_list_remote_datasets_az(self, fixture_working_dir, snapshot):
        """test list datasets"""
        responses.add(responses.GET, 'https://api.gigantum.com/read/datasets?first=2&order_by=name&sort=desc',
                      json=DUMMY_DATA, status=200)
        responses.add(responses.GET, 'https://api.gigantum.com/read/datasets?first=3&order_by=name&sort=asc',
                      json=list(reversed(DUMMY_DATA)), status=200)
        responses.add(responses.GET, 'https://api.gigantum.com/read/datasets?first=3&after=eyJwYWdlIjogMSwgIml0ZW0iOiAzfQ==&order_by=name&sort=asc',
                      json=list(), status=200)

        list_query = """
                    {
                    datasetList{
                      remoteDatasets(orderBy: "name", sort: "desc", first: 2){
                        edges{
                          node{
                            id
                            description
                            creationDateUtc
                            modifiedDateUtc
                            name
                            owner
                            isLocal
                          }
                          cursor
                        }
                        pageInfo{
                          hasNextPage
                        }
                      }
                    }
                    }"""

        r = fixture_working_dir[2].execute(list_query)
        assert 'errors' not in r
        snapshot.assert_match(r)

        list_query = """
                    {
                    datasetList{
                      remoteDatasets(orderBy: "name", sort: "asc", first: 3){
                        edges{
                          node{
                            id
                            description
                            creationDateUtc
                            modifiedDateUtc
                            name
                            owner
                          }
                          cursor
                        }
                        pageInfo{
                          hasNextPage
                        }
                      }
                    }
                    }"""

        r = fixture_working_dir[2].execute(list_query)
        assert 'errors' not in r
        print(r)
        snapshot.assert_match(r)

        list_query = """
                    {
                    datasetList{
                      remoteDatasets(orderBy: "name", sort: "asc", first: 3, after: "eyJwYWdlIjogMSwgIml0ZW0iOiAzfQ=="){
                        edges{
                          node{
                            id
                            description
                            creationDateUtc
                            modifiedDateUtc
                            name
                            owner
                          }
                          cursor
                        }
                        pageInfo{
                          hasNextPage
                        }
                      }
                    }
                    }"""

        r = fixture_working_dir[2].execute(list_query)
        assert 'errors' not in r
        assert len(r['data']['datasetList']['remoteDatasets']['edges']) == 0
        assert r['data']['datasetList']['remoteDatasets']['pageInfo']['hasNextPage'] is False

    @responses.activate
    def test_list_remote_datasets_modified(self, fixture_working_dir, snapshot):
        """test list datasets"""
        """test list datasets"""
        responses.add(responses.GET, 'https://api.gigantum.com/read/datasets?first=2&page=1&order_by=modified_on&sort=desc',
                      json=list(reversed(DUMMY_DATA)), status=200)
        responses.add(responses.GET, 'https://api.gigantum.com/read/datasets?first=10&page=1&order_by=modified_on&sort=asc',
                      json=DUMMY_DATA, status=200)

        list_query = """
                    {
                    datasetList{
                      remoteDatasets(orderBy: "modified_on", sort: "desc", first: 2){
                        edges{
                          node{
                            id
                            description
                            creationDateUtc
                            modifiedDateUtc
                            name
                            owner
                            isLocal
                          }
                          cursor
                        }
                        pageInfo{
                          hasNextPage
                        }
                      }
                    }
                    }"""

        r = fixture_working_dir[2].execute(list_query)
        assert 'errors' not in r
        snapshot.assert_match(r)

        list_query = """
                    {
                    datasetList{
                      remoteDatasets(orderBy: "modified_on", sort: "asc", first: 10){
                        edges{
                          node{
                            id
                            description
                            creationDateUtc
                            modifiedDateUtc
                            name
                            owner
                          }
                          cursor
                        }
                        pageInfo{
                          hasNextPage
                        }
                      }
                    }
                    }"""

        r = fixture_working_dir[2].execute(list_query)
        assert 'errors' not in r
        snapshot.assert_match(r)

    @responses.activate
    def test_list_remote_datasets_created(self, fixture_working_dir, snapshot):
        """test list datasets"""
        responses.add(responses.GET, 'https://api.gigantum.com/read/datasets?first=2&page=1&order_by=created_on&sort=desc',
                      json=DUMMY_DATA, status=200)
        responses.add(responses.GET, 'https://api.gigantum.com/read/datasets?first=2&page=1&order_by=created_on&sort=asc',
                      json=list(reversed(DUMMY_DATA)), status=200)

        list_query = """
                    {
                    datasetList{
                      remoteDatasets(orderBy: "created_on", sort: "desc", first: 2){
                        edges{
                          node{
                            id
                            description
                            creationDateUtc
                            modifiedDateUtc
                            name
                            owner
                            isLocal
                          }
                          cursor
                        }
                        pageInfo{
                          hasNextPage
                        }
                      }
                    }
                    }"""

        r = fixture_working_dir[2].execute(list_query)
        assert 'errors' not in r
        snapshot.assert_match(r)

        list_query = """
                    {
                    datasetList{
                      remoteDatasets(orderBy: "created_on", sort: "asc", first: 10){
                        edges{
                          node{
                            id
                            description
                            creationDateUtc
                            modifiedDateUtc
                            name
                            owner
                          }
                          cursor
                        }
                        pageInfo{
                          hasNextPage
                        }
                      }
                    }
                    }"""

        r = fixture_working_dir[2].execute(list_query)
        assert 'errors' not in r
        snapshot.assert_match(r)

    @responses.activate
    def test_list_remote_datasets_page(self, fixture_working_dir, snapshot):
        """test list datasets"""
        responses.add(responses.GET, 'https://api.gigantum.com/read/datasets?first=1&order_by=name&sort=desc',
                      json=[DUMMY_DATA[0]], status=200)

        responses.add(responses.GET, 'https://api.gigantum.com/read/datasets?first=1&after=eyJwYWdlIjogMSwgIml0ZW0iOiAxfQ==&order_by=name&sort=desc',
                      json=[DUMMY_DATA[1]], status=200)

        responses.add(responses.GET, 'https://api.gigantum.com/read/datasets?first=1&after=eyJwYWdlIjogMSwgIml0ZW0iOiAzfQ==&order_by=name&sort=desc',
                      json=list(), status=200)

        list_query = """
                    {
                    datasetList{
                      remoteDatasets(orderBy: "name", sort: "desc", first: 1){
                        edges{
                          node{
                            id
                            description
                            creationDateUtc
                            modifiedDateUtc
                            name
                            owner
                            isLocal
                          }
                          cursor
                        }
                        pageInfo{
                          hasNextPage
                        }
                      }
                    }
                    }"""

        r = fixture_working_dir[2].execute(list_query)
        assert 'errors' not in r
        snapshot.assert_match(r)

        list_query = """
                    {
                    datasetList{
                      remoteDatasets(orderBy: "name", sort: "desc", first: 1, after: "eyJwYWdlIjogMSwgIml0ZW0iOiAxfQ=="){
                        edges{
                          node{
                            id
                            description
                            creationDateUtc
                            modifiedDateUtc
                            name
                            owner
                          }
                          cursor
                        }
                        pageInfo{
                          hasNextPage
                        }
                      }
                    }
                    }"""

        r = fixture_working_dir[2].execute(list_query)
        assert 'errors' not in r
        snapshot.assert_match(r)

        list_query = """
                    {
                    datasetList{
                      remoteDatasets(orderBy: "name", sort: "desc", first: 1, after: "eyJwYWdlIjogMSwgIml0ZW0iOiAzfQ=="){
                        edges{
                          node{
                            id
                            description
                            creationDateUtc
                            modifiedDateUtc
                            name
                            owner
                          }
                          cursor
                        }
                        pageInfo{
                          hasNextPage
                        }
                      }
                    }
                    }"""

        r = fixture_working_dir[2].execute(list_query)
        assert 'errors' not in r
        assert len(r['data']['datasetList']['remoteDatasets']['edges']) == 0
        assert r['data']['datasetList']['remoteDatasets']['pageInfo']['hasNextPage'] is False

