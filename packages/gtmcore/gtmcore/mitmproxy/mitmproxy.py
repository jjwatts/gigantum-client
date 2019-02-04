import time
from typing import Optional

import redis

from gtmcore.configuration import get_docker_client
from gtmcore.logging import LMLogger
from gtmcore.exceptions import GigantumException

logger = LMLogger.get_logger()
CURRENT_MITMPROXY_TAG = '37af201e'


class MITMProxyOperations(object):

    @classmethod
    def get_mitmendpoint(cls, lb_endpoint: str) -> Optional[str]:
        """Determine in there is a proxy installed for this endpoint

        Args:
            lb_endpoint: the specific target running a dev tool

        Returns:
            str that contains the proxy endpoint as http://{ip}:{port}
        """
        redis_conn = redis.Redis(db=1)
        retval = redis_conn.get(f"{lb_endpoint}-mitm-endpoint")
        if retval:
            return retval.decode()
        else:
            return None

    @classmethod
    def get_mitmcontainerid(cls, lb_endpoint: str) -> Optional[str]:
        """Return the container associated with the mitm proxy.

        Args:
            lb_endpoint: the specific target running a dev tool

        Returns:
        str that contains the containerid
        """
        redis_conn = redis.Redis(db=1)
        retval = redis_conn.get(f"{lb_endpoint}-mitm-container_id")
        if retval:
            return retval.decode()
        else:
            return None

    @classmethod
    def get_mitmkey(cls, lb_endpoint: str) -> Optional[str]:
        """Return the key associated with the mitm proxy.

        Args:
            lb_endpoint: the specific target running a dev tool

        Returns:
        str that contains the key
        """
        redis_conn = redis.Redis(db=1)
        retval = redis_conn.get(f"{lb_endpoint}-mitm-container_id")
        if retval:
            return retval.decode()
        else:
            return None

    @classmethod
    def start_mitm_proxy(cls, lb_endpoint: str, key: str) -> str:
        """Launch a proxy cointainer between client and labbook.

        Args:
            lb_endpoint: the specific target running a dev tool
            key: a unique key for this instance (related to the monitored Project container - e.g., RStudio)

        Returns:
            str that contains the proxy endpoint as http://{ip}:{port}
        """

        # setup the environment - note that UID is obtained inside the container based on labmanager_share_vol
        # (mounted at /mnt/share)
        env_var = [f"LBENDPOINT={lb_endpoint}", f"PROXYID={key}"]
        nametag = f"gmitmproxy.{key}"
        volumes_dict = {
            'labmanager_share_vol': {'bind': '/mnt/share', 'mode': 'rw'}
        }

        docker_client = get_docker_client()

        container = docker_client.containers.run("gigantum/mitmproxy_proxy:" + CURRENT_MITMPROXY_TAG, detach=True,
                                                 init=True, name=nametag, volumes=volumes_dict,
                                                 environment=env_var)

        # For now, we hammer repeatedly for 5 seconds
        # Plan for a better solution is mentioned in #434
        for _ in range(50):
            time.sleep(.1)
            # Hope that our container is actually up and reload
            container.reload()
            container_ip = container.attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
            if container_ip:
                break

        if not container_ip:
            raise GigantumException("Unable to get mitmproxy_proxy IP address.")

        mitm_endpoint = f'http://{container_ip}:8079'

        # register the proxy in KV store
        redis_conn = redis.Redis(db=1)
        redis_conn.set(f"{lb_endpoint}-mitm-endpoint", mitm_endpoint)
        redis_conn.set(f"{lb_endpoint}-mitm-container_id", container.id)
        redis_conn.set(f"{lb_endpoint}-mitm-key", key)

        # make sure proxy is up.
        for timeout in range(10):
            time.sleep(1)
            ec, new_ps_list = container.exec_run(
                f'sh -c "ps aux | grep nginx | grep -v \' grep \'"')
            new_ps_list = new_ps_list.decode().split('\n')
            if any('nginx' in l for l in new_ps_list):
                logger.info(f"Proxy to rserver started within {timeout + 1} seconds")
                break
        else:
            raise ValueError('mitmproxy failed to start after 10 seconds')

        return mitm_endpoint

    @classmethod
    def stop_mitm_proxy(cls, lb_endpoint: str) -> str:
        """Stop the MITM proxy. Destroy container. Delete volume.

        Args:
            lb_endpoint: the specific target running a dev tool

        Returns:
            ip address of the mitm_proxy for removing the route
        """
        container_id = MITMProxyOperations.get_mitmcontainerid(lb_endpoint)

        # stop the mitm container
        docker_client = get_docker_client()
        mitm_container = docker_client.containers.get(container_id)
        mitm_container.stop()
        mitm_container.remove()

        # unregister the proxy in KV store
        redis_conn = redis.Redis(db=1)
        mitm_endpoint = redis_conn.get(f"{lb_endpoint}-mitm-endpoint").decode()
        redis_conn.delete(f"{lb_endpoint}-mitm-endpoint")
        redis_conn.delete(f"{lb_endpoint}-mitm-container_id")
        redis_conn.delete(f"{lb_endpoint}-mitm-key")

        return mitm_endpoint
