from pathlib import Path
import pprint
import uuid
import os

import pytest
import yaml

from gtmcore.environment import ComponentManager
from gtmcore.fixtures import mock_config_file, mock_labbook, mock_config_with_repo
from gtmcore.inventory.inventory import InventoryManager
import gtmcore.fixtures

from gtmcore.environment.tests import ENV_SKIP_MSG, ENV_SKIP_TEST


def create_tmp_labbook(cfg_file):
    im = InventoryManager(cfg_file)
    lb = im.create_labbook('unittest', 'unittest',
                           f'unittest-labbook-{str(uuid.uuid4())[:4]}')
    return lb


@pytest.mark.skipif(ENV_SKIP_TEST, reason=ENV_SKIP_MSG)
class TestComponentManager(object):
    def test_initalize_labbook(self, mock_config_with_repo):
        """Test preparing an empty labbook"""

        lb = create_tmp_labbook(mock_config_with_repo[0])
        labbook_dir = lb.root_dir

        pprint.pprint([n[0] for n in os.walk(labbook_dir)])
        # Verify missing dir structure
        assert os.path.exists(os.path.join(labbook_dir, '.gigantum', 'env', 'base')) is True
        assert os.path.exists(os.path.join(labbook_dir, '.gigantum', 'env', 'package_manager')) is True
        assert os.path.exists(os.path.join(labbook_dir, '.gigantum', 'env', 'custom')) is True
        assert os.path.exists(os.path.join(labbook_dir, '.gigantum', 'env', 'entrypoint.sh')) is False

        cm = ComponentManager(lb)

        # Verify dir structure
        assert os.path.exists(os.path.join(labbook_dir, '.gigantum', 'env', 'base')) is True
        assert os.path.exists(os.path.join(labbook_dir, '.gigantum', 'env', 'package_manager')) is True
        assert os.path.exists(os.path.join(labbook_dir, '.gigantum', 'env', 'custom')) is True
        assert os.path.exists(os.path.join(labbook_dir, '.gigantum', 'env', 'entrypoint.sh')) is True

    def test_add_package(self, mock_config_with_repo):
        """Test adding a package such as one from apt-get or pip3. """
        # Create a labook
        lb = create_tmp_labbook(mock_config_with_repo[0])
        labbook_dir = lb.root_dir

        # Create Component Manager
        cm = ComponentManager(lb)

        # Add some sample components
        pkgs = [{"manager": "pip3", "package": "requests", "version": "2.18.2"},
                {"manager": "pip3", "package": "gigantum", "version": "0.5"}]
        cm.add_packages('pip3', pkgs)

        pkgs = [{"manager": "apt", "package": "ack", "version": "1.0"},
                {"manager": "apt", "package": "docker", "version": "3.5"}]
        cm.add_packages('apt', pkgs)

        package_path = os.path.join(lb._root_dir, '.gigantum', 'env', 'package_manager')
        assert os.path.exists(package_path)

        # Ensure all four packages exist.
        package_files = [f for f in os.listdir(package_path)]
        package_files = [p for p in package_files if p != '.gitkeep']
        assert len(package_files) == 4

        # Ensure the fields in each of the 4 packages exist.
        for file in package_files:
            full_path = os.path.join(package_path, file)
            with open(full_path) as package_yaml:
                fields_dict = yaml.safe_load(package_yaml.read())
                for required_field in ['manager', 'package', 'from_base', 'version']:
                    assert required_field in fields_dict.keys()

        # Verify git/activity
        log = lb.git.log()
        print(log)
        assert len(log) == 7
        assert "_GTM_ACTIVITY_START_" in log[0]["message"]
        assert 'Added 2 apt package(s)' in log[0]["message"]
        assert "_GTM_ACTIVITY_START_" in log[2]["message"]
        assert 'Added 2 pip3 package(s)' in log[2]["message"]

    def test_add_duplicate_package(self, mock_config_with_repo):
        """Test adding a duplicate package to a labbook"""

        lb = create_tmp_labbook(mock_config_with_repo[0])
        labbook_dir = lb.root_dir
        cm = ComponentManager(lb)

        # Add a component;
        pkgs = [{"manager": "pip3", "package": "requests", "version": "2.18.2"}]
        cm.add_packages('pip3', pkgs)

        # Verify file
        package_file = os.path.join(labbook_dir,
                                     '.gigantum',
                                     'env',
                                     'package_manager',
                                     'pip3_requests.yaml')
        assert os.path.exists(package_file) is True

        # Add a component
        with pytest.raises(ValueError):
            cm.add_packages('pip3', pkgs)

        # Force add a component
        cm.add_packages('pip3', pkgs, force=True)
        assert os.path.exists(package_file) is True

        with open(package_file, 'rt') as pf:
            data = yaml.safe_load(pf)
            assert data['version'] == '2.18.2'

    def test_add_base(self, mock_config_with_repo):
        """Test adding a base to a labbook"""
        # Create a labook
        lb = create_tmp_labbook(mock_config_with_repo[0])
        labbook_dir = lb.root_dir

        # Create Component Manager
        cm = ComponentManager(lb)

        # Add a component
        cm.add_base(gtmcore.fixtures.ENV_UNIT_TEST_REPO, gtmcore.fixtures.ENV_UNIT_TEST_BASE,
                    gtmcore.fixtures.ENV_UNIT_TEST_REV)

        # Verify file
        component_file = os.path.join(labbook_dir,
                                      '.gigantum',
                                      'env',
                                      'base',
                                      f"{gtmcore.fixtures.ENV_UNIT_TEST_REPO}_"
                                      f"{gtmcore.fixtures.ENV_UNIT_TEST_BASE}.yaml")
        assert os.path.exists(component_file) is True
        with open(component_file, 'rt') as cf:
            data = yaml.safe_load(cf)

        preinstalled_pkgs = os.listdir(os.path.join(labbook_dir, ".gigantum/env/package_manager"))
        pkg_yaml_files = [n for n in preinstalled_pkgs if '.yaml' in n]
        assert len(pkg_yaml_files) == 7
        for p in pkg_yaml_files:
            with open(os.path.join(labbook_dir, ".gigantum/env/package_manager", p)) as f:
                assert 'from_base: true' in f.read()

        assert data['id'] == gtmcore.fixtures.ENV_UNIT_TEST_BASE
        assert data['revision'] == gtmcore.fixtures.ENV_UNIT_TEST_REV

        # Verify git/activity
        log = lb.git.log()
        assert len(log) >= 4
        assert "_GTM_ACTIVITY_START_" in log[0]["message"]
        assert 'Added base:' in log[0]["message"]
        assert "_GTM_ACTIVITY_START_" in log[2]["message"]
        assert 'Added 6 pip3 package(s)' in log[2]["message"]
        assert "_GTM_ACTIVITY_START_" in log[4]["message"]
        assert 'Added 1 apt package(s)' in log[4]["message"]

    def test_add_duplicate_base(self, mock_config_with_repo):
        """Test adding a duplicate base to a labbook"""
        # Create a labook
        lb = create_tmp_labbook(mock_config_with_repo[0])
        labbook_dir = lb.root_dir

        # Create Component Manager
        cm = ComponentManager(lb)

        # Add a component;
        cm.add_base(gtmcore.fixtures.ENV_UNIT_TEST_REPO, gtmcore.fixtures.ENV_UNIT_TEST_BASE,
                    gtmcore.fixtures.ENV_UNIT_TEST_REV)

        c = f"{gtmcore.fixtures.ENV_UNIT_TEST_REPO}_{gtmcore.fixtures.ENV_UNIT_TEST_BASE}.yaml"
        # Verify file
        component_file = os.path.join(labbook_dir,
                                      '.gigantum',
                                      'env',
                                      'base',
                                      c)
        assert os.path.exists(component_file) is True

        # Add a component
        with pytest.raises(ValueError):
            cm.add_base(gtmcore.fixtures.ENV_UNIT_TEST_REPO, gtmcore.fixtures.ENV_UNIT_TEST_BASE,
                        gtmcore.fixtures.ENV_UNIT_TEST_REV)

    def test_change_base(self, mock_labbook):
        """change_base is used both for updating versions and truly changing the base"""
        conf_file, root_dir, lb = mock_labbook

        # Initial configuration for the labbook - base config taken from `test_add_base` and package config from
        # `test_add_package` - so we don't test assertions (again) on this part
        cm = ComponentManager(lb)

        # We "misconfigure" a package that is not part of the base as if it was from a base
        # This shouldn't happen, but we address it just in case
        pkgs = [{"manager": "pip3", "package": "gigantum", "version": "0.5"},
                # pandas *is* part of the quickstart-juypter base, but we specify a different version here
                {"package": "pandas", "version": "0.21"}]
        cm.add_packages('pip3', pkgs, force=True, from_base=True)
        packages = [p for p in cm.get_component_list('package_manager')]
        assert(len(packages) == 2)
        assert(all(p['from_base'] for p in packages))

        cm.add_base(gtmcore.fixtures.ENV_UNIT_TEST_REPO, 'quickstart-jupyterlab', 1)

        # After installing the base, we should have one version of matplotlib installed
        packages = [p for p in cm.get_component_list('package_manager')
                    if p['package'] == 'matplotlib']
        assert(len(packages) == 1)
        assert(packages[0]['version'] == '2.1.1')

        # add_base() should have converted these to user-installed
        packages = [p for p in cm.get_component_list('package_manager')
                    if p['package'] in ['gigantum', 'pandas']]
        # If we had redundancy from fake base-installed pandas plus real base-installed pandas, this would be 3
        assert(len(packages) == 2)
        for p in packages:
            # Fake base-installed is converted to user ("not from_base") installed
            assert(not p['from_base'])
            if p['package'] == 'pandas':
                # we should still have the fake base-installed version
                assert(p['version'] == '0.21')


        pkgs = [{"manager": "pip3", "package": "requests", "version": "2.18.2"},
                # This will override an already installed package
                {"manager": "pip3", "package": "matplotlib", "version": "2.2"}]
        cm.add_packages('pip3', pkgs, force=True)

        pkgs = [{"manager": "apt", "package": "ack", "version": "1.0"},
                {"manager": "apt", "package": "docker", "version": "3.5"}]
        cm.add_packages('apt', pkgs)

        # Installing a customized version of matplotlib is a new package compared to other tests,
        # and is a critical piece of testing cm.change_base
        packages = [p for p in cm.get_component_list('package_manager')
                    if p['package'] == 'matplotlib']
        assert(len(packages) == 1)
        assert(packages[0]['version'] == '2.2')

        # We upgrade our base
        cm.change_base(gtmcore.fixtures.ENV_UNIT_TEST_REPO, 'quickstart-jupyterlab', 2)

        # matplotlib still set up per "user" update?
        packages = [p for p in cm.get_component_list('package_manager')
                    if p['package'] == 'matplotlib']
        assert(len(packages) == 1)
        assert(packages[0]['version'] == '2.2')

        # Base revision now 2?
        assert(cm.base_fields['revision'] == 2)

    def test_get_component_list_base(self, mock_config_with_repo):
        """Test listing base images added a to labbook"""
        lb = create_tmp_labbook(mock_config_with_repo[0])
        labbook_dir = lb.root_dir
        cm = ComponentManager(lb)

        # mock_config_with_repo is a ComponentManager Instance
        cm.add_base(gtmcore.fixtures.ENV_UNIT_TEST_REPO, gtmcore.fixtures.ENV_UNIT_TEST_BASE,
                    gtmcore.fixtures.ENV_UNIT_TEST_REV)

        bases = cm.get_component_list('base')

        assert len(bases) == 1
        assert bases[0]['id'] == gtmcore.fixtures.ENV_UNIT_TEST_BASE
        assert bases[0]['revision'] == gtmcore.fixtures.ENV_UNIT_TEST_REV

    def test_get_component_list_packages(self, mock_config_with_repo):
        """Test listing packages added a to labbook"""
        lb = create_tmp_labbook(mock_config_with_repo[0])
        labbook_dir = lb.root_dir
        cm = ComponentManager(lb)

        # mock_config_with_repo is a ComponentManager Instance
        pkgs = [{"manager": "pip3", "package": "requests", "version": "2.18.2"},
                {"manager": "pip3", "package": "gigantum", "version": "0.5"}]
        cm.add_packages('pip3', pkgs)

        packages = cm.get_component_list('package_manager')

        assert len(packages) == 2
        assert packages[1]['manager'] == 'pip3'
        assert packages[1]['package'] == 'requests'
        assert packages[1]['version'] == '2.18.2'
        assert packages[0]['manager'] == 'pip3'
        assert packages[0]['package'] == 'gigantum'
        assert packages[0]['version'] == '0.5'

    def test_remove_package_errors(self, mock_config_with_repo):
        """Test removing a package with expected errors"""
        lb = create_tmp_labbook(mock_config_with_repo[0])
        cm = ComponentManager(lb)

        # Try removing package that doesn't exist
        with pytest.raises(ValueError):
            cm.remove_packages('apt', ['ack'])

        # Add a package as if it's from the base
        pkgs = [{"manager": "pip3", "package": "requests", "version": "2.18.2"}]
        cm.add_packages('pip3', pkgs, from_base=True)

        # Try removing package that you can't because it comes from a base
        with pytest.raises(ValueError):
            cm.remove_packages('pip3', ['requests'])

    def test_remove_package(self, mock_config_with_repo):
        """Test removing a package such as one from apt-get or pip3. """
        lb = create_tmp_labbook(mock_config_with_repo[0])
        labbook_dir = lb.root_dir
        cm = ComponentManager(lb)

        # Add some sample components
        pkgs = [{"manager": "pip3", "package": "requests", "version": "2.18.2"},
                {"manager": "pip3", "package": "docker", "version": "0.5"}]
        cm.add_packages('pip3', pkgs)

        pkgs = [{"manager": "apt", "package": "ack", "version": "1.5"},
                {"manager": "apt", "package": "docker", "version": "1.3"}]
        cm.add_packages('apt', pkgs)

        pkgs = [{"manager": "pip3", "package": "matplotlib", "version": "2.0.0"}]
        cm.add_packages('pip3', pkgs, from_base=True)

        package_path = os.path.join(lb._root_dir, '.gigantum', 'env', 'package_manager')
        assert os.path.exists(package_path)

        # Ensure all four packages exist
        assert os.path.exists(os.path.join(package_path, "apt_ack.yaml"))
        assert os.path.exists(os.path.join(package_path, "pip3_requests.yaml"))
        assert os.path.exists(os.path.join(package_path, "apt_docker.yaml"))
        assert os.path.exists(os.path.join(package_path, "pip3_docker.yaml"))
        assert os.path.exists(os.path.join(package_path, "pip3_matplotlib.yaml"))

        # Remove packages
        cm.remove_packages("apt", ["ack", "docker"])
        cm.remove_packages("pip3", ["requests", "docker"])

        with pytest.raises(ValueError):
            cm.remove_packages("pip3", ["matplotlib"])

        # Ensure files are gone
        assert not os.path.exists(os.path.join(package_path, "apt_ack.yaml"))
        assert not os.path.exists(os.path.join(package_path, "pip3_requests.yaml"))
        assert not os.path.exists(os.path.join(package_path, "apt_docker.yaml"))
        assert not os.path.exists(os.path.join(package_path, "pip3_docker.yaml"))
        assert os.path.exists(os.path.join(package_path, "pip3_matplotlib.yaml"))

        # Ensure git is clean
        status = lb.git.status()
        assert status['untracked'] == []
        assert status['staged'] == []
        assert status['unstaged'] == []

        # Ensure activity is being written
        log = lb.git.log()
        assert "_GTM_ACTIVITY_START_" in log[0]["message"]
        assert 'Removed 2 pip3 managed package(s)' in log[0]["message"]

    def test_misconfigured_base_no_base(self, mock_config_with_repo):
        lb = create_tmp_labbook(mock_config_with_repo[0])
        cm = ComponentManager(lb)
        with pytest.raises(ValueError):
            a = cm.base_fields

    def test_misconfigured_base_two_bases(self, mock_config_with_repo):
        conf_file = mock_config_with_repo[0]
        lb = create_tmp_labbook(conf_file)
        cm = ComponentManager(lb)
        # mock_config_with_repo is a ComponentManager Instance
        cm.add_base(gtmcore.fixtures.ENV_UNIT_TEST_REPO, "ut-jupyterlab-1", 0)
        # Updated logic to enable changing bases won't allow `add_base` again. Need to manually create a file
        bad_base_config = Path(cm.env_dir, 'base', 'evil_repo_quantum-deathray.yaml')
        bad_base_config.write_text("I'm gonna break you!")

        with pytest.raises(ValueError):
            a = cm.base_fields

    def test_try_configuring_two_bases(self, mock_config_with_repo):
        conf_file = mock_config_with_repo[0]
        lb = create_tmp_labbook(conf_file)
        cm = ComponentManager(lb)
        # mock_config_with_repo is a ComponentManager Instance
        cm.add_base(gtmcore.fixtures.ENV_UNIT_TEST_REPO, "ut-jupyterlab-1", 0)
        with pytest.raises(ValueError):
            cm.add_base(gtmcore.fixtures.ENV_UNIT_TEST_REPO, "ut-jupyterlab-2", 0)

    def test_get_base(self, mock_config_with_repo):
        lb = create_tmp_labbook(mock_config_with_repo[0])
        cm = ComponentManager(lb)

        # mock_config_with_repo is a ComponentManager Instance
        cm.add_base(gtmcore.fixtures.ENV_UNIT_TEST_REPO, "ut-jupyterlab-1", 0)

        base_data = cm.base_fields

        assert type(base_data) == dict
        assert base_data['name'] == 'Unit Test1'
        assert base_data['os_class'] == 'ubuntu'
        assert base_data['schema'] == 1

    def test_get_base_empty_error(self, mock_config_with_repo):
        lb = create_tmp_labbook(mock_config_with_repo[0])
        cm = ComponentManager(lb)

        # mock_config_with_repo is a ComponentManager Instance
        cm.add_base(gtmcore.fixtures.ENV_UNIT_TEST_REPO, "ut-jupyterlab-1", 0)

        base_filename = f"gigantum_base-images-testing_ut-jupyterlab-1.yaml"
        base_final_path = os.path.join(cm.env_dir, 'base', base_filename)

        with open(base_final_path, 'wt') as cf:
            cf.write(yaml.safe_dump({}, default_flow_style=False))

        with pytest.raises(ValueError):
            cm.base_fields

    def test_add_then_remove_custom_docker_snipper_with_valid_docker(self, mock_config_with_repo):
        lb = create_tmp_labbook(mock_config_with_repo[0])
        snippet = ["RUN true", "RUN touch /tmp/testfile", "RUN rm /tmp/testfile", "RUN echo 'done'"]
        c1 = lb.git.commit_hash
        cm = ComponentManager(lb)
        cm.add_docker_snippet("unittest-docker", docker_content=snippet,
                              description="yada yada's, \n\n **I'm putting in lots of apostrophę's**.")
        c2 = lb.git.commit_hash
        assert c1 != c2

        import yaml
        d = yaml.safe_load(open(os.path.join(lb.root_dir, '.gigantum', 'env', 'docker', 'unittest-docker.yaml')))
        print(d)
        assert d['description'] == "yada yada's, \n\n **I'm putting in lots of apostrophę's**."
        assert d['name'] == 'unittest-docker'
        assert all([d['content'][i] == snippet[i] for i in range(len(snippet))])

        with pytest.raises(ValueError):
            cm.remove_docker_snippet('nothing')

        c1 = lb.git.commit_hash
        cm.remove_docker_snippet('unittest-docker')
        c2 = lb.git.commit_hash
        assert not os.path.exists(os.path.join(lb.root_dir, '.gigantum', 'env', 'docker', 'unittest-docker.yaml'))
        assert c1 != c2
