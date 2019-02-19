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
import os
import responses

import pytest
from mock import patch
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from gtmcore.fixtures import (_MOCK_create_remote_repo2, remote_bare_repo, mock_config_file)
from gtmcore.labbook import LabBook
from gtmcore.inventory.inventory import InventoryManager
from gtmcore.workflows import LabbookWorkflow, GitWorkflow
from gtmcore.files import FileOperations

from .fixtures import fixture_working_dir, fixture_working_dir_lfs_disabled

@pytest.fixture()
def mock_create_labbooks(fixture_working_dir):
    # Create a labbook in the temporary directory
    im = InventoryManager(fixture_working_dir[0])
    lb = im.create_labbook("default", "default", "labbook1",
                           description="Cats labbook 1")

    # Create a file in the dir
    with open(os.path.join(fixture_working_dir[1], 'sillyfile'), 'w') as sf:
        sf.write("1234567")
        sf.seek(0)
    FileOperations.insert_file(lb, 'code', sf.name)

    assert os.path.isfile(os.path.join(lb.root_dir, 'code', 'sillyfile'))
    # name of the config file, temporary working directory, the schema
    yield fixture_working_dir


@pytest.fixture()
def mock_create_labbooks_no_lfs(fixture_working_dir_lfs_disabled):
    # Create a labbook in the temporary directory
    im = InventoryManager(fixture_working_dir_lfs_disabled[0])
    lb = im.create_labbook("default", "default", "labbook1",
                           description="Cats labbook 1")

    # Create a file in the dir
    with open(os.path.join(fixture_working_dir_lfs_disabled[1], 'sillyfile'), 'w') as sf:
        sf.write("1234567")
        sf.seek(0)
    FileOperations.insert_file(lb, 'code', sf.name)

    assert os.path.isfile(os.path.join(lb.root_dir, 'code', 'sillyfile'))
    # name of the config file, temporary working directory, the schema
    yield fixture_working_dir_lfs_disabled


class TestLabbookShareProtocol(object):
    @patch('gtmcore.workflows.gitworkflows_utils.create_remote_gitlab_repo', new=_MOCK_create_remote_repo2)
    def test_publish_basic(self, fixture_working_dir, mock_create_labbooks_no_lfs):

        # Mock the request context so a fake authorization header is present
        builder = EnvironBuilder(path='/labbook', method='POST', headers={'Authorization': 'Bearer AJDFHASD'})
        env = builder.get_environ()
        req = Request(environ=env)

        im = InventoryManager(mock_create_labbooks_no_lfs[0])
        test_user_lb = im.load_labbook('default', 'default', 'labbook1')

        publish_query = f"""
        mutation c {{
            publishLabbook(input: {{
                labbookName: "labbook1",
                owner: "default"
            }}) {{
                jobKey
            }}
        }}
        """

        r = mock_create_labbooks_no_lfs[2].execute(publish_query, context_value=req)
        assert 'errors' not in r
        # TODO - Pause and wait for bg job to finish
        #assert r['data']['publishLabbook']['success'] is True

    @responses.activate
    @patch('gtmcore.workflows.gitworkflows_utils.create_remote_gitlab_repo', new=_MOCK_create_remote_repo2)
    def test_sync_1(self, mock_create_labbooks_no_lfs, mock_config_file):

        # Setup responses mock for this test
        responses.add(responses.GET, 'https://usersrv.gigantum.io/key',
                      json={'key': 'afaketoken'}, status=200)

        im = InventoryManager(mock_create_labbooks_no_lfs[0])
        test_user_lb = im.load_labbook('default', 'default', 'labbook1')
        test_user_wf = LabbookWorkflow(test_user_lb)
        test_user_wf.publish('default')

        # Mock the request context so a fake authorization header is present
        builder = EnvironBuilder(path='/labbook', method='POST', headers={'Authorization': 'Bearer AJDFHASD'})
        env = builder.get_environ()
        req = Request(environ=env)


        sally_wf = LabbookWorkflow.import_from_remote(test_user_wf.remote, 'sally', config_file=mock_config_file[0])
        sally_lb = sally_wf.labbook
        FileOperations.makedir(sally_lb, relative_path='code/sally-dir', create_activity_record=True)
        sally_wf.sync('sally')

        sync_query = """
        mutation x {
            syncLabbook(input: {
                labbookName: "labbook1",
                owner: "default"
            }) {
                jobKey
            }
        }
        """
        r = mock_create_labbooks_no_lfs[2].execute(sync_query, context_value=req)

        assert 'errors' not in r
        # TODO - Pause and wait for job to report finished
 
    @patch('gtmcore.workflows.gitworkflows_utils.create_remote_gitlab_repo', new=_MOCK_create_remote_repo2)
    def test_reset_branch_to_remote(self, fixture_working_dir, mock_create_labbooks_no_lfs):

        # Mock the request context so a fake authorization header is present
        builder = EnvironBuilder(path='/labbook', method='POST', headers={'Authorization': 'Bearer AJDFHASD'})
        env = builder.get_environ()
        req = Request(environ=env)

        im = InventoryManager(mock_create_labbooks_no_lfs[0])
        test_user_lb = im.load_labbook('default', 'default', 'labbook1')
        wf = LabbookWorkflow(test_user_lb)
        wf.publish(username='default')
        hash_original = wf.labbook.git.commit_hash

        new_file_path = os.path.join(wf.labbook.root_dir, 'input', 'new-file')
        with open(new_file_path, 'w') as f: f.write('File data')
        wf.labbook.sweep_uncommitted_changes()
        hash_before_reset = wf.labbook.git.commit_hash

        publish_query = f"""
        mutation c {{
            resetBranchToRemote(input: {{
                labbookName: "labbook1",
                owner: "default"
            }}) {{
                labbook {{
                    activeBranchName
                }}
            }}
        }}
        """

        r = mock_create_labbooks_no_lfs[2].execute(publish_query, context_value=req)
        assert 'errors' not in r
        assert wf.labbook.git.commit_hash == hash_original
        #hash_after_reset = r['data']['resetBranchToRemote']['labbook']['activeBranch']['commit']['shortHash']
        #assert hash_after_reset not in hash_before_reset
        #assert hash_after_reset in hash_original
