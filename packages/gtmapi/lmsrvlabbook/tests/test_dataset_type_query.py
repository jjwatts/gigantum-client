from snapshottest import snapshot
from lmsrvlabbook.tests.fixtures import fixture_working_dir, mock_enable_unmanaged_for_testing,\
    fixture_working_dir_dataset_tests


class TestDatasetTypesQueries(object):
    def test_get_available_dataset_types(self, fixture_working_dir_dataset_tests, snapshot):
        query = """
                {
                  availableDatasetTypes{
                        id
                        name
                        description
                        isManaged
                        canUpdateUnmanagedFromRemote
                        storageType
                        readme
                        tags
                        icon
                        url
                      }
                }
        """
        snapshot.assert_match(fixture_working_dir_dataset_tests[2].execute(query))
