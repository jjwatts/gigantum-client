import pytest
import graphene
import pprint

from gtmcore.inventory.inventory import InventoryManager
from gtmcore.fixtures import ENV_UNIT_TEST_REPO, ENV_UNIT_TEST_BASE, ENV_UNIT_TEST_REV
from gtmcore.environment import ComponentManager
from gtmcore.environment.bundledapp import BundledAppManager


from lmsrvlabbook.tests.fixtures import fixture_working_dir_env_repo_scoped, fixture_working_dir


class TestEnvironmentServiceQueries(object):
    def test_get_environment_status(self, fixture_working_dir, snapshot):
        """Test getting the a LabBook's environment status"""
        im = InventoryManager(fixture_working_dir[0])
        lb = im.create_labbook("default", "default", "labbook10", description="my first labbook10000")

        query = """
        {
          labbook(owner: "default", name: "labbook10") {
              environment {
                containerStatus
                imageStatus
              }
          }
        }
        """
        snapshot.assert_match(fixture_working_dir[2].execute(query))

    def test_get_base(self, fixture_working_dir_env_repo_scoped, snapshot):
        """Test getting the a LabBook's base"""
        # Create labbook
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
        variables = {"name": "labbook-base-test", "desc": "my test 1",
                     "base_id": ENV_UNIT_TEST_BASE, "repository": ENV_UNIT_TEST_REPO,
                     "revision": ENV_UNIT_TEST_REV}
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query, variable_values=variables))

        query = """
                {
                  labbook(owner: "default", name: "labbook-base-test") {
                    name
                    description
                    environment {
                      base{                        
                        id
                        componentId
                        name
                        description
                        readme
                        tags
                        icon
                        osClass
                        osRelease
                        license
                        url
                        languages
                        developmentTools
                        dockerImageServer
                        dockerImageNamespace
                        dockerImageRepository
                        dockerImageTag
                        packageManagers
                      }
                    }
                  }
                }
        """
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query))

    def test_get_package_manager(self, fixture_working_dir_env_repo_scoped, snapshot):
        """Test getting the a LabBook's package manager dependencies"""
        # Create labbook
        im = InventoryManager(fixture_working_dir_env_repo_scoped[0])
        lb = im.create_labbook("default", "default", "labbook4", description="my first labbook10000")

        query = """
                    {
                      labbook(owner: "default", name: "labbook4") {
                        environment {
                         packageDependencies {
                            edges {
                              node {
                                id
                                manager
                                package
                                version
                                fromBase
                              }
                              cursor
                            }
                            pageInfo {
                              hasNextPage
                            }
                          }
                        }
                      }
                    }
                    """
        # should be null
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query))

        # Add a base image
        cm = ComponentManager(lb)
        pkgs = [{"manager": "pip", "package": "requests", "version": "1.3"},
                {"manager": "pip", "package": "numpy", "version": "1.12"},
                {"manager": "pip", "package": "gtmunit1", "version": "0.2.4"}]
        cm.add_packages('pip', pkgs)

        pkgs = [{"manager": "conda3", "package": "cdutil", "version": "8.1"},
                {"manager": "conda3", "package": "nltk", "version": '3.2.5'}]
        cm.add_packages('conda3', pkgs)

        # Add one package without a version, which should cause an error in the API since version is required
        pkgs = [{"manager": "apt", "package": "lxml", "version": "3.4"}]
        cm.add_packages('apt', pkgs)

        query = """
                   {
                     labbook(owner: "default", name: "labbook4") {
                       environment {
                        packageDependencies {
                            edges {
                              node {
                                id
                                manager
                                package
                                version
                                fromBase
                              }
                              cursor
                            }
                            pageInfo {
                              hasNextPage
                            }
                          }
                       }
                     }
                   }
                   """
        r1 = fixture_working_dir_env_repo_scoped[2].execute(query)
        assert 'errors' not in r1
        snapshot.assert_match(r1)

        query = """
                   {
                     labbook(owner: "default", name: "labbook4") {
                       environment {
                        packageDependencies(first: 2, after: "MA==") {
                            edges {
                              node {
                                id
                                manager
                                package
                                version
                                fromBase
                              }
                              cursor
                            }
                            pageInfo {
                              hasNextPage
                            }
                          }
                       }
                     }
                   }
                   """
        r1 = fixture_working_dir_env_repo_scoped[2].execute(query)
        assert 'errors' not in r1
        snapshot.assert_match(r1)

    def test_get_package_manager_metadata(self, fixture_working_dir_env_repo_scoped, snapshot):
        """Test getting the a LabBook's package manager dependencies"""
        # Create labbook
        im = InventoryManager(fixture_working_dir_env_repo_scoped[0])
        lb = im.create_labbook("default", "default", "labbook4meta", description="my first asdf")

        query = """
                    {
                      labbook(owner: "default", name: "labbook4meta") {
                        environment {
                         packageDependencies {
                            edges {
                              node {
                                id
                                manager
                                package
                                version
                                fromBase
                                description
                                docsUrl
                                latestVersion
                              }
                              cursor
                            }
                            pageInfo {
                              hasNextPage
                            }
                          }
                        }
                      }
                    }
                    """
        # should be null
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query))

        # Add a base image
        cm = ComponentManager(lb)
        pkgs = [{"manager": "pip", "package": "gtmunit3", "version": "5.0"},
                {"manager": "pip", "package": "gtmunit2", "version": "12.2"},
                {"manager": "pip", "package": "gtmunit1", "version": '0.2.1'}]
        cm.add_packages('pip', pkgs)

        pkgs = [{"manager": "conda3", "package": "cdutil", "version": "8.1"},
                {"manager": "conda3", "package": "python-coveralls", "version": "2.5.0"}]
        cm.add_packages('conda3', pkgs)

        r1 = fixture_working_dir_env_repo_scoped[2].execute(query)
        assert 'errors' not in r1
        snapshot.assert_match(r1)

    def test_package_query_with_errors(self, snapshot, fixture_working_dir_env_repo_scoped):
        """Test querying for package info"""
        # Create labbook
        im = InventoryManager(fixture_working_dir_env_repo_scoped[0])
        lb = im.create_labbook("default", "default", "labbook5", description="my first labbook10000")

        query = """
                    {
                      labbook(owner: "default", name: "labbook5"){
                        id
                        checkPackages(packageInput: [
                          {manager: "pip", package: "gtmunit1", version:"0.2.4"},
                          {manager: "pip", package: "gtmunit2", version:"100.00"},
                          {manager: "pip", package: "gtmunit3", version:""},
                          {manager: "pip", package: "asdfasdfasdf", version:""}]){
                          id
                          manager 
                          package
                          version
                          latestVersion
                          description
                          isValid     
                        }
                      }
                    }
                """

        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query))

    def test_package_query_with_errors_conda(self, snapshot, fixture_working_dir_env_repo_scoped):
        """Test querying for package info"""
        # Create labbook
        im = InventoryManager(fixture_working_dir_env_repo_scoped[0])
        lb = im.create_labbook("default", "default", "labbook5conda", description="my first labbook10000")

        query = """
                    {
                      labbook(owner: "default", name: "labbook5conda"){
                        id
                        checkPackages(packageInput: [
                          {manager: "conda3", package: "cdutil", version:"8.1"},
                          {manager: "conda3", package: "nltk", version:"100.00"},
                          {manager: "conda3", package: "python-coveralls", version:""},
                          {manager: "conda3", package: "thisshouldtotallyfail", version:"1.0"},
                          {manager: "conda3", package: "notarealpackage", version:""}]){
                          id
                          manager 
                          package
                          version
                          latestVersion
                          description
                          isValid     
                        }
                      }
                    }
                """

        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query))

    def test_package_query_with_errors_apt(self, snapshot, fixture_working_dir_env_repo_scoped):
        """Test querying for package info"""
        # Create labbook
        im = InventoryManager(fixture_working_dir_env_repo_scoped[0])
        lb = im.create_labbook("default", "default", "labbook5apt", description="my first labbook10000")

        # Create Component Manager
        cm = ComponentManager(lb)

        # Add a component
        cm.add_base(ENV_UNIT_TEST_REPO, ENV_UNIT_TEST_BASE, ENV_UNIT_TEST_REV)

        query = """
                    {
                      labbook(owner: "default", name: "labbook5apt"){
                        id
                        checkPackages(packageInput: [
                          {manager: "apt", package: "curl", version:"8.1"},
                          {manager: "apt", package: "notarealpackage", version:""}]){
                          id
                          manager 
                          package
                          version
                          latestVersion
                          description
                          isValid     
                        }
                      }
                    }
                """

        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query))

    def test_package_query(self, snapshot, fixture_working_dir_env_repo_scoped):
        """Test querying for package info"""
        im = InventoryManager(fixture_working_dir_env_repo_scoped[0])
        lb = im.create_labbook("default", "default", "labbook6", description="my first labbook10000")

        query = """
                    {
                      labbook(owner: "default", name: "labbook6"){
                        id
                        checkPackages(packageInput: [
                          {manager: "pip", package: "gtmunit1", version:"0.2.4"},
                          {manager: "pip", package: "gtmunit2", version:""}]){
                          id
                          manager 
                          package
                          version
                          isValid     
                        }
                      }
                    }
                """
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query))

    def test_package_query_no_version(self, snapshot, fixture_working_dir_env_repo_scoped):
        """Test querying for package info"""
        im = InventoryManager(fixture_working_dir_env_repo_scoped[0])
        lb = im.create_labbook("default", "default", "labbook6noversion", description="my first labbook10000")

        # Create Component Manager
        cm = ComponentManager(lb)
        cm.add_base(ENV_UNIT_TEST_REPO, ENV_UNIT_TEST_BASE, ENV_UNIT_TEST_REV)

        query = """
                    {
                      labbook(owner: "default", name: "labbook6noversion"){
                        id
                        checkPackages(packageInput: [
                          {manager: "pip", package: "gtmunit1"},
                          {manager: "pip", package: "notarealpackage"}]){
                          id
                          manager 
                          package
                          version
                          latestVersion
                          description
                          isValid     
                        }
                      }
                    }
                """
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query))

        query = """
                    {
                      labbook(owner: "default", name: "labbook6noversion"){
                        id
                        checkPackages(packageInput: [                         
                          {manager: "apt", package: "curl"},
                          {manager: "apt", package: "notarealpackage"}]){
                          id
                          manager 
                          package
                          version
                          latestVersion
                          description
                          isValid     
                        }
                      }
                    }
                """
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query))

        query = """
                    {
                      labbook(owner: "default", name: "labbook6noversion"){
                        id
                        checkPackages(packageInput: [
                          {manager: "conda3", package: "nltk"},
                          {manager: "conda3", package: "notarealpackage"}]){
                          id
                          manager 
                          package
                          version
                          latestVersion
                          description
                          isValid     
                        }
                      }
                    }
                """
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query))

    def test_bundle_app_query(self, snapshot, fixture_working_dir_env_repo_scoped):
        """Test querying for bundled app info"""
        im = InventoryManager(fixture_working_dir_env_repo_scoped[0])
        lb = im.create_labbook("default", "default", "labbook-bundle", description="my first df")

        query = """
                    {
                      labbook(owner: "default", name: "labbook-bundle"){
                        id
                        environment {
                          bundledApps{
                            id
                            appName
                            description
                            port
                            command
                          }
                        }
                      }
                    }
                """
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query))

        bam = BundledAppManager(lb)
        bam.add_bundled_app(8050, 'dash 1', 'a demo dash app 1', 'python app1.py')
        bam.add_bundled_app(9000, 'dash 2', 'a demo dash app 2', 'python app2.py')
        bam.add_bundled_app(9001, 'dash 3', 'a demo dash app 3', 'python app3.py')

        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(query))
