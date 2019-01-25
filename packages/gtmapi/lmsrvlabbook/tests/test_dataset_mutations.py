import pytest
import os

from snapshottest import snapshot
from lmsrvlabbook.tests.fixtures import fixture_working_dir_env_repo_scoped, fixture_working_dir

from gtmcore.inventory.inventory import InventoryManager

from gtmcore.fixtures.datasets import mock_dataset_with_cache_dir, mock_dataset_with_manifest, helper_append_file

from gtmcore.fixtures import _MOCK_create_remote_repo2


class TestDatasetMutations(object):
    def test_create_dataset(self, fixture_working_dir, snapshot):
        query = """
        mutation myCreateDataset($name: String!, $desc: String!, $storage_type: String!) {
          createDataset(input: {name: $name, description: $desc,
                                storageType: $storage_type}) {
            dataset {
              id
              name
              description
              schemaVersion
              datasetType{
                name
                id
                description
              }
            }
          }
        }
        """
        variables = {"name": "test-dataset-1", "desc": "my test dataset",
                     "storage_type": "gigantum_object_v1"}

        snapshot.assert_match(fixture_working_dir[2].execute(query, variable_values=variables))

        # Get Dataset you just created
        query = """{
            dataset(name: "test-dataset-1", owner: "default")  {
                  id
                  name
                  description
                  schemaVersion
                  datasetType{
                    name
                    id
                    description
                  }
                }
                }
        """
        snapshot.assert_match(fixture_working_dir[2].execute(query))

    def test_fetch_dataset_edge(self, fixture_working_dir):
        """Test export"""
        create_query = """
                mutation myCreateDataset($name: String!, $desc: String!, $storage_type: String!) {
                  createDataset(input: {name: $name, description: $desc,
                                        storageType: $storage_type}) {
                    dataset {
                      id
                      name
                    }
                  }
                }
                """
        create_variables = {"name": "test-dataset-2", "desc": "my test dataset",
                            "storage_type": "gigantum_object_v1"}

        result = fixture_working_dir[2].execute(create_query, variable_values=create_variables)
        assert "errors" not in result

        query = """
                mutation myMutation($owner: String!, $datasetName: String!) {
                  fetchDatasetEdge(input: {owner: $owner, datasetName: $datasetName}) {
                      newDatasetEdge {
                        node {
                          id
                          name
                        }
                      }
                  }
                }
                """
        variables = {"datasetName": "test-dataset-2", "owner": "default"}
        result = fixture_working_dir[2].execute(query, variable_values=variables)
        assert "errors" not in result
        assert "test-dataset-2" == result['data']['fetchDatasetEdge']['newDatasetEdge']['node']['name']

    def test_modify_dataset_link(self, fixture_working_dir, snapshot):
        im = InventoryManager(fixture_working_dir[0])
        lb = im.create_labbook('default', 'default', 'test-lb', 'testing dataset links')
        ds = im.create_dataset('default', 'default', "dataset100", storage_type="gigantum_object_v1", description="100")

        # Fake publish to a local bare repo
        _MOCK_create_remote_repo2(ds, 'default', None, None)

        assert os.path.exists(os.path.join(lb.root_dir, '.gitmodules')) is False

        query = """
                   mutation myMutation($lo: String!, $ln: String!, $do: String!, $dn: String!,
                                       $a: String!, $du: String) {
                     modifyDatasetLink(input: {labbookOwner: $lo, labbookName: $ln, datasetOwner: $do, datasetName: $dn,
                                               action: $a, datasetUrl: $du}) {
                         newLabbookEdge {
                           node {
                             id
                             name
                             description
                             linkedDatasets {
                               name
                             }
                           }
                         }
                     }
                   }
                   """
        variables = {"lo": "default", "ln": "test-lb", "do": "default", "dn": "dataset100", "a": "link", "du": ds.remote}
        result = fixture_working_dir[2].execute(query, variable_values=variables)
        assert "errors" not in result
        snapshot.assert_match(result)

        assert os.path.exists(os.path.join(lb.root_dir, '.gitmodules')) is True
        dataset_submodule_dir = os.path.join(lb.root_dir, '.gigantum', 'datasets', 'default', 'dataset100')
        assert os.path.exists(dataset_submodule_dir) is True
        assert os.path.exists(os.path.join(dataset_submodule_dir, '.gigantum')) is True

        with open(os.path.join(lb.root_dir, '.gitmodules'), 'rt') as mf:
            data = mf.read()

        assert len(data) > 0

        query = """
                   mutation myMutation($lo: String!, $ln: String!, $do: String!, $dn: String!,
                                       $a: String!) {
                     modifyDatasetLink(input: {labbookOwner: $lo, labbookName: $ln, datasetOwner: $do, datasetName: $dn,
                                               action: $a}) {
                         newLabbookEdge {
                           node {
                             id
                             name
                             description
                             linkedDatasets {
                               name
                             }
                           }
                         }
                     }
                   }
                   """
        variables = {"lo": "default", "ln": "test-lb", "do": "default", "dn": "dataset100", "a": "unlink"}
        result = fixture_working_dir[2].execute(query, variable_values=variables)
        assert "errors" not in result
        snapshot.assert_match(result)

        dataset_submodule_dir = os.path.join(lb.root_dir, '.gigantum', 'datasets', 'default', 'dataset100')
        assert os.path.exists(dataset_submodule_dir) is False
        assert os.path.exists(os.path.join(dataset_submodule_dir, '.gigantum')) is False
        with open(os.path.join(lb.root_dir, '.gitmodules'), 'rt') as mf:
            data = mf.read()

        assert len(data) == 0

    def test_modify_dataset_link_errors(self, fixture_working_dir, snapshot):
        im = InventoryManager(fixture_working_dir[0])
        lb = im.create_labbook('default', 'default', 'test-lb', 'testing dataset links')
        ds = im.create_dataset('default', 'default', "dataset100", storage_type="gigantum_object_v1",
                               description="100")
        # Fake publish to a local bare repo
        _MOCK_create_remote_repo2(ds, 'default', None, None)

        query = """
                   mutation myMutation($lo: String!, $ln: String!, $do: String!, $dn: String!,
                                       $a: String!, $du: String) {
                     modifyDatasetLink(input: {labbookOwner: $lo, labbookName: $ln, datasetOwner: $do, datasetName: $dn,
                                               action: $a, datasetUrl: $du}) {
                         newLabbookEdge {
                           node {
                             id
                             name
                             description
                             linkedDatasets {
                               name
                             }
                           }
                         }
                     }
                   }
                   """
        variables = {"lo": "default", "ln": "test-lb", "do": "default", "dn": "dataset100", "a": "asdfasdf",
                     "du": ds.remote}
        result = fixture_working_dir[2].execute(query, variable_values=variables)
        assert "errors" in result
        snapshot.assert_match(result)

        query = """
                   mutation myMutation($lo: String!, $ln: String!, $do: String!, $dn: String!,
                                       $a: String!) {
                     modifyDatasetLink(input: {labbookOwner: $lo, labbookName: $ln, datasetOwner: $do, datasetName: $dn,
                                               action: $a}) {
                         newLabbookEdge {
                           node {
                             id
                             name
                             description
                             linkedDatasets {
                               name
                             }
                           }
                         }
                     }
                   }
                   """
        variables = {"lo": "default", "ln": "test-lb", "do": "default", "dn": "dataset100", "a": "link"}
        result = fixture_working_dir[2].execute(query, variable_values=variables)
        assert "errors" in result
        snapshot.assert_match(result)
