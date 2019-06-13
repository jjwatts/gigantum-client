import os
import time
import tempfile
import tarfile
from typing import Optional, Tuple

import docker
import docker.errors

from gtmcore.configuration import get_docker_client
from gtmcore.logging import LMLogger
from gtmcore.inventory.inventory import InventoryManager
from gtmcore.labbook import LabBook

from gtmcore.container.utils import infer_docker_image_name
from gtmcore.container.exceptions import ContainerException
from gtmcore.container.core import (build_docker_image, stop_labbook_container,
                                     start_labbook_container, get_container_ip)

logger = LMLogger.get_logger()


class ContainerOperations:

    @classmethod
    def build_image(cls, labbook: LabBook, username: str, override_image_tag: Optional[str] = None,
                    nocache: bool = False) -> Tuple[LabBook, str]:
        """ Build docker image according to the Dockerfile just assembled. Does NOT
            assemble the Dockerfile from environment (See ImageBuilder)

        Args:
            labbook: Subject LabBook to build.
            override_image_tag: Tag of docker image
            nocache: Don't user the Docker cache if True
            username: The current logged in username

        Returns:
            A tuple containing the labbook, docker image id.

        Raises:
            ContainerBuildException if container build fails.
        """
        logger.info(f"Building docker image for {str(labbook)}, "
                    f"using override name `{override_image_tag}`")
        docker_img_id = build_docker_image(labbook.root_dir,
                                           override_image_tag=override_image_tag,
                                           username=username,
                                           nocache=nocache)
        return labbook, docker_img_id

    @classmethod
    def delete_image(cls, labbook: LabBook, username: str,
                     override_image_tag: Optional[str] = None) -> Tuple[LabBook, bool]:
        """ Delete the Docker image for the given LabBook

        Args:
            labbook: Subject LabBook.
            override_image_tag: Tag of docker image (optional)
            username: The current logged in username

        Returns:
            A tuple containing the labbook, docker image id.
        """
        image_name = override_image_tag or cls.labbook_image_name(labbook, username)
        # We need to remove any images pertaining to this labbook before triggering a build.
        logger.info(f"Deleting docker image for {str(labbook)}")
        try:
            get_docker_client().images.get(name=image_name)
            get_docker_client().images.remove(image_name)
            logger.info(f"Deleted docker image for {str(labbook)}: {image_name}")
        except docker.errors.ImageNotFound:
            logger.warning(f"Could not delete docker image for {str(labbook)}: {image_name} not found")
        except Exception as e:
            logger.error("Error deleting docker images for {str(lb)}: {e}")
            return labbook, False
        return labbook, True

    @classmethod
    def run_command(
            cls, cmd_text: str, labbook: LabBook, username: str,
            override_image_tag: Optional[str] = None, fallback_image: str = None) -> bytes:

        """Run a command executed in the context of the LabBook's docker image.

        Args:
            cmd_text: Content of command to be executed.
            labbook: Subject labbook
            username: Optional active username
            override_image_tag: If set, does not automatically infer container name.
            fallback_image: If LabBook image can't be found, use this one instead.

        Returns:
            A tuple containing the labbook, Docker container id, and port mapping.
        """
        image_name = override_image_tag or cls.labbook_image_name(labbook, username)
        # Get a docker client instance
        client = get_docker_client()

        # Verify image name exists. If it doesn't, fallback and use the base image
        try:
            client.images.get(image_name)
        except docker.errors.ImageNotFound:
            # Image not found...assume build has failed and fallback to base
            if not fallback_image:
                raise
            logger.warning(f"LabBook image not available for package query."
                           f"Falling back to base image `{fallback_image}`.")
            image_name = fallback_image

        t0 = time.time()
        try:
            # Note, for container docs see: http://docker-py.readthedocs.io/en/stable/containers.html
            container = client.containers.run(image_name, cmd_text, entrypoint=[], remove=False, detach=True,
                                              stdout=True)
            while container.status != "exited":
                time.sleep(.25)
                container.reload()
            result = container.logs(stdout=True, stderr=False)
            container.remove(v=True)

        except docker.errors.ContainerError as e:
            tfail = time.time()
            logger.error(f'Command ({cmd_text}) failed after {tfail-t0:.2f}s - '
                         f'output: {e.exit_status}, {e.stderr}')
            raise ContainerException(e)

        ts = time.time()
        if ts - t0 > 5.0:
            logger.warning(f'Command ({cmd_text}) in {str(labbook)} took {ts-t0:.2f} sec')

        return result

    @classmethod
    def start_container(cls, labbook: LabBook, username: str,
                        override_image_tag: Optional[str] = None) -> Tuple[LabBook, str]:
        """ Start a Docker container for a given labbook LabBook. Return the new labbook instances
            and a list of TCP port mappings.

        Args:
            labbook: Subject labbook
            username: Optional active username
            override_image_tag: If set, does not automatically infer container name.

        Returns:
            A tuple containing the labbook, Docker container id
        """
        if not os.environ.get('HOST_WORK_DIR'):
            raise ValueError("Environment variable HOST_WORK_DIR must be set")

        container_id = start_labbook_container(labbook_root=labbook.root_dir,
                                               config_path=labbook.client_config.config_file,
                                               override_image_id=override_image_tag,
                                               username=username)
        return labbook, container_id

    @classmethod
    def stop_container(cls, labbook: LabBook, username: str) -> Tuple[LabBook, bool]:
        """ Stop the given labbook. Returns True in the second field if stopped,
            otherwise False (False can simply imply no container was running).

        Args:
            labbook: Subject labbook
            username: Optional username of active user

        Returns:
            A tuple of (Labbook, boolean indicating whether a container was successfully stopped).
        """
        n = cls.labbook_image_name(labbook, username)
        logger.info(f"Stopping {str(labbook)} ({n})")

        try:
            stopped = stop_labbook_container(n)
        finally:
            # Save state of LB when container turned off.
            labbook.sweep_uncommitted_changes()

        return labbook, stopped

    @classmethod
    def labbook_image_name(cls, labbook: LabBook, username: str) -> str:
        """Return the image name of the LabBook container

        Args:
            labbook: Subject LabBook
            username: Username of active user

        Returns:
            Externally facing IP
        """
        owner = InventoryManager().query_owner(labbook)
        return infer_docker_image_name(labbook_name=labbook.name,
                                       owner=owner,
                                       username=username)

    @classmethod
    def get_labbook_ip(cls, labbook: LabBook, username: str) -> str:
        """Return the IP on the docker network of the LabBook container

        Args:
            labbook: Subject LabBook
            username: Username of active user

        Returns:
            Externally facing IP
        """
        docker_key = cls.labbook_image_name(labbook, username)
        return get_container_ip(docker_key)

    @classmethod
    def copy_into_container(cls, labbook: LabBook, username: str, src_path: str, dst_dir: str):
        """Copy the given file in src_path into the project's container.

        Args:
            labbook: Project under consideration.
            username: Active username
            src_path: Source path ON THE HOST of the file - callers responsibility to sanitize
            dst_dir: Destination directory INSIDE THE CONTAINER.
        """
        if not labbook.owner:
            raise ContainerException(f"{str(labbook)} has no owner")

        if not os.path.isfile(src_path):
            raise ContainerException(f"Source file {src_path} is not a file")

        docker_key = infer_docker_image_name(labbook_name=labbook.name,
                                             owner=labbook.owner,
                                             username=username)
        lb_container = docker.from_env().containers.get(docker_key)
        r = lb_container.exec_run(f'sh -c "mkdir -p {dst_dir}"')

        # Tar up the src file to copy into container
        tarred_secret_file = tempfile.NamedTemporaryFile()
        t = tarfile.open(mode='w', fileobj=tarred_secret_file)
        abs_path = os.path.abspath(src_path)
        t.add(abs_path, arcname=os.path.basename(src_path), recursive=True)
        t.close()
        tarred_secret_file.seek(0)

        try:
            logger.info(f"Copying file {src_path} into {dst_dir} in {str(labbook)}")
            docker.from_env().api.put_archive(docker_key, dst_dir, tarred_secret_file)
        finally:
            # Make sure the temporary Tar archive gets deleted.
            tarred_secret_file.close()
