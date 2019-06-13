import responses

from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from lmsrvlabbook.tests.fixtures import fixture_working_dir

import pytest
from gtmcore.inventory.inventory import InventoryManager


@pytest.fixture()
def mock_create_dataset(fixture_working_dir):
    # Create a labbook in the temporary directory
    im = InventoryManager(fixture_working_dir[0])
    im.create_dataset("default", "default", "dataset1",
                      storage_type="gigantum_object_v1", description="Test labbook 1")

    responses.add(responses.GET, 'https://usersrv.gigantum.io/key',
                  json={'key': 'afaketoken'}, status=200)
    responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/projects?search=dataset1',
                  json=[{
                          "id": 22,
                          "description": "",
                        }],
                  status=200, match_querystring=True)

    yield fixture_working_dir


class TestDatasetCollaboratorMutations(object):
    @responses.activate
    def test_add_collaborator(self, mock_create_dataset):
        """Test adding a collaborator to a dataset"""
        # Setup REST mocks
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/users?username=person100',
                      json=[
                                {
                                    "id": 100,
                                    "name": "New Person",
                                    "username": "person100",
                                    "state": "active",
                                    "access_level": 30
                                }
                            ],
                      status=200)
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1/members',
                      json=[
                                {
                                    "id": 29,
                                    "name": "Default User",
                                    "username": "default",
                                    "access_level": 40,
                                    "expires_at": None
                                }
                            ],
                      status=200)
        responses.add(responses.POST, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1/members',
                      json={
                                "id": 100,
                                "name": "New Person",
                                "username": "person100",
                                "state": "active",
                            },
                      status=201)
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1',
                      json=[{
                              "id": 27,
                              "description": "",
                            }],
                      status=200)
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1/members',
                      json=[
                                {
                                    "id": 29,
                                    "name": "Jane Doe",
                                    "username": "default",
                                    "access_level": 40,
                                    "expires_at": None
                                },
                                {
                                    "id": 100,
                                    "name": "New Person",
                                    "username": "person100",
                                    "access_level": 30,
                                    "expires_at": None
                                }
                            ],
                      status=200)

        # Mock the request context so a fake authorization header is present
        builder = EnvironBuilder(path='/labbook', method='POST', headers={'Authorization': 'Bearer AJDFHASD'})
        env = builder.get_environ()
        req = Request(environ=env)

        query = """
        mutation AddCollaborator {
          addDatasetCollaborator(
            input: {
              owner: "default",
              datasetName: "dataset1",
              username: "person100"
              permissions: "readwrite"
            }) {
              updatedDataset {
                collaborators {
                    collaboratorUsername
                    permission
                }
                canManageCollaborators
              }
            }
        }
        """
        r = mock_create_dataset[2].execute(query, context_value=req)
        assert 'errors' not in r
        assert r['data']['addDatasetCollaborator']['updatedDataset']['collaborators'][0]['collaboratorUsername'] == 'default'
        assert r['data']['addDatasetCollaborator']['updatedDataset']['collaborators'][0]['permission'] == 'OWNER'
        assert r['data']['addDatasetCollaborator']['updatedDataset']['collaborators'][1]['collaboratorUsername'] == 'person100'
        assert r['data']['addDatasetCollaborator']['updatedDataset']['collaborators'][1]['permission'] == 'READ_WRITE'
        assert r['data']['addDatasetCollaborator']['updatedDataset']['canManageCollaborators'] is True

    @responses.activate
    def test_add_collaborator_as_owner(self, mock_create_dataset):
        """Test adding a collaborator to a LabBook"""
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/users?username=person100',
                      json=[
                                {
                                    "id": 100,
                                    "name": "New Person",
                                    "username": "person100",
                                    "state": "active",
                                    "access_level": 30
                                }
                            ],
                      status=200)
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1/members',
                      json=[
                                {
                                    "id": 29,
                                    "name": "Default User",
                                    "username": "default",
                                    "access_level": 40,
                                    "expires_at": None
                                }
                            ],
                      status=200)
        responses.add(responses.POST, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1/members',
                      json={
                                "id": 100,
                                "name": "New Person",
                                "username": "person100",
                                "state": "active",
                            },
                      status=201)
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1',
                      json=[{
                              "id": 27,
                              "description": "",
                            }],
                      status=200)
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1/members',
                      json=[
                                {
                                    "id": 29,
                                    "name": "Jane Doe",
                                    "username": "default",
                                    "access_level": 40,
                                    "expires_at": None
                                },
                                {
                                    "id": 100,
                                    "name": "New Person",
                                    "username": "person100",
                                    "access_level": 40,
                                    "expires_at": None
                                }
                            ],
                      status=200)

        # Mock the request context so a fake authorization header is present
        builder = EnvironBuilder(path='/labbook', method='POST', headers={'Authorization': 'Bearer AJDFHASD'})
        env = builder.get_environ()
        req = Request(environ=env)

        query = """
        mutation AddCollaborator {
          addDatasetCollaborator(
            input: {
              owner: "default",
              datasetName: "dataset1",
              username: "person100"
              permissions: "owner"
            }) {
              updatedDataset {
                collaborators {
                    collaboratorUsername
                    permission
                }
                canManageCollaborators
              }
            }
        }
        """
        r = mock_create_dataset[2].execute(query, context_value=req)
        assert 'errors' not in r
        assert r['data']['addDatasetCollaborator']['updatedDataset']['collaborators'][0]['collaboratorUsername'] == 'default'
        assert r['data']['addDatasetCollaborator']['updatedDataset']['collaborators'][0]['permission'] == 'OWNER'
        assert r['data']['addDatasetCollaborator']['updatedDataset']['collaborators'][1]['collaboratorUsername'] == 'person100'
        assert r['data']['addDatasetCollaborator']['updatedDataset']['collaborators'][1]['permission'] == 'OWNER'
        assert r['data']['addDatasetCollaborator']['updatedDataset']['canManageCollaborators'] is True

    @responses.activate
    def test_delete_collaborator(self, mock_create_dataset):
        """Test deleting a collaborator from a LabBook"""
        # Setup REST mocks
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/users?username=person100',
                      json=[
                                {
                                    "id": 100,
                                    "name": "New Person",
                                    "username": "person100",
                                    "state": "active",
                                }
                            ],
                      status=200)
        responses.add(responses.DELETE, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1/members/100',
                      status=204)
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1',
                      json=[{
                              "id": 27,
                              "description": "",
                            }],
                      status=200)
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1/members',
                      json=[
                                {
                                    "id": 29,
                                    "name": "Default User",
                                    "username": "default",
                                    "access_level": 40,
                                    "expires_at": None
                                }
                            ],
                      status=200)

        # Mock the request context so a fake authorization header is present
        builder = EnvironBuilder(path='/labbook', method='DELETE', headers={'Authorization': 'Bearer AJDFHASD'})
        env = builder.get_environ()
        req = Request(environ=env)

        query = """
        mutation DeleteCollaborator {
          deleteDatasetCollaborator(
            input: {
              owner: "default",
              datasetName: "dataset1",
              username: "person100"
            }) {
              updatedDataset {
                collaborators {
                    collaboratorUsername
                }
              }
            }
        }
        """
        r = mock_create_dataset[2].execute(query, context_value=req)
        assert 'errors' not in r
        assert r['data']['deleteDatasetCollaborator']['updatedDataset']['collaborators'][0]['collaboratorUsername'] == 'default'

    @responses.activate
    def test_change_collaborator_permissions(self, mock_create_dataset):
        """Test adding a collaborator to a dataset"""
        # Setup REST mocks
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/users?username=person100',
                      json=[
                                {
                                    "id": 100,
                                    "name": "New Person",
                                    "username": "person100",
                                    "state": "active",
                                    "access_level": 30
                                }
                            ],
                      status=200)
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1/members',
                      json=[
                              {
                                  "id": 29,
                                  "name": "Jane Doe",
                                  "username": "default",
                                  "access_level": 40,
                                  "expires_at": None
                              },
                              {
                                  "id": 100,
                                  "name": "New Person",
                                  "username": "person100",
                                  "access_level": 30,
                                  "expires_at": None
                              }
                            ],
                      status=200)
        responses.add(responses.DELETE, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1/members/100',
                      status=204)
        responses.add(responses.POST, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1/members',
                      json={
                                "id": 100,
                                "name": "New Person",
                                "username": "person100",
                                "state": "active",
                            },
                      status=201)
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1',
                      json=[{
                              "id": 27,
                              "description": "",
                            }],
                      status=200)
        responses.add(responses.GET, 'https://repo.gigantum.io/api/v4/projects/default%2Fdataset1/members',
                      json=[
                                {
                                    "id": 29,
                                    "name": "Jane Doe",
                                    "username": "default",
                                    "access_level": 40,
                                    "expires_at": None
                                },
                                {
                                    "id": 100,
                                    "name": "New Person",
                                    "username": "person100",
                                    "access_level": 20,
                                    "expires_at": None
                                }
                            ],
                      status=200)

        # Mock the request context so a fake authorization header is present
        builder = EnvironBuilder(path='/labbook', method='POST', headers={'Authorization': 'Bearer AJDFHASD'})
        env = builder.get_environ()
        req = Request(environ=env)

        query = """
        mutation AddCollaborator {
          addDatasetCollaborator(
            input: {
              owner: "default",
              datasetName: "dataset1",
              username: "person100"
              permissions: "readonly"
            }) {
              updatedDataset {
                collaborators {
                    collaboratorUsername
                    permission
                }
                canManageCollaborators
              }
            }
        }
        """
        r = mock_create_dataset[2].execute(query, context_value=req)
        assert 'errors' not in r
        assert r['data']['addDatasetCollaborator']['updatedDataset']['collaborators'][0]['collaboratorUsername'] == 'default'
        assert r['data']['addDatasetCollaborator']['updatedDataset']['collaborators'][0]['permission'] == 'OWNER'
        assert r['data']['addDatasetCollaborator']['updatedDataset']['collaborators'][1]['collaboratorUsername'] == 'person100'
        assert r['data']['addDatasetCollaborator']['updatedDataset']['collaborators'][1]['permission'] == 'READ_ONLY'
