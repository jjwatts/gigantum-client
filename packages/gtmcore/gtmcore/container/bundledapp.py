from typing import Optional

from gtmcore.configuration import get_docker_client
from gtmcore.inventory.inventory import InventoryManager
from gtmcore.container.core import infer_docker_image_name
from gtmcore.labbook import LabBook
from gtmcore.exceptions import GigantumException


def start_bundled_app(labbook: LabBook, username: str, command: str, tag: Optional[str] = None) -> None:
    """ Method to start a bundled app by running the user specified command inside the running Project container

    Args:
        labbook: labbook instance
        username: current logged in user
        command: user specified command to run
        tag: optional tag for the container override id

    Returns:

    """
    if len(command) == 0:
        return

    owner = InventoryManager().query_owner(labbook)
    lb_key = tag or infer_docker_image_name(labbook_name=labbook.name,
                                            owner=owner,
                                            username=username)
    docker_client = get_docker_client()
    lb_container = docker_client.containers.get(lb_key)
    if lb_container.status != 'running':
        raise GigantumException(f"{str(labbook)} container is not running. Start it before starting a bundled app.")

    lb_container.exec_run(f'sh -c "{command}"', detach=True, user='giguser')
