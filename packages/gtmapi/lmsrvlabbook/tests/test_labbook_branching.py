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
import pytest
import shutil
import flask
from flask import Flask
import graphene
import pprint
from graphene.test import Client
from mock import patch

from gtmcore.auth.identity import get_identity_manager
from gtmcore.configuration import Configuration
from gtmcore.inventory.branching import BranchManager
from gtmcore.inventory.inventory import InventoryManager

from gtmcore.files import FileOperations

from lmsrvcore.middleware import DataloaderMiddleware, error_middleware
from lmsrvlabbook.tests.fixtures import ContextMock, fixture_working_dir, _create_temp_work_dir
from lmsrvlabbook.api.query import LabbookQuery
from lmsrvlabbook.api.mutation import LabbookMutations

UT_USERNAME = "default"
UT_LBNAME = "unittest-workflow-branch-1"


@pytest.fixture()
def mock_create_labbooks(fixture_working_dir):
    # Create a labbook in the temporary directory
    config_file = fixture_working_dir[0]
    im = InventoryManager(fixture_working_dir[0])
    lb = im.create_labbook(UT_USERNAME, UT_USERNAME, UT_LBNAME, description="Cats labbook 1")

    # Create a file in the dir
    with open(os.path.join(fixture_working_dir[1], 'unittest-examplefile'), 'w') as sf:
        sf.write("test data")
        sf.seek(0)
    FileOperations.insert_file(lb, 'code', sf.name)

    assert os.path.isfile(os.path.join(lb.root_dir, 'code', 'unittest-examplefile'))

    # Create test client
    schema = graphene.Schema(query=LabbookQuery, mutation=LabbookMutations)
    with patch.object(Configuration, 'find_default_config', lambda self: config_file):
        app = Flask("lmsrvlabbook")
        app.config["LABMGR_CONFIG"] = Configuration()
        app.config["LABMGR_ID_MGR"] = get_identity_manager(Configuration())
        with app.app_context():
            flask.g.user_obj = app.config["LABMGR_ID_MGR"].get_user_profile()
            client = Client(schema, middleware=[DataloaderMiddleware(), error_middleware],
                            context_value=ContextMock())
            yield lb, client, schema
    shutil.rmtree(fixture_working_dir, ignore_errors=True)


class TestWorkflowsBranching(object):
    def test_active_branch_name(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        bm = BranchManager(lb, username=UT_USERNAME)

        q = f"""
        {{
            labbook(name: "{UT_LBNAME}", owner: "{UT_USERNAME}") {{
                activeBranchName
                workspaceBranchName
            }}
        }}
        """
        r = client.execute(q)
        assert 'errors' not in r
        assert r['data']['labbook']['activeBranchName'] == bm.active_branch
        assert r['data']['labbook']['workspaceBranchName'] == bm.workspace_branch

    def test_available_branches(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        bm = BranchManager(lb, username=UT_USERNAME)

        q = f"""
        {{
            labbook(name: "{UT_LBNAME}", owner: "{UT_USERNAME}") {{
                branches {{
                    branchName
                    isLocal
                    isRemote
                    isActive
                }}
            }}
        }}
        """
        r = client.execute(q)
        pprint.pprint(r)
        assert 'errors' not in r
        assert len(r['data']['labbook']['branches']) == 1
        assert r['data']['labbook']['branches'][0]['branchName'] == bm.workspace_branch
        assert r['data']['labbook']['branches'][0]['isLocal'] == True, "Should be local"
        assert r['data']['labbook']['branches'][0]['isRemote'] == False, "There should be no remote branches"
        assert r['data']['labbook']['branches'][0]['isActive'] == True

    def test_query_mergeable_branches_from_main(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        bm = BranchManager(lb, username=UT_USERNAME)
        b1 = bm.create_branch(f"tester1")
        bm.workon_branch(bm.workspace_branch)
        b2 = bm.create_branch(f"tester2")
        bm.workon_branch(bm.workspace_branch)
        assert bm.active_branch == bm.workspace_branch

        q = f"""
        {{
            labbook(name: "{UT_LBNAME}", owner: "{UT_USERNAME}") {{
                branches {{
                    branchName
                    isMergeable
                }}
            }}
        }}
        """
        r = client.execute(q)
        assert 'errors' not in r
        assert len(r['data']['labbook']['branches']) == 3
        assert r['data']['labbook']['branches'][0]['branchName'] == 'master'
        assert r['data']['labbook']['branches'][0]['isMergeable'] == False
        assert r['data']['labbook']['branches'][1]['branchName'] == 'tester1'
        assert r['data']['labbook']['branches'][1]['isMergeable'] == True
        assert r['data']['labbook']['branches'][2]['branchName'] == 'tester2'
        assert r['data']['labbook']['branches'][2]['isMergeable'] == True

    def test_query_mergeable_branches_from_feature_branch(self, mock_create_labbooks):
        # Per current branch model, can only merge in workspace branch
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        bm = BranchManager(lb, username=UT_USERNAME)
        b1 = bm.create_branch(f"tester1")
        bm.workon_branch(bm.workspace_branch)
        b2 = bm.create_branch(f"tester2")

        q = f"""
        {{
            labbook(name: "{UT_LBNAME}", owner: "{UT_USERNAME}") {{
                workspaceBranchName
                branches {{
                    branchName
                    isMergeable
                }}
            }}
        }}
        """
        r = client.execute(q)
        assert 'errors' not in r
        assert r['data']['labbook']['workspaceBranchName'] == bm.workspace_branch
        branches = r['data']['labbook']['branches']
        assert branches[0]['branchName'] == 'master'
        assert branches[0]['isMergeable'] is True
        assert branches[1]['branchName'] == 'tester1'
        assert branches[1]['isMergeable'] is True
        assert branches[2]['branchName'] == 'tester2'
        assert branches[2]['isMergeable'] is False


    def test_create_feature_branch_bad_name_fail(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        bm = BranchManager(lb, username=UT_USERNAME)
        bad_branch_names = ['', '_', 'Über-bad', 'xxx-xxx' * 40, 'cats_99', 'bad-', '-', '-bad', 'bad--bad',
                            'bad---bad--bad-bad', 'Nope', 'Nope99', 'Nope-99', 'N&PE', 'n*ope', 'no;way', 'no:way',
                            '<nope>-not-a-branch', 'Robert") DROP TABLE Students; --', "no way not a branch",
                            ''.join(chr(x) for x in range(0, 78)), ''.join(chr(x) for x in range(0, 255)),
                            chr(0) * 10, chr(0) * 10000]

        for bad_name in bad_branch_names:
            q = f"""
            mutation makeFeatureBranch {{
                createExperimentalBranch(input: {{
                    owner: "{UT_USERNAME}",
                    labbookName: "{UT_LBNAME}",
                    branchName: "{bad_name}"
                }}) {{
                    newBranchName
                }}
            }}
            """
            r = client.execute(q)
            pprint.pprint(r)
            assert 'errors' in r
            assert bm.active_branch == bm.workspace_branch
            assert lb.is_repo_clean

    def test_create_feature_branch_from_feature_branch_fail(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        bm = BranchManager(lb, username=UT_USERNAME)
        b1 = bm.create_branch(f"tester1")

        q = f"""
        mutation makeFeatureBranch {{
            createExperimentalBranch(input: {{
                owner: "{UT_USERNAME}",
                labbookName: "{UT_LBNAME}",
                branchName: "valid-branch-name"
            }}) {{
                newBranchName
            }}
        }}
        """
        r = client.execute(q)
        pprint.pprint(r)
        assert 'errors' in r
        assert bm.active_branch == b1
        assert lb.is_repo_clean

    def test_create_feature_branch_success(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        bm = BranchManager(lb, username=UT_USERNAME)
        b1 = bm.create_branch(f"tester1")
        bm.workon_branch(bm.workspace_branch)

        q = f"""
        mutation makeFeatureBranch {{
            createExperimentalBranch(input: {{
                owner: "{UT_USERNAME}",
                labbookName: "{UT_LBNAME}",
                branchName: "valid-branch-name-working1"
            }}) {{
                labbook{{
                    name
                    activeBranchName
                    branches {{
                        branchName
                    }}
                }}
            }}
        }}
        """
        r = client.execute(q)
        assert 'errors' not in r
        assert r['data']['createExperimentalBranch']['labbook']['activeBranchName'] \
            == 'valid-branch-name-working1'
        assert set([n['branchName'] for n in r['data']['createExperimentalBranch']['labbook']['branches']]) \
            == set(['tester1', 'master', 'valid-branch-name-working1'])

        assert lb.active_branch == 'valid-branch-name-working1'
        assert lb.is_repo_clean

    def test_create_feature_branch_success_update_description(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        bm = BranchManager(lb, username=UT_USERNAME)
        b1 = bm.create_branch(f"tester1")
        bm.workon_branch(bm.workspace_branch)

        q = f"""
        mutation makeFeatureBranch {{
            createExperimentalBranch(input: {{
                owner: "{UT_USERNAME}",
                labbookName: "{UT_LBNAME}",
                branchName: "valid-branch-name-working1"
                description: "Updated description"
            }}) {{
                labbook{{
                    name
                    description
                    branches {{
                        branchName
                    }}
                    activeBranchName
                }}
            }}
        }}
        """
        r = client.execute(q)
        assert 'errors' not in r
        assert r['data']['createExperimentalBranch']['labbook']['activeBranchName'] \
               == 'valid-branch-name-working1'
        assert r['data']['createExperimentalBranch']['labbook']['description'] \
               == "Updated description"

        assert bm.active_branch == 'valid-branch-name-working1'
        assert lb.is_repo_clean

        # Make sure activity record was created when description was changed
        log_data = lb.git.log()
        assert "_GTM_ACTIVITY_START_**\nmsg:Updated description of Project" in log_data[0]['message']

    def test_delete_feature_branch_fail(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        bm = BranchManager(lb, username=UT_USERNAME)
        b1 = bm.create_branch(f"tester1")

        q = f"""
        mutation makeFeatureBranch {{
            deleteExperimentalBranch(input: {{
                owner: "{UT_USERNAME}",
                labbookName: "{UT_LBNAME}",
                branchName: "{b1}",
                deleteLocal: true
            }}) {{
                success
            }}
        }}
        """
        r = client.execute(q)
        pprint.pprint(r)
        # Cannot delete branch when it's the currently active branch
        assert 'errors' in r
        assert bm.active_branch == b1
        assert lb.is_repo_clean

    def test_delete_feature_branch_success(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        bm = BranchManager(lb, username=UT_USERNAME)
        b1 = bm.create_branch(f"tester1")
        bm.workon_branch(bm.workspace_branch)

        q = f"""
        mutation makeFeatureBranch {{
            deleteExperimentalBranch(input: {{
                owner: "{UT_USERNAME}",
                labbookName: "{UT_LBNAME}",
                branchName: "{b1}",
                deleteLocal: true
            }}) {{
                labbook {{
                    branches {{
                        branchName
                    }}
                }}
            }}
        }}
        """
        r = client.execute(q)
        pprint.pprint(r)
        # Cannot delete branch when it's the currently active branch
        assert 'errors' not in r
        assert bm.active_branch == bm.workspace_branch
        assert lb.is_repo_clean
        assert b1 not in bm.branches_local

    def test_workon_feature_branch_bad_name_fail(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        bm = BranchManager(lb, username=UT_USERNAME)
        b1 = bm.create_branch(f"tester1")
        bm.workon_branch(bm.workspace_branch)

        q = f"""
        mutation makeFeatureBranch {{
            workonExperimentalBranch(input: {{
                owner: "{UT_USERNAME}",
                labbookName: "{UT_LBNAME}",
                branchName: "{b1.replace('gm', '')}"
            }}) {{
                currentBranchName
            }}
        }}
        """
        r = client.execute(q)
        pprint.pprint(r)
        # Cannot delete branch when it's the currently active branch
        assert 'errors' in r
        assert bm.active_branch == bm.workspace_branch
        assert lb.is_repo_clean

    def test_workon_feature_branch_success(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        bm = BranchManager(lb, username=UT_USERNAME)
        b1 = bm.create_branch(f"tester1")
        bm.workon_branch(bm.workspace_branch)

        assert bm.active_branch == 'master'

        q = f"""
        mutation makeFeatureBranch {{
            workonExperimentalBranch(input: {{
                owner: "{UT_USERNAME}",
                labbookName: "{UT_LBNAME}",
                branchName: "{b1}"
            }}) {{
                labbook{{
                    name
                    description
                    branches {{
                        branchName
                    }}
                    activeBranchName
                }}
            }}
        }}
        """
        r = client.execute(q)
        assert 'errors' not in r
        assert r['data']['workonExperimentalBranch']['labbook']['activeBranchName'] \
               == 'tester1'
        ab = r['data']['workonExperimentalBranch']['labbook']['branches']
        assert set([n['branchName'] for n in ab]) \
            == set(['master', 'tester1'])
        assert bm.active_branch == 'tester1'
        assert lb.is_repo_clean

    def test_merge_into_workspace_from_simple_success(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        bm = BranchManager(lb, username=UT_USERNAME)
        og_hash = lb.git.commit_hash
        b1 = bm.create_branch(f"test-branch")
        FileOperations.makedir(lb, 'code/sillydir1', create_activity_record=True)
        FileOperations.makedir(lb, 'code/sillydir2', create_activity_record=True)
        branch_hash = lb.git.commit_hash

        assert og_hash != branch_hash

        bm.workon_branch(bm.workspace_branch)
        assert lb.git.log()[0]['commit'] == og_hash
        assert not os.path.exists(os.path.join(lb.root_dir, 'code/sillydir1'))

        merge_q = f"""
        mutation x {{
            mergeFromBranch(input: {{
                owner: "{UT_USERNAME}",
                labbookName: "{UT_LBNAME}",
                otherBranchName: "{b1}"
            }}) {{
                labbook{{
                    name
                    description
                    activeBranchName
                }}
            }}
        }}
        """
        r = client.execute(merge_q)
        assert 'errors' not in r
        assert r['data']['mergeFromBranch']['labbook']['activeBranchName'] \
               == 'master'

        assert lb.active_branch == bm.workspace_branch
        assert os.path.exists(os.path.join(lb.root_dir, 'code/sillydir1'))
        assert lb.is_repo_clean

    def test_merge_into_feature_from_workspace_simple_success(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        bm = BranchManager(lb, username=UT_USERNAME)
        og_hash = lb.git.commit_hash
        b1 = bm.create_branch(f"test-branch")
        bm.workon_branch(bm.workspace_branch)
        assert lb.active_branch == bm.workspace_branch
        og2_hash = lb.git.commit_hash
        assert lb.git.commit_hash == og_hash

        FileOperations.makedir(lb, 'code/main-branch-dir1', create_activity_record=True)
        FileOperations.makedir(lb, 'code/main-branch-dir2', create_activity_record=True)
        next_main_hash = lb.git.commit_hash
        assert og_hash != next_main_hash

        bm.workon_branch(b1)
        assert not os.path.exists(os.path.join(lb.root_dir, 'code/main-branch-dir1'))

        merge_q = f"""
        mutation x {{
            mergeFromBranch(input: {{
                owner: "{UT_USERNAME}",
                labbookName: "{UT_LBNAME}",
                otherBranchName: "{bm.workspace_branch}"
            }}) {{
                labbook{{
                    name
                    description
                    activeBranchName
                }}
            }}
        }}
        """
        r = client.execute(merge_q)
        assert 'errors' not in r
        assert r['data']['mergeFromBranch']['labbook']['activeBranchName'] == 'test-branch'
        assert r['data']['mergeFromBranch']['labbook']['name'] == 'unittest-workflow-branch-1'

        assert lb.active_branch == b1
        assert os.path.exists(os.path.join(lb.root_dir, 'code/main-branch-dir1'))
        assert lb.is_repo_clean

    def test_conflicted_merge_from_no_force_fail(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        with open('/tmp/s1.txt', 'w') as s1:
            s1.write('original-file\ndata')
        FileOperations.insert_file(lb, section='code', src_file=s1.name)
        bm = BranchManager(lb, username=UT_USERNAME)

        nb = bm.create_branch(f'new-branch')
        with open('/tmp/s1.txt', 'w') as s1:
            s1.write('branch-conflict-data')
        FileOperations.insert_file(lb, section='code', src_file=s1.name)

        bm.workon_branch(bm.workspace_branch)
        with open('/tmp/s1.txt', 'w') as s1:
            s1.write('mainline-conflict-data')
        FileOperations.insert_file(lb, section='code', src_file=s1.name)

        merge_q = f"""
        mutation x {{
            mergeFromBranch(input: {{
                owner: "{UT_USERNAME}",
                labbookName: "{UT_LBNAME}",
                otherBranchName: "{nb}"
            }}) {{
                labbook{{
                    name
                    description
                    activeBranchName
                }}
            }}
        }}
        """
        r = client.execute(merge_q)
        assert 'errors' in r
        assert 'Merge conflict' in r['errors'][0]['message']

    def test_conflicted_merge_from_force_success(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        with open('/tmp/s1.txt', 'w') as s1:
            s1.write('original-file\ndata')
        FileOperations.insert_file(lb, section='code', src_file=s1.name)
        bm = BranchManager(lb, username=UT_USERNAME)

        nb = bm.create_branch(f'new-branch')
        with open('/tmp/s1.txt', 'w') as s1:
            s1.write('branch-conflict-data')
        FileOperations.insert_file(lb, section='code', src_file=s1.name)

        bm.workon_branch(bm.workspace_branch)
        with open('/tmp/s1.txt', 'w') as s1:
            s1.write('mainline-conflict-data')
        FileOperations.insert_file(lb, section='code', src_file=s1.name)

        merge_q = f"""
        mutation x {{
            mergeFromBranch(input: {{
                owner: "{UT_USERNAME}",
                labbookName: "{UT_LBNAME}",
                otherBranchName: "{nb}",
                overrideMethod: "theirs"
            }}) {{
                labbook{{
                    name
                    description
                    activeBranchName
                }}
            }}
        }}
        """
        r = client.execute(merge_q)
        assert 'errors' not in r
        assert r['data']['mergeFromBranch']['labbook']['activeBranchName'] == 'master'

    def test_reflect_deleted_files_on_merge_in(self, mock_create_labbooks):
        lb, client = mock_create_labbooks[0], mock_create_labbooks[1]
        with open('/tmp/s1.txt', 'w') as s1:
            s1.write('original-file\ndata')
        FileOperations.insert_file(lb, section='code', src_file=s1.name)
        bm = BranchManager(lb, username=UT_USERNAME)

        nb = bm.create_branch(f'new-branch')
        assert os.path.exists(os.path.join(lb.root_dir, 'code', 's1.txt'))
        FileOperations.delete_files(lb, 'code', ['s1.txt'])
        assert lb.is_repo_clean
        assert not os.path.exists(os.path.join(lb.root_dir, 'code', 's1.txt'))

        bm.workon_branch(bm.workspace_branch)
        assert os.path.exists(os.path.join(lb.root_dir, 'code', 's1.txt'))

        merge_q = f"""
        mutation x {{
            mergeFromBranch(input: {{
                owner: "{UT_USERNAME}",
                labbookName: "{UT_LBNAME}",
                otherBranchName: "{nb}"
            }}) {{
                labbook{{
                    name
                    description
                    activeBranchName
                }}
            }}
        }}
        """
        r = client.execute(merge_q)
        assert 'errors' not in r
        assert r['data']['mergeFromBranch']['labbook']['activeBranchName'] == 'master'
        assert not os.path.exists(os.path.join(lb.root_dir, 'code', 's1.txt'))

