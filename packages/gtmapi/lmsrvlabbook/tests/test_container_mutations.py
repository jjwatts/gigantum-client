import pytest
import getpass
import time
import pprint
import subprocess
import requests

from lmsrvlabbook.tests.fixtures import fixture_working_dir, fixture_working_dir_env_repo_scoped, \
    build_image_for_jupyterlab, build_image_for_rserver

from gtmcore.container.container import ContainerOperations


@pytest.fixture
def start_proxy():
    if getpass.getuser() == 'circleci':
        cmds = ['configurable-http-proxy', '--port=10000', '--api-port=1999',
                '--no-prepend-path', '--no-include-prefix']
        proxyserver = subprocess.Popen(
                cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)
    try:
        yield
    finally:
        if getpass.getuser() == 'circleci':
            time.sleep(1)
            proxyserver.kill()


class TestContainerMutations(object):
    def test_start_stop_container(self, build_image_for_jupyterlab, start_proxy):
        """Test start stop mutations"""
        docker_client = build_image_for_jupyterlab[2]
        gql_client = build_image_for_jupyterlab[4]

        is_running_query = """
           {
               labbook(name: "containerunittestbook", owner: "unittester") {
                   environment {
                       imageStatus
                       containerStatus
                   }
               }
           }
           """
        r = gql_client.execute(is_running_query)
        assert 'errors' not in r
        assert r['data']['labbook']['environment']['imageStatus'] == 'EXISTS'
        assert r['data']['labbook']['environment']['containerStatus'] == 'NOT_RUNNING'

        try:
            # We wrap the below in a try to ensure the container is cleaned up

            # Start the container
            start_query = """
               mutation myStart {
                 startContainer(input: {labbookName: "containerunittestbook", owner: "unittester"}) {
                   environment {
                     imageStatus
                     containerStatus
                   }
                 }
               }
               """
            r = gql_client.execute(start_query)
            pprint.pprint(r)
            assert r['data']['startContainer']['environment']['imageStatus'] == 'EXISTS'
            assert r['data']['startContainer']['environment']['containerStatus'] == 'RUNNING'

            # TEST GIG-909: Prevent rebuilding images when container for LB already running
            build_q = """
                mutation myBuild {
                    buildImage(input: {
                        labbookName: "containerunittestbook",
                        owner: "unittester"
                    }) {
                        environment {
                            imageStatus
                            containerStatus
                        }                        
                    }
                }
            """
            r = gql_client.execute(build_q)
            assert 'errors' in r  # Yes, we really want to check that the errors key exists
            assert 'Cannot build image for running container' in r['errors'][0]['message']
            assert not r['data']['buildImage']  # Yes, this should be empty due to failure.

            # Stop the container
            stop_query = """
               mutation myStop {
                 stopContainer(input: {labbookName: "containerunittestbook", owner: "unittester"}) {
                   environment {
                     imageStatus
                     containerStatus
                   }
                 }
               }
               """
            r = gql_client.execute(stop_query)
            assert 'errors' not in r
            assert r['data']['stopContainer']['environment']['imageStatus'] == 'EXISTS'
            assert r['data']['stopContainer']['environment']['containerStatus'] == 'NOT_RUNNING'

        except:
            try:
                # Mutation failed. Container *might* have stopped, but try to stop it just in case
                docker_client.containers.get('gmlb-default-unittester-containerunittestbook').stop(timeout=4)
            except:
                # Make a best effort
                pass
            raise
        finally:
            try:
                # Remove the container.
                docker_client.containers.get('gmlb-default-unittester-containerunittestbook').remove()
            except:
                # Make a best effort
                pass

    @pytest.mark.skipif(getpass.getuser() == 'circleci', reason="Cannot run this networking test in CircleCI environment")
    def test_start_jupyterlab(self, build_image_for_jupyterlab):
        """Test listing labbooks"""
        # Start the container
        _, container_id = ContainerOperations.start_container(build_image_for_jupyterlab[0],
                                                                          username='default')

        lb = build_image_for_jupyterlab[0]

        docker_client = build_image_for_jupyterlab[2]
        gql_client = build_image_for_jupyterlab[4]
        owner = build_image_for_jupyterlab[-1]

        try:
            q = f"""
            mutation x {{
                startDevTool(input: {{
                    owner: "{owner}",
                    labbookName: "{lb.name}",
                    devTool: "jupyterlab"
                }}) {{
                    path
                }}

            }}
            """
            r = gql_client.execute(q)
            assert 'errors' not in r

            assert ':10000/jupyter/' in r['data']['startDevTool']['path']
            rc, t = docker_client.containers.get(container_id=container_id).exec_run(
                'sh -c "ps aux | grep jupyter-lab | grep -v \' grep \'"', user='giguser')
            l = [a for a in t.decode().split('\n') if a]
            assert len(l) == 1
        finally:
            # Remove the container you fired up
            docker_client.containers.get(container_id=container_id).stop(timeout=10)
            docker_client.containers.get(container_id=container_id).remove()

    @pytest.mark.skipif(getpass.getuser() == 'circleci', reason="Cannot run this networking test in CircleCI")
    def test_start_bundled_app(self, build_image_for_jupyterlab):
        """Test bundled app

        Note: In the fixture `build_image_for_jupyterlab`, the environment has been augmented to add the bundled app
        "share" with the command "cd /mnt; python3 -m http.server 9999" on port 9999. This test then verifies that
        the command is executed and route opened through the CHP.

        The reason the dev tool is called "share" is because this test simply uses http.server to run a simple web
        server in the /mnt directory. There will be a folder there called "share". http.server doesn't support
        route prefixes unless you write a bit of code, so simply calling the app "share" is a simple work around
        to create a funtioning test. So if you go to the route provided you'll get a 200 back if everything started
        and is wired up OK.
        """
        # Start the container
        _, container_id = ContainerOperations.start_container(build_image_for_jupyterlab[0],
                                                                          username='default')

        lb = build_image_for_jupyterlab[0]

        docker_client = build_image_for_jupyterlab[2]
        gql_client = build_image_for_jupyterlab[4]
        owner = build_image_for_jupyterlab[-1]

        try:
            q = f"""
            mutation x {{
                startDevTool(input: {{
                    owner: "{owner}",
                    labbookName: "{lb.name}",
                    devTool: "share"
                }}) {{
                    path
                }}

            }}
            """
            r = gql_client.execute(q)
            assert 'errors' not in r

            time.sleep(5)
            url = f"http://localhost{r['data']['startDevTool']['path']}"
            response = requests.get(url)
            assert response.status_code == 200

            # Running again should work and just load route
            r = gql_client.execute(q)
            assert 'errors' not in r

            url = f"http://localhost{r['data']['startDevTool']['path']}"
            response = requests.get(url)
            assert response.status_code == 200
        finally:
            # Remove the container you fired up
            docker_client.containers.get(container_id=container_id).stop(timeout=10)
            docker_client.containers.get(container_id=container_id).remove()

    @pytest.mark.skipif(getpass.getuser() == 'circleci', reason="Cannot run this networking test in CircleCI environment")
    def test_start_rserver(self, build_image_for_rserver):
        pytest.xfail("RStudio Server tests not implemented")
