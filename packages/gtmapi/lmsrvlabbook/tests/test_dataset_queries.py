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
from snapshottest import snapshot
from lmsrvlabbook.tests.fixtures import fixture_working_dir_dataset_populated_scoped

from gtmcore.inventory.inventory import InventoryManager


class TestDatasetQueries(object):

    def test_get_dataset(self, fixture_working_dir_dataset_populated_scoped):
        query = """{
                    dataset(name: "dataset8", owner: "default") {
                      id
                      name
                      description
                      schemaVersion
                      datasetType{
                        name
                        id
                        description
                      }
                      visibility
                      defaultRemote
                    }
                    }
                """
        r = fixture_working_dir_dataset_populated_scoped[2].execute(query)
        assert r['data']['dataset']['description'] == 'Cats 8'
        assert r['data']['dataset']['datasetType']['description'] == 'Scalable Dataset storage provided by your Gigantum account'
        assert r['data']['dataset']['datasetType']['name'] == 'Gigantum Cloud'
        assert r['data']['dataset']['name'] == 'dataset8'
        assert r['data']['dataset']['schemaVersion'] == 1
        assert r['data']['dataset']['visibility'] == "local"
        assert r['data']['dataset']['defaultRemote'] is None

    def test_get_dataset_all_fields(self, fixture_working_dir_dataset_populated_scoped, snapshot):
        query = """{
                    dataset(name: "dataset8", owner: "default") {
                      id
                      name
                      description
                      schemaVersion
                      activityRecords{
                        edges{
                            node{
                                message
                                type
                                show
                                importance
                                tags
                                }
                            }                    
                        pageInfo{
                            hasNextPage
                            hasPreviousPage
                        }
                      }
                      datasetType{
                        name
                        id
                        description
                        storageType
                        readme
                        tags
                        icon
                      }
                    }
                    }
                """
        snapshot.assert_match(fixture_working_dir_dataset_populated_scoped[2].execute(query))

        query = """{
                    dataset(name: "dataset8", owner: "default") {
                      name
                      createdOnUtc
                      modifiedOnUtc
                      
                    }
                    }
                """
        result = fixture_working_dir_dataset_populated_scoped[2].execute(query)
        assert isinstance(result['data']['dataset']['createdOnUtc'], str) is True
        assert isinstance(result['data']['dataset']['modifiedOnUtc'], str) is True
        assert len(result['data']['dataset']['createdOnUtc']) > 10
        assert len(result['data']['dataset']['modifiedOnUtc']) > 10

    def test_pagination_noargs(self, fixture_working_dir_dataset_populated_scoped, snapshot):
        query = """
                {
                datasetList{
                    localDatasets {
                        edges {
                            node {
                                name
                                description
                            }
                            cursor
                        }
                        pageInfo {
                            hasNextPage
                            hasPreviousPage
                        }
                    }
                }
                }
                """
        snapshot.assert_match(fixture_working_dir_dataset_populated_scoped[2].execute(query))

    def test_pagination_sort_az_reverse(self, fixture_working_dir_dataset_populated_scoped, snapshot):
        query = """
                {
                datasetList{
                    localDatasets(orderBy: "name", sort: "desc") {
                        edges {
                            node {
                                id
                                name
                                description
                                datasetType{
                                  storageType
                                  name
                                  description
                                }
                            }
                            cursor
                        }
                        pageInfo {
                            hasNextPage
                            hasPreviousPage
                        }
                    }
                }
                }
                """
        snapshot.assert_match(fixture_working_dir_dataset_populated_scoped[2].execute(query))

    def test_pagination_sort_create(self, fixture_working_dir_dataset_populated_scoped, snapshot):
        query = """
                {
                datasetList{
                    localDatasets(orderBy: "created_on") {
                        edges {
                            node {
                                id
                                name
                                description
                            }
                            cursor
                        }
                        pageInfo {
                            hasNextPage
                            hasPreviousPage
                        }
                    }
                }
                }
                """
        snapshot.assert_match(fixture_working_dir_dataset_populated_scoped[2].execute(query))

    def test_pagination_sort_create_desc(self, fixture_working_dir_dataset_populated_scoped, snapshot):
        query = """
                {
                datasetList{
                    localDatasets(orderBy: "created_on", sort: "desc") {
                        edges {
                            node {
                                id
                                name
                                description
                            }
                            cursor
                        }
                        pageInfo {
                            hasNextPage
                            hasPreviousPage
                        }
                    }
                }
                }
                """
        snapshot.assert_match(fixture_working_dir_dataset_populated_scoped[2].execute(query))

    def test_pagination_sort_modified(self, fixture_working_dir_dataset_populated_scoped, snapshot):

        query = """
                {
                datasetList{
                    localDatasets(orderBy: "modified_on", sort: "desc") {
                        edges {
                            node {
                                id
                                name
                                description
                            }
                            cursor
                        }
                        pageInfo {
                            hasNextPage
                            hasPreviousPage
                        }
                    }
                }
                }
                """
        snapshot.assert_match(fixture_working_dir_dataset_populated_scoped[2].execute(query))

        im = InventoryManager(fixture_working_dir_dataset_populated_scoped[0])
        ds = im.load_dataset("default", "default", "dataset4")
        with open(os.path.join(ds.root_dir, "test.txt"), 'wt') as tf:
            tf.write("asdfasdf")
        ds.git.add_all()
        ds.git.commit("Changing the repo")

        # Run query again
        snapshot.assert_match(fixture_working_dir_dataset_populated_scoped[2].execute(query))

    def test_pagination(self, fixture_working_dir_dataset_populated_scoped, snapshot):
        """Test pagination and cursors"""
        query = """
                {
                datasetList{
                    localDatasets(first: 2) {
                        edges {
                            node {
                                name
                                description
                            }
                            cursor
                        }
                        pageInfo {
                            hasNextPage
                            hasPreviousPage
                        }
                    }
                }
                }
                """
        snapshot.assert_match(fixture_working_dir_dataset_populated_scoped[2].execute(query))

        query = """
                {
                datasetList{
                    localDatasets(first: 5, after: "MQ==") {
                        edges {
                            node {
                                name
                                description
                            }
                            cursor
                        }
                        pageInfo {
                            hasNextPage
                            hasPreviousPage
                        }
                    }
                }
                }
                """
        snapshot.assert_match(fixture_working_dir_dataset_populated_scoped[2].execute(query))

        query = """
                {
                datasetList{
                    localDatasets(first: 3, after: "Ng==") {
                        edges {
                            node {
                                name
                                description
                            }
                            cursor
                        }
                        pageInfo {
                            hasNextPage
                            hasPreviousPage
                        }
                    }
                }
                }
                """
        snapshot.assert_match(fixture_working_dir_dataset_populated_scoped[2].execute(query))

        query = """
                {
                datasetList{
                    localDatasets(first: 3, after: "OQ==") {
                        edges {
                            node {
                                name
                                description
                            }
                            cursor
                        }
                        pageInfo {
                            hasNextPage
                            hasPreviousPage
                        }
                    }
                }
                }
                """
        snapshot.assert_match(fixture_working_dir_dataset_populated_scoped[2].execute(query))
