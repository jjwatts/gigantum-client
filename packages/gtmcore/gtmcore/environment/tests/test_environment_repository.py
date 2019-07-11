import pytest

from gtmcore.environment import BaseRepository
from gtmcore.fixtures import (mock_config_with_repo, ENV_UNIT_TEST_REPO, ENV_UNIT_TEST_BASE, ENV_UNIT_TEST_REV)

from gtmcore.environment.tests import ENV_SKIP_MSG, ENV_SKIP_TEST


@pytest.mark.skipif(ENV_SKIP_TEST, reason=ENV_SKIP_MSG)
class TestEnvironmentRepository(object):
    def test_get_list_index_base_image(self, mock_config_with_repo):
        """Test accessing the list version of the index"""

        repo = BaseRepository(mock_config_with_repo[0])
        data = repo.get_base_list()

        assert type(data) == list
        assert len(data) == 5

        assert any(n.get('id') == ENV_UNIT_TEST_BASE for n in data)
        assert any(n.get('repository') == ENV_UNIT_TEST_REPO for n in data)

    def test_get_component_index_base(self, mock_config_with_repo):
        """Test accessing the detail version of the index"""
        repo = BaseRepository(mock_config_with_repo[0])
        data = repo.get_base_versions(ENV_UNIT_TEST_REPO,
                                      ENV_UNIT_TEST_BASE)
        assert type(data) == list
        assert len(data) >= 1
        assert data[-1][1]['id'] == ENV_UNIT_TEST_BASE
        assert data[-1][1]['repository'] == ENV_UNIT_TEST_REPO

    def test_get_component_version_base(self, mock_config_with_repo):
        """Test accessing the a single version of the index"""
        repo = BaseRepository(mock_config_with_repo[0])
        data = repo.get_base(ENV_UNIT_TEST_REPO,
                             ENV_UNIT_TEST_BASE,
                             ENV_UNIT_TEST_REV)

        assert type(data) == dict
        assert data['id'] == ENV_UNIT_TEST_BASE
        assert data['revision'] == ENV_UNIT_TEST_REV
        assert 'image' in data
        assert len(data['package_managers']) == 2
        assert data['repository'] == ENV_UNIT_TEST_REPO

    def test_get_component_version_base_does_not_exist(self, mock_config_with_repo):
        """Test accessing the a single version of the index that does not exist"""
        repo = BaseRepository(mock_config_with_repo[0])
        with pytest.raises(ValueError):
            repo.get_base('gig-dev_environment-componentsXXX',
                               'quickstart-jupyterlab', '0.1')
        with pytest.raises(ValueError):
            repo.get_base(ENV_UNIT_TEST_REPO,
                               'quickstart-jupyterlab', '3')
        with pytest.raises(ValueError):
            repo.get_base(ENV_UNIT_TEST_REPO,
                               'quickstart-jupyterlabXXX', 0)
        with pytest.raises(ValueError):
            repo.get_base(ENV_UNIT_TEST_REPO,
                               'quickstart-jupyterlab', 99)
