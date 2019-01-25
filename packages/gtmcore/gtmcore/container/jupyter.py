import uuid
import time
import os
import re
from typing import Optional

import redis
import requests

from gtmcore.logging import LMLogger
from gtmcore.configuration import get_docker_client
from gtmcore.inventory.inventory import InventoryManager
from gtmcore.environment import ComponentManager
from gtmcore.container.core import infer_docker_image_name, get_container_ip
from gtmcore.labbook import LabBook
from gtmcore.exceptions import GigantumException

logger = LMLogger.get_logger()

DEFAULT_JUPYTER_PORT = 8888


def start_jupyter(labbook: LabBook, username: str, tag: Optional[str] = None,
                  check_reachable: bool = True,
                  proxy_prefix: Optional[str] = None) -> str:
    """ Main entrypoint to launching Jupyter. Note, the caller must
        determine for themselves the host and port.

    Returns:
        Path to jupyter (e.g., "/lab?token=xyz")
    """
    owner = InventoryManager().query_owner(labbook)
    lb_key = tag or infer_docker_image_name(labbook_name=labbook.name,
                                            owner=owner,
                                            username=username)
    docker_client = get_docker_client()
    lb_container = docker_client.containers.get(lb_key)
    if lb_container.status != 'running':
        raise GigantumException(f"{str(labbook)} container is not running. Start it before launch a dev tool.")

    search_sh = f'sh -c "ps aux | grep \'jupyter lab\' | grep -v \' grep \'"'
    ec, jupyter_tokens = lb_container.exec_run(search_sh)
    jupyter_ps = [l for l in jupyter_tokens.decode().split('\n') if l]

    # Get IP of container on Docker Bridge Network
    lb_ip_addr = get_container_ip(lb_key)

    if len(jupyter_ps) == 1:
        logger.info(f'Found existing Jupyter instance for {str(labbook)}.')

        # Get token from PS in container
        t = re.search("token='?([a-zA-Z\d-]+)'?", jupyter_ps[0])
        if not t:
            raise GigantumException('Cannot detect Jupyter Lab token')
        token = t.groups()[0]
        suffix = f'{proxy_prefix or ""}/lab/tree/code?token={token}'

        if check_reachable:
            check_jupyter_reachable(lb_ip_addr, DEFAULT_JUPYTER_PORT, f'{proxy_prefix or ""}')

        return suffix
    elif len(jupyter_ps) == 0:
        token = str(uuid.uuid4()).replace('-', '')
        if proxy_prefix and proxy_prefix[0] != '/':
            proxy_prefix = f'/{proxy_prefix}'
        _start_jupyter_process(labbook, lb_container, username, lb_key, token,
                               proxy_prefix)
        suffix = f'{proxy_prefix or ""}/lab/tree/code?token={token}'
        if check_reachable:
            check_jupyter_reachable(lb_ip_addr, DEFAULT_JUPYTER_PORT, f'{proxy_prefix or ""}')
        return suffix
    else:
        # If "ps aux" for jupyterlab returns multiple hits - this should never happen.
        for n, l in enumerate(jupyter_ps):
            logger.error(f'Multiple JupyerLab instances - ({n+1} of {len(jupyter_ps)}) - {l}')
        raise ValueError(f'Multiple Jupyter Lab instances detected in project env. You should restart the container.')


def _shim_skip_python2_savehook(labbook: LabBook) -> bool:
    """Return True if the LabBook uses a Python 2 base image.
    If the base is Python 2, we cannot use the save hook. There is no upstream fix coming. """
    cm = ComponentManager(labbook)
    return 'python2' in cm.base_fields['id'].lower().replace(' ', '')


def _start_jupyter_process(labbook: LabBook, lb_container,
                           username: str, lb_key: str, token: str,
                           proxy_prefix: Optional[str] = None) -> None:
    use_savehook = os.path.exists('/mnt/share/jupyterhooks') \
                   and not _shim_skip_python2_savehook(labbook)
    owner = InventoryManager().query_owner(labbook)
    cmd = (f"export PYTHONPATH=/mnt/share:$PYTHONPATH && "
           f'echo "{username},{owner},{labbook.name},{token}" > /home/giguser/jupyter_token && '
           f"cd /mnt/labbook && "
           f"jupyter lab --port={DEFAULT_JUPYTER_PORT} --ip=0.0.0.0 "
           f"--NotebookApp.token='{token}' --no-browser "
           f'--ConnectionFileMixin.ip=0.0.0.0 ' +
           (f'--FileContentsManager.post_save_hook="jupyterhooks.post_save_hook" '
            if use_savehook else "") +
           (f'--NotebookApp.base_url="{proxy_prefix}" '
            if proxy_prefix else ''))

    lb_container.exec_run(f'sh -c "{cmd}"', detach=True, user='giguser')

    # Pause briefly to avoid race conditions
    for timeout in range(10):
        time.sleep(1)
        ec, new_ps_list = lb_container.exec_run(
            f'sh -c "ps aux | grep jupyter | grep -v \' grep \'"')
        new_ps_list = new_ps_list.decode().split('\n')
        if any(['jupyter lab' in l or 'jupyter-lab' in l for l in new_ps_list]):
            logger.info(f"JupyterLab started within {timeout + 1} seconds")
            break
    else:
        raise ValueError('Jupyter Lab failed to start after 10 seconds')

    # Store token in redis for later activity monitoring
    # (activity data is stored in db1)
    redis_conn = redis.Redis(db=1)
    redis_conn.set(f"{lb_key}-jupyter-token", token)


def check_jupyter_reachable(ip_address: str, port: int, prefix: str):
    for n in range(20):
        test_url = f'http://{ip_address}:{port}{prefix}/api'
        logger.debug(f"Attempt {n + 1}: Testing if JupyerLab is up at {test_url}...")
        try:
            r = requests.get(test_url, timeout=0.5)
            if r.status_code != 200:
                time.sleep(0.5)
            else:
                if "version" in r.json():
                    logger.info(f'Found JupyterLab up at {test_url} after {n/2.0} seconds')
                    break
                else:
                    time.sleep(0.5)
        except requests.exceptions.ConnectionError:
            # Assume API isn't up at all yet, so no connection can be made
            time.sleep(0.5)
    else:
        raise GigantumException(f'Could not reach JupyterLab at {test_url} after timeout')
