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
import io
import math
import os
import tempfile
import datetime
import pprint
from zipfile import ZipFile
from pkg_resources import resource_filename
import getpass
import json

from gtmcore.fixtures import ENV_UNIT_TEST_REPO, ENV_UNIT_TEST_BASE, ENV_UNIT_TEST_REV
from gtmcore.files import FileOperations

from snapshottest import snapshot
from lmsrvlabbook.tests.fixtures import fixture_working_dir_env_repo_scoped, fixture_working_dir

import pytest
from graphene.test import Client
from mock import patch
from werkzeug.datastructures import FileStorage

from gtmcore.configuration import Configuration
from gtmcore.dispatcher.jobs import export_labbook_as_zip
from gtmcore.files import FileOperations
from gtmcore.fixtures import remote_labbook_repo, mock_config_file

from gtmcore.inventory.inventory import InventoryManager

from lmsrvcore.middleware import error_middleware, DataloaderMiddleware


@pytest.fixture()
def mock_create_labbooks(fixture_working_dir):
    # Create a labbook in the temporary directory
    # Create a temporary labbook
    lb = InventoryManager(fixture_working_dir[0]).create_labbook("default", "default", "labbook1",
                                                                 description="Cats labbook 1")

    # Create a file in the dir
    with open(os.path.join(fixture_working_dir[1], 'sillyfile'), 'w') as sf:
        sf.write("1234567")
        sf.seek(0)
    FileOperations.insert_file(lb, 'code', sf.name)

    assert os.path.isfile(os.path.join(lb.root_dir, 'code', 'sillyfile'))
    # name of the config file, temporary working directory, the schema
    yield fixture_working_dir


class TestLabBookServiceMutations(object):
    def test_create_labbook(self, fixture_working_dir_env_repo_scoped, snapshot):
        """Test listing labbooks"""
        # Mock the configuration class it it returns the same mocked config file
        # Create LabBook
        query = """
        mutation myCreateLabbook($name: String!, $desc: String!, $repository: String!, 
                                 $base_id: String!, $revision: Int!) {
          createLabbook(input: {name: $name, description: $desc, 
                                repository: $repository, 
                                baseId: $base_id, revision: $revision}) {
            labbook {
              id
              name
              description
            }
          }
        }
        """
        variables = {"name": "test-lab-book1", "desc": "my test description",
                     "base_id": ENV_UNIT_TEST_BASE, "repository": ENV_UNIT_TEST_REPO,
                     "revision": ENV_UNIT_TEST_REV}
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query, variable_values=variables))

        # Get LabBook you just created
        query = """
        {
          labbook(name: "test-lab-book1", owner: "default") {               
            activityRecords {
                edges{
                    node{
                        message
                        type
                        show
                        importance
                        tags
                        username
                        email
                        detailObjects{
                            type
                            data
                            show
                            importance
                            tags
                        }
                        }                        
                    }    
            }
          }
        }
        """
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query))

    def test_delete_labbook(self, mock_create_labbooks, fixture_working_dir_env_repo_scoped):
        """Test deleting a LabBook off disk. """
        labbook_dir = os.path.join(mock_create_labbooks[1], 'default', 'default', 'labbooks', 'labbook1')

        assert os.path.exists(labbook_dir)

        delete_query = f"""
        mutation delete {{
            deleteLabbook(input: {{
                owner: "default",
                labbookName: "labbook1",
                confirm: true
            }}) {{
                success
            }}
        }}
        """

        r = fixture_working_dir_env_repo_scoped[2].execute(delete_query)
        assert 'errors' not in r
        assert r['data']['deleteLabbook']['success'] is True
        assert not os.path.exists(labbook_dir)

    def test_update_labbook_description(self, mock_create_labbooks, fixture_working_dir_env_repo_scoped):
        labbook_dir = os.path.join(mock_create_labbooks[1], 'default', 'default', 'labbooks', 'labbook1')
        assert os.path.exists(labbook_dir)

        desc_md = f"# Titłe\n ## \"Subtitle\"\n{'æbčdęfghį:*&^&%$%$@!_t ' * 200}. ## Ænother Sübtitle's\n{'xyz.?/<>č ' * 300}.\n"
        #desc_md = "abc"
        description_query = f"""
        mutation setDesc($content: String!) {{
            setLabbookDescription(input: {{
                owner: "default",
                labbookName: "labbook1",
                descriptionContent: $content
            }}) {{
                success
            }}
        }}
        """
        variables = {'content': desc_md}
        r = fixture_working_dir_env_repo_scoped[2].execute(description_query, variable_values=variables)
        assert 'errors' not in r
        assert r['data']['setLabbookDescription']['success'] is True

        # Get LabBook you just created
        query = """
        {
          labbook(name: "labbook1", owner: "default") {
            description
            isRepoClean
          }
        }
        """
        r = fixture_working_dir_env_repo_scoped[2].execute(query)
        assert 'errors' not in r
        # There's a lot of weird characters getting filtered out, make sure the bulk of the text remains
        assert abs(1.0 * len(r['data']['labbook']['description']) / len(desc_md)) > 0.75
        assert r['data']['labbook']['isRepoClean'] == True

    def test_delete_labbook_dry_run(self, mock_create_labbooks, fixture_working_dir_env_repo_scoped):
        """Test deleting a LabBook off disk. """
        labbook_dir = os.path.join(mock_create_labbooks[1], 'default', 'default', 'labbooks', 'labbook1')

        assert os.path.exists(labbook_dir)

        delete_query = f"""
        mutation delete {{
            deleteLabbook(input: {{
                owner: "default",
                labbookName: "labbook1",
                confirm: false
            }}) {{
                success
            }}
        }}
        """

        r = fixture_working_dir_env_repo_scoped[2].execute(delete_query)
        assert 'errors' not in r
        assert r['data']['deleteLabbook']['success'] is False
        assert os.path.exists(labbook_dir)

    def test_set_lb_for_untracked_ins_and_outs(self, fixture_working_dir_env_repo_scoped):
        query = """
        mutation myCreateLabbook($name: String!, $desc: String!, $repository: String!, 
                                 $component_id: String!, $revision: Int!) {
          createLabbook(input: {name: $name, description: $desc, 
                                repository: $repository, 
                                baseId: $component_id,
                                revision: $revision,
                                isUntracked: true}) {
            labbook {
              id
              name
              description
              input {
                isUntracked
              }
              output {
                isUntracked
              }
              code {
                isUntracked
              }
            }
          }
        }
        """
        variables = {"name": "unittest-untracked-inout-1", "desc": "my test description",
                     "component_id": ENV_UNIT_TEST_BASE, "repository": ENV_UNIT_TEST_REPO,
                     "revision": ENV_UNIT_TEST_REV}
        r = fixture_working_dir_env_repo_scoped[2].execute(query, variable_values=variables)
        assert 'errors' not in r
        assert r['data']['createLabbook']['labbook']['input']['isUntracked'] is True
        assert r['data']['createLabbook']['labbook']['output']['isUntracked'] is True
        assert r['data']['createLabbook']['labbook']['code']['isUntracked'] is False

    def test_create_labbook_already_exists(self, fixture_working_dir_env_repo_scoped, snapshot):
        """Test listing labbooks"""
        query = """
        mutation myCreateLabbook($name: String!, $desc: String!, $repository: String!, 
                                 $base_id: String!, $revision: Int!) {
          createLabbook(input: {name: $name, description: $desc, 
                                repository: $repository, 
                                baseId: $base_id, revision: $revision}) {
            labbook {
              id
              name
              description
            }
          }
        }
        """
        variables = {"name": "test-lab-duplicate", "desc": "my test description",
                     "base_id": ENV_UNIT_TEST_BASE, "repository": ENV_UNIT_TEST_REPO,
                     "revision": ENV_UNIT_TEST_REV}
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query, variable_values=variables))

        # Get LabBook you just created
        check_query = """
        {
          labbook(name: "test-lab-duplicate", owner: "default") {   
            name
            description
          }
        }
        """
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(check_query))

        # Second should fail with an error message
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query, variable_values=variables))

    def test_move_file(self, mock_create_labbooks):
        """Test moving a file"""
        labbook_dir = os.path.join(mock_create_labbooks[1], 'default', 'default', 'labbooks', 'labbook1')
        os.makedirs(os.path.join(labbook_dir, 'code', 'subdir'))

        query = """
        mutation MoveLabbookFile {
            moveLabbookFile(
                input: {
                    owner: "default",
                    labbookName: "labbook1",
                    section: "code",
                    srcPath: "sillyfile",
                    dstPath: "subdir/sillyfile"
                }) {
                updatedEdges {
                    node {
                        id
                        key
                        isDir
                        size
                        section
                    }                    
                }
            }
        }
        """
        result_1 = mock_create_labbooks[2].execute(query)
        assert 'errors' not in result_1
        nodes = result_1['data']['moveLabbookFile']['updatedEdges']
        assert len(nodes) == 1
        assert nodes[0]['node']['key'] == 'subdir/sillyfile'
        assert nodes[0]['node']['isDir'] is False
        assert nodes[0]['node']['size'] == '7'
        assert nodes[0]['node']['section'] == 'code'

        os.makedirs(os.path.join(labbook_dir, 'code', 'subdir2'))
        query = """
        mutation MoveLabbookFile {
            moveLabbookFile(
                input: {
                owner: "default",
                labbookName: "labbook1",
                section: "code",
                srcPath: "subdir",
                dstPath: "subdir2"
            }) {
                updatedEdges {
                    node {
                        id
                        section
                        key
                        isDir
                        size
                    }                
                }
            }
        }
        """
        result_2 = mock_create_labbooks[2].execute(query)
        assert 'errors' not in result_2
        nodes = result_2['data']['moveLabbookFile']['updatedEdges']
        assert len(nodes) == 2
        assert nodes[0]['node']['key'] == 'subdir2/subdir/'
        assert nodes[0]['node']['isDir'] is True
        assert nodes[0]['node']['section'] == 'code'
        assert nodes[1]['node']['key'] == 'subdir2/subdir/sillyfile'
        assert nodes[1]['node']['isDir'] is False
        assert nodes[1]['node']['section'] == 'code'

        assert os.path.exists(os.path.join(labbook_dir, 'code', 'subdir2', 'subdir', 'sillyfile')) is True

    def test_move_file_many_times(self, mock_create_labbooks):
        """Test moving a file around a bunch"""
        labbook_dir = os.path.join(mock_create_labbooks[1], 'default', 'default', 'labbooks', 'labbook1', 'code')
        os.makedirs(os.path.join(labbook_dir, 'subdir'))

        query1 = """
        mutation MoveLabbookFile {
            moveLabbookFile(input: {
                owner: "default",
                labbookName: "labbook1",
                section: "code",
                srcPath: "sillyfile",
                dstPath: "subdir/sillyfile"
            }) {
                updatedEdges {
                    node {
                        section
                        key
                        isDir
                        size
                    }
            }
            }
        }
        """

        query2 = """
        mutation MoveLabbookFile {
            moveLabbookFile(input: {
                owner: "default",
                labbookName: "labbook1",
                section: "code",
                srcPath: "subdir/sillyfile",
                dstPath: "sillyfile"
            }) {
                updatedEdges {
                    node {
                        section
                        key
                        isDir
                        size
                    }
                }
            }
        }
        """
        result1 = mock_create_labbooks[2].execute(query1)
        assert 'errors' not in result1
        assert len(result1['data']['moveLabbookFile']['updatedEdges']) == 1
        assert result1['data']['moveLabbookFile']['updatedEdges'][0]['node']['key'] == 'subdir/sillyfile'
        assert result1['data']['moveLabbookFile']['updatedEdges'][0]['node']['isDir'] == False
        assert os.path.exists(os.path.join(labbook_dir, 'subdir', 'sillyfile'))
        assert os.path.isfile(os.path.join(labbook_dir, 'subdir', 'sillyfile'))

        result2 = mock_create_labbooks[2].execute(query2)
        assert 'errors' not in result2
        assert len(result2['data']['moveLabbookFile']['updatedEdges']) == 1
        assert result2['data']['moveLabbookFile']['updatedEdges'][0]['node']['key'] == 'sillyfile'
        assert result2['data']['moveLabbookFile']['updatedEdges'][0]['node']['isDir'] == False
        assert os.path.exists(os.path.join(labbook_dir, 'sillyfile'))
        assert os.path.isfile(os.path.join(labbook_dir, 'sillyfile'))

        result3 = mock_create_labbooks[2].execute(query1)
        assert 'errors' not in result3
        assert len(result3['data']['moveLabbookFile']['updatedEdges']) == 1
        assert result3['data']['moveLabbookFile']['updatedEdges'][0]['node']['key'] == 'subdir/sillyfile'
        assert result3['data']['moveLabbookFile']['updatedEdges'][0]['node']['isDir'] == False
        assert os.path.exists(os.path.join(labbook_dir, 'subdir', 'sillyfile'))
        assert os.path.isfile(os.path.join(labbook_dir, 'subdir', 'sillyfile'))

        result4 = mock_create_labbooks[2].execute(query2)
        assert len(result4['data']['moveLabbookFile']['updatedEdges']) == 1
        assert result4['data']['moveLabbookFile']['updatedEdges'][0]['node']['key'] == 'sillyfile'
        assert result4['data']['moveLabbookFile']['updatedEdges'][0]['node']['isDir'] == False
        assert os.path.exists(os.path.join(labbook_dir, 'sillyfile'))
        assert os.path.isfile(os.path.join(labbook_dir, 'sillyfile'))

        result5 = mock_create_labbooks[2].execute(query1)
        assert len(result5['data']['moveLabbookFile']['updatedEdges']) == 1
        assert result5['data']['moveLabbookFile']['updatedEdges'][0]['node']['key'] == 'subdir/sillyfile'
        assert result5['data']['moveLabbookFile']['updatedEdges'][0]['node']['isDir'] == False
        assert os.path.exists(os.path.join(labbook_dir, 'subdir', 'sillyfile'))
        assert os.path.isfile(os.path.join(labbook_dir, 'subdir', 'sillyfile'))

    def test_delete_file(self, mock_create_labbooks):
        query = """
        mutation deleteLabbookFiless {
          deleteLabbookFiles(
            input: {
              owner: "default",
              labbookName: "labbook1",
              section: "code",
              filePaths: ["sillyfile"]
            }) {
              success
            }
        }
        """
        filepath = os.path.join(mock_create_labbooks[1], 'default', 'default', 'labbooks', 'labbook1',
                                'code', 'sillyfile')
        assert os.path.exists(filepath) is True

        res = mock_create_labbooks[2].execute(query)
        assert res['data']['deleteLabbookFiles']['success'] is True

        assert os.path.exists(filepath) is False

    def test_delete_dir(self, mock_create_labbooks):
        im = InventoryManager(mock_create_labbooks[0])
        lb = im.load_labbook('default', 'default', 'labbook1')
        FileOperations.makedir(lb, 'code/subdir')

        test_file = os.path.join(lb.root_dir, 'code', 'subdir', 'test.txt')
        with open(test_file, 'wt') as tf:
            tf.write("puppers")

        lb.git.add_all('code/')
        lb.git.commit("blah")

        dir_path = os.path.join(lb.root_dir, 'code', 'subdir')
        assert os.path.exists(dir_path) is True
        assert os.path.exists(test_file) is True

        # Note, deleting a file should work with and without a trailing / at the end.
        query = """
        mutation deleteLabbookFiles {
          deleteLabbookFiles(
            input: {
              owner: "default",
              labbookName: "labbook1",
              section: "code",
              filePaths: ["subdir/"]
            }) {
              success
            }
        }
        """
        res = mock_create_labbooks[2].execute(query)
        print(res)
        assert res['data']['deleteLabbookFiles']['success'] is True

        assert os.path.exists(dir_path) is False
        assert os.path.exists(test_file) is False
        assert os.path.exists(os.path.join(lb.root_dir, 'code')) is True

    def test_makedir(self, mock_create_labbooks, snapshot):
        query = """
        mutation makeLabbookDirectory {
          makeLabbookDirectory(
            input: {
              owner: "default",
              labbookName: "labbook1",
              section: "output",
              directory: "new_folder",
            }) {
              newLabbookFileEdge {
                node{
                  key
                  isDir
                  size
                }
              }
            }}"""
        snapshot.assert_match(mock_create_labbooks[2].execute(query))


    def test_add_favorite(self, mock_create_labbooks, snapshot):
        """Method to test adding a favorite"""

        # Verify no favs
        fav_query = """
                   {
                     labbook(name: "labbook1", owner: "default") {
                       name
                       code{
                           favorites{
                               edges {
                                   node {
                                       id
                                       index
                                       key
                                       description
                                       isDir
                                   }
                               }
                           }
                       }
                     }
                   }
                   """
        snapshot.assert_match(mock_create_labbooks[2].execute(fav_query))

        test_file = os.path.join(mock_create_labbooks[1], 'default', 'default', 'labbooks',
                                 'labbook1', 'code', 'test.txt')
        with open(test_file, 'wt') as tf:
            tf.write("a test file...")

        # Add a favorite in code
        query = """
        mutation addFavorite {
          addFavorite(
            input: {
              owner: "default",
              labbookName: "labbook1",
              section: "code",
              key: "test.txt",
              description: "my test favorite"
            }) {
              newFavoriteEdge{
                node {
                   id
                   index
                   key
                   description
                   isDir
                }
              }
            }
        }
        """
        snapshot.assert_match(mock_create_labbooks[2].execute(query))

        # Verify the favorite is there
        snapshot.assert_match(mock_create_labbooks[2].execute(fav_query))

    def test_add_favorite_dir(self, mock_create_labbooks, snapshot):
        """Method to test adding a favorite"""
        # Verify no favs
        fav_query = """
                   {
                     labbook(name: "labbook1", owner: "default") {
                       name
                       input{
                           favorites{
                               edges {
                                   node {
                                       id
                                       index
                                       key
                                       description
                                       isDir
                                   }
                               }
                           }
                       }
                     }
                   }
                   """
        snapshot.assert_match(mock_create_labbooks[2].execute(fav_query))

        os.makedirs(os.path.join(mock_create_labbooks[1], 'default', 'default', 'labbooks',
                                 'labbook1', 'input', 'sample1'))
        os.makedirs(os.path.join(mock_create_labbooks[1], 'default', 'default', 'labbooks',
                                 'labbook1', 'input', 'sample2'))

        # Add a favorite in code
        query = """
        mutation addFavorite {
          addFavorite(
            input: {
              owner: "default",
              labbookName: "labbook1",
              section: "input",
              key: "sample1",
              description: "my data dir",
              isDir: true
            }) {
              newFavoriteEdge{
                node{
                   id
                   index
                   key
                   description
                   isDir
                   }
              }
            }
        }
        """
        snapshot.assert_match(mock_create_labbooks[2].execute(query))

        # Verify the favorite is there
        snapshot.assert_match(mock_create_labbooks[2].execute(fav_query))

        # Add a favorite in code
        query = """
        mutation addFavorite {
          addFavorite(
            input: {
              owner: "default",
              labbookName: "labbook1",
              section: "input",
              key: "sample2/",
              description: "my data dir 2",
              isDir: true
            }) {
              newFavoriteEdge{
                node{
                   id
                   index
                   key
                   description
                   isDir
                   }
              }
            }
        }
        """
        snapshot.assert_match(mock_create_labbooks[2].execute(query))

        # Verify the favorite is there
        snapshot.assert_match(mock_create_labbooks[2].execute(fav_query))

    def test_update_favorite(self, mock_create_labbooks, snapshot):
        """Method to test updating a favorite"""
        # Verify no favs
        fav_query = """
                   {
                     labbook(name: "labbook1", owner: "default") {
                       name
                       code{
                           favorites{
                               edges {
                                   node {
                                       id
                                       index
                                       key
                                       description
                                       isDir
                                   }
                               }
                           }
                       }
                     }
                   }
                   """
        snapshot.assert_match(mock_create_labbooks[2].execute(fav_query))

        test_file = os.path.join(mock_create_labbooks[1], 'default', 'default', 'labbooks',
                                 'labbook1', 'code', 'test.txt')
        test_file2 = os.path.join(mock_create_labbooks[1], 'default', 'default', 'labbooks',
                                  'labbook1', 'code', 'test2.txt')
        with open(test_file, 'wt') as tf:
            tf.write("a test file...")
        with open(test_file2, 'wt') as tf:
            tf.write("a test file...")

        # Add a favorite in code
        query = """
        mutation addFavorite {
          addFavorite(
            input: {
              owner: "default",
              labbookName: "labbook1",
              section: "code",
              key: "test.txt",
              description: "my test favorite"
            }) {
              newFavoriteEdge{
                node {
                   id
                   index
                   key
                   description
                   isDir
                }
              }
            }
        }
        """
        snapshot.assert_match(mock_create_labbooks[2].execute(query))

        # Add a favorite in code
        query = """
        mutation addFavorite {
          addFavorite(
            input: {
              owner: "default",
              labbookName: "labbook1",
              section: "code",
              key: "test2.txt",
              description: "my test favorite 2"
            }) {
              newFavoriteEdge{
                node {
                   id
                   index
                   key
                   description
                   isDir
                }
              }
            }
        }
        """
        snapshot.assert_match(mock_create_labbooks[2].execute(query))

        # Verify the favorites are there
        snapshot.assert_match(mock_create_labbooks[2].execute(fav_query))

        query = """
        mutation updateFavorite {
          updateFavorite(
            input: {
              owner: "default",
              labbookName: "labbook1",
              section: "code",
              updatedIndex: 0,
              key: "test2.txt",
              updatedDescription: "UPDATED"
            }) {
              updatedFavoriteEdge{
                node {
                   id
                   index
                   key
                   description
                   isDir
                }
              }
            }
        }
        """
        snapshot.assert_match(mock_create_labbooks[2].execute(query))

        # Make sure they are reordered
        snapshot.assert_match(mock_create_labbooks[2].execute(fav_query))

    def test_delete_favorite(self, mock_create_labbooks, snapshot):
        """Method to test adding a favorite"""
        test_file = os.path.join(mock_create_labbooks[1], 'default', 'default', 'labbooks',
                                 'labbook1', 'code', 'test.txt')
        with open(test_file, 'wt') as tf:
            tf.write("a test file...")

        # Add a favorite in code
        query = """
        mutation addFavorite {
          addFavorite(
            input: {
              owner: "default",
              labbookName: "labbook1",
              section: "code",
              key: "test.txt",
              description: "my test favorite"
            }) {
              newFavoriteEdge{
                node{
                   id
                   index
                   key
                   description
                   isDir
                   }
              }
            }
        }
        """
        snapshot.assert_match(mock_create_labbooks[2].execute(query))


        # Verify the favorite is there
        fav_query = """
        {
         labbook(name: "labbook1", owner: "default") {
           name
           code{
               favorites{
                   edges {
                       node {
                           id
                           index
                           key
                           description
                           isDir
                       }
                   }
               }
           }
         }
        }
        """
        snapshot.assert_match(mock_create_labbooks[2].execute(fav_query))

        # Delete a favorite in code
        query = """
        mutation deleteFavorite {
          removeFavorite(
            input: {
              owner: "default",
              labbookName: "labbook1",
              section: "code",
              key: "test.txt"
            }) {
              success
              removedNodeId
            }
        }
        """
        snapshot.assert_match(mock_create_labbooks[2].execute(query))

        # Make sure favorite is gone now
        snapshot.assert_match(mock_create_labbooks[2].execute(fav_query))

    def test_import_labbook(self, fixture_working_dir):
        """Test batch uploading, but not full import"""
        class DummyContext(object):
            def __init__(self, file_handle):
                self.labbook_loader = None
                self.files = {'uploadChunk': file_handle}

        client = Client(fixture_working_dir[3], middleware=[DataloaderMiddleware()])

        # Create a temporary labbook
        lb = InventoryManager(fixture_working_dir[0]).create_labbook("default", "default", "test-export",
                                                                     description="Tester")

        # Create a largeish file in the dir
        with open(os.path.join(fixture_working_dir[1], 'testfile.bin'), 'wb') as testfile:
            testfile.write(os.urandom(9000000))
        FileOperations.insert_file(lb, 'input', testfile.name)

        # Export labbook
        zip_file = export_labbook_as_zip(lb.root_dir, tempfile.gettempdir())
        lb_dir = lb.root_dir

        # Get upload params
        chunk_size = 4194304
        file_info = os.stat(zip_file)
        file_size = int(file_info.st_size / 1000)
        total_chunks = int(math.ceil(file_info.st_size/chunk_size))

        with open(zip_file, 'rb') as tf:
            for chunk_index in range(total_chunks):
                chunk = io.BytesIO()
                chunk.write(tf.read(chunk_size))
                chunk.seek(0)
                file = FileStorage(chunk)

                query = f"""
                            mutation myMutation{{
                              importLabbook(input:{{
                                chunkUploadParams:{{
                                  uploadId: "jfdjfdjdisdjwdoijwlkfjd",
                                  chunkSize: {chunk_size},
                                  totalChunks: {total_chunks},
                                  chunkIndex: {chunk_index},
                                  fileSizeKb: {file_size},
                                  filename: "{os.path.basename(zip_file)}"
                                }}
                              }}) {{
                                importJobKey
                              }}
                            }}
                            """
                result = client.execute(query, context_value=DummyContext(file))
                assert "errors" not in result
                if chunk_index == total_chunks - 1:
                    assert type(result['data']['importLabbook']['importJobKey']) == str
                    assert "rq:job:" in result['data']['importLabbook']['importJobKey']

                chunk.close()

    def test_write_readme(self, mock_create_labbooks, snapshot):
        content = json.dumps('##Overview\n\nThis is my readme\n :df,a//3p49kasdf')

        query = f"""
        mutation writeReadme {{
          writeLabbookReadme(
            input: {{
              owner: "default",
              labbookName: "labbook1",
              content: {content},
            }}) {{
              updatedLabbook{{
                name
                description
                overview{{
                    readme
                }}
              }}
            }}
        }}
        """
        snapshot.assert_match(mock_create_labbooks[2].execute(query))

    def test_fetch_labbook_edge(self, mock_create_labbooks):
        query = f"""
        mutation f {{
            fetchLabbookEdge(input:{{
                owner: "default",
                labbookName: "labbook1"
            }}) {{
                newLabbookEdge {{
                    node {{
                        name
                        owner
                    }}
                }}
            }}
        }}
        """
        r = mock_create_labbooks[2].execute(query)
        assert 'errors' not in r
        assert r['data']['fetchLabbookEdge']['newLabbookEdge']['node']['owner'] == 'default'
        assert r['data']['fetchLabbookEdge']['newLabbookEdge']['node']['name'] == 'labbook1'

