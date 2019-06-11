import os
import tempfile
import docker

from gtmcore.fixtures.container import build_lb_image_for_jupyterlab, mock_config_with_repo, ContainerFixture

from gtmcore.labbook import SecretStore
from gtmcore.workflows import ContainerWorkflows
from gtmcore.container import ContainerOperations


class TestStartContainer(object):
    def test_with_secrets(self, build_lb_image_for_jupyterlab):
        fix = ContainerFixture(build_lb_image_for_jupyterlab)
        fix.docker_client.containers.get(fix.docker_container_id).stop()
        fix.docker_client.containers.get(fix.docker_container_id).remove()

        sectore = SecretStore(fix.labbook, fix.username)
        target_dir = '/root/.aws-sample-creds'

        sectore['private-key.key'] = target_dir
        sectore['public-key.key'] = target_dir

        with tempfile.TemporaryDirectory() as tempdir:
            p1 = open(os.path.join(tempdir, 'private-key.key'), 'wb')
            p1.write(b'AWS-mock-PRIVATE')
            p1.close()
            p2 = open(os.path.join(tempdir, 'public-key.key'), 'wb')
            p2.write(b'AWS-mock-PUBLIC')
            p2.close()

            # Add the mock AWS keys
            l1 = sectore.insert_file(p1.name)
            l2 = sectore.insert_file(p2.name)

        container_id = ContainerWorkflows.start_labbook(fix.labbook, fix.username)

        with tempfile.TemporaryDirectory() as td2:
            tfile = open(os.path.join(td2, 'sample.py'), 'w')
            tfile.write("""
import os
r = os.path.expanduser('~/.aws-sample-creds')
pri_key = open(os.path.join(r, 'private-key.key')).read(1000)
pub_key = open(os.path.join(r, 'public-key.key')).read(1000)
print(pri_key, pub_key)""")
            tfile.close()
            ContainerOperations.copy_into_container(fix.labbook, fix.username,
                                                    src_path=tfile.name,
                                                    dst_dir='/tmp/samplescript')
            r = fix.docker_client.containers.get(container_id).\
                exec_run(f'sh -c "python /tmp/samplescript/sample.py"')

            # Run the script to load and print out the mock "secret" keys
            assert r.output.decode().strip() == 'AWS-mock-PRIVATE AWS-mock-PUBLIC'
