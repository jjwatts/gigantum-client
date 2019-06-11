import pytest
import os
import time
import getpass
import docker
import time
import requests
import shutil
import tempfile
from gtmcore.container.jupyter import start_jupyter
from gtmcore.container.bundledapp import start_bundled_app

from gtmcore.configuration import get_docker_client

from gtmcore.container.container import ContainerOperations
from gtmcore.container.utils import infer_docker_image_name
from gtmcore.inventory.inventory import InventoryManager

from gtmcore.fixtures.container import build_lb_image_for_jupyterlab, mock_config_with_repo, ContainerFixture
from gtmcore.container.exceptions import ContainerBuildException, ContainerException
from gtmcore.container.exceptions import ContainerBuildException
from gtmcore.environment.bundledapp import BundledAppManager



def remove_image_cache_data():
    try:
        shutil.rmtree('/mnt/gigantum/.labmanager/image-cache', ignore_errors=True)
    except:
        pass


class TestContainerOps(object):
    def test_build_image_fixture(self, build_lb_image_for_jupyterlab):
        # Note, the test is in the fixure (the fixture is needed by other tests around here).
        pass

    def test_start_jupyterlab(self, build_lb_image_for_jupyterlab):
        container_id = build_lb_image_for_jupyterlab[4]
        docker_image_id = build_lb_image_for_jupyterlab[3]
        client = build_lb_image_for_jupyterlab[2]
        ib = build_lb_image_for_jupyterlab[1]
        lb = build_lb_image_for_jupyterlab[0]

        ec, stdo = client.containers.get(container_id=container_id).exec_run(
            'sh -c "ps aux | grep jupyter | grep -v \' grep \'"', user='giguser')
        l = [a for a in stdo.decode().split('\n') if a]
        assert len(l) == 0

        start_jupyter(lb, username='unittester', check_reachable=not (getpass.getuser() == 'circleci'))

        ec, stdo = client.containers.get(container_id=container_id).exec_run(
            'sh -c "ps aux | grep jupyter-lab | grep -v \' grep \'"', user='giguser')
        l = [a for a in stdo.decode().split('\n') if a]
        assert len(l) == 1

        # Now, we test the second path through, start jupyterlab when it's already running.
        start_jupyter(lb, username='unittester', check_reachable=not (getpass.getuser() == 'circleci'))

        # Validate there is only one instance running.
        ec, stdo = client.containers.get(container_id=container_id).exec_run(
            'sh -c "ps aux | grep jupyter-lab | grep -v \' grep \'"', user='giguser')
        l = [a for a in stdo.decode().split('\n') if a]
        assert len(l) == 1

    def test_run_command(self, build_lb_image_for_jupyterlab):
        my_lb = build_lb_image_for_jupyterlab[0]
        docker_image_id = build_lb_image_for_jupyterlab[3]

        result = ContainerOperations.run_command("echo My sample message", my_lb, username="unittester")
        assert result.decode().strip() == 'My sample message'

        result = ContainerOperations.run_command("pip search gigantum", my_lb, username="unittester")
        assert any(['Gigantum Platform' in l for l in result.decode().strip().split('\n')])

        result = ContainerOperations.run_command("/bin/true", my_lb, username="unittester")
        assert result.decode().strip() == ""

        result = ContainerOperations.run_command("/bin/false", my_lb, username="unittester")
        assert result.decode().strip() == ""

    def test_old_dockerfile_removed_when_new_build_fails(self, build_lb_image_for_jupyterlab):
        # Test that when a new build fails, old images are removed so they cannot be launched.
        my_lb = build_lb_image_for_jupyterlab[0]
        docker_image_id = build_lb_image_for_jupyterlab[3]

        my_lb, stopped = ContainerOperations.stop_container(my_lb, username="unittester")

        assert stopped

        olines = open(os.path.join(my_lb.root_dir, '.gigantum/env/Dockerfile')).readlines()[:6]
        with open(os.path.join(my_lb.root_dir, '.gigantum/env/Dockerfile'), 'w') as dockerfile:
            dockerfile.write('\n'.join(olines))
            dockerfile.write('\nRUN /bin/false')

        # We need to remove cache data otherwise the following tests won't work
        remove_image_cache_data()

        with pytest.raises(ContainerBuildException):
            ContainerOperations.build_image(labbook=my_lb, username="unittester")

        with pytest.raises(docker.errors.ImageNotFound):
            owner = InventoryManager().query_owner(my_lb)
            get_docker_client().images.get(infer_docker_image_name(labbook_name=my_lb.name,
                                                                   owner=owner,
                                                                   username="unittester"))

        with pytest.raises(requests.exceptions.HTTPError):
            # Image not found so container cannot be started
            ContainerOperations.start_container(labbook=my_lb, username="unittester")


class TestPutFile(object):
    def test_put_single_file(self, build_lb_image_for_jupyterlab):
        # Note - we are combining multiple tests in one to speed things up
        # We do not want to build, start, execute, stop, and delete at container for each
        # of the following test points.
        fixture = ContainerFixture(build_lb_image_for_jupyterlab)
        container = docker.from_env().containers.get(fixture.docker_container_id)

        # Test insert of a single file.
        dst_dir_1 = "/home/giguser/sample-creds"
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, 'secretfile'), 'w') as sample_secret:
                sample_secret.write("<<Secret File Content>>")
            t0 = time.time()
            ContainerOperations.copy_into_container(fixture.labbook, fixture.username,
                                                    src_path=sample_secret.name,
                                                    dst_dir=dst_dir_1)
            tf = time.time()
            container.exec_run(f'sh -c "cat {dst_dir_1}/secretfile"')

            # The copy_into_container should NOT remove the original file on disk.
            assert os.path.exists(sample_secret.name)
            assert tf - t0 < 1.0, \
                f"Time to insert small file must be less than 1 sec - took {tf-t0:.2f}s"

    @pytest.mark.skipif(getpass.getuser() == 'circleci', reason="Cannot run this test in CircleCI, needs shared vol")
    def test_start_bundled_app(self, build_lb_image_for_jupyterlab):
        test_file_path = os.path.join('/mnt', 'share', 'test.txt')
        try:
            lb = build_lb_image_for_jupyterlab[0]

            assert os.path.exists(test_file_path) is False

            bam = BundledAppManager(lb)
            bam.add_bundled_app(9002, 'my app', 'tester', f"echo 'teststr' >> {test_file_path}")
            apps = bam.get_bundled_apps()

            start_bundled_app(lb, 'unittester', apps['my app']['command'])

            time.sleep(3)
            assert os.path.exists(test_file_path) is True
        except:
            raise
        finally:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
