import pytest
import yaml
import os
from snapshottest import snapshot

from lmsrvlabbook.tests.fixtures import fixture_working_dir_env_repo_scoped

from gtmcore.inventory.inventory import InventoryManager
from gtmcore.environment.bundledapp import BundledAppManager


class TestBundledAppMutations(object):

    def test_add_bundled_app(self, fixture_working_dir_env_repo_scoped, snapshot):
        """Test adding a bundled app to a labbooks"""
        im = InventoryManager(fixture_working_dir_env_repo_scoped[0])
        im.create_labbook('default', 'default', 'test-app', description="testing 1")

        lookup_query = """
                           {
                             labbook(owner: "default", name: "test-app"){
                               id
                               environment {
                                 id
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
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(lookup_query))

        # Add a bundled app
        add_query = """
        mutation myBundledAppMutation {
          setBundledApp (input: {
            owner: "default",
            labbookName: "test-app",
            appName: "my app",
            port: 9999,
            description: "a cool app to do things",
            command: "python /opt/app.py"}) {
            clientMutationId
            environment{
              id
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
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(add_query))

        # Query again
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(lookup_query))

        # Edit a bundled app
        add_query = """
        mutation myBundledAppMutation {
          setBundledApp (input: {
            owner: "default",
            labbookName: "test-app",
            appName: "my app",
            port: 9900,
            description: "a cooler app to do things",
            command: "python /opt/app2.py"}) {
            clientMutationId
            environment{
              id
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
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(add_query))

        # Query again
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(lookup_query))

    def test_remove_bundled_app(self, fixture_working_dir_env_repo_scoped, snapshot):
        """Test removing a bundled app from a labbook"""
        im = InventoryManager(fixture_working_dir_env_repo_scoped[0])
        lb = im.create_labbook('default', 'default', 'test-app-2', description="testing 1")
        bam = BundledAppManager(lb)
        bam.add_bundled_app(9999, "dash app 1", "my example bundled app 1", "python /mnt/labbook/code/dash1.py")
        bam.add_bundled_app(8822, "dash app 2", "my example bundled app 2", "python /mnt/labbook/code/dash2.py")
        bam.add_bundled_app(9966, "dash app 3", "my example bundled app 3", "python /mnt/labbook/code/dash3.py")

        lookup_query = """
                           {
                             labbook(owner: "default", name: "test-app-2"){
                               id
                               environment {
                                 id
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
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(lookup_query))

        # Add a bundled app
        remove_query = """
        mutation myBundledAppMutation {
          removeBundledApp (input: {
            owner: "default",
            labbookName: "test-app-2",
            appName: "dash app 2"}) {
            clientMutationId
            environment{
              id
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
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(remove_query))

        # Query again
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(lookup_query))

    def test_start_bundled_app(self, fixture_working_dir_env_repo_scoped, snapshot):
        """Test listing labbooks"""
        im = InventoryManager(fixture_working_dir_env_repo_scoped[0])
        lb = im.create_labbook('default', 'default', 'test-app-1', description="testing 1")
        bam = BundledAppManager(lb)
        bam.add_bundled_app(9999, "dash app 1", "my example bundled app 1", "echo test")

        lookup_query = """
                           {
                             labbook(owner: "default", name: "test-app-1"){
                               id
                               environment {
                                 id
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
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(lookup_query))

        # Add a bundled app
        remove_query = """
        mutation startDevTool {
          removeBundledApp (input: {
            owner: "default",
            labbookName: "test-app-1",
            appName: "dash app 2"}) {
            clientMutationId
            environment{
              id
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
        snapshot.assert_match(fixture_working_dir_env_repo_scoped[2].execute(remove_query))
