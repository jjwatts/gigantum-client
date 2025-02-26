# Copyright (c) 2018 FlashX, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from typing import Optional, List
from docker.models.containers import Container


def infer_docker_image_name(labbook_name: str, owner: str, username: str) -> str:
    """
    Produce the suggested name for the Docker image from the given LabBook details

    Args:
        labbook_name: Name of subject labbook
        owner: Username of owner of labbook
        username: Optional username of active owner

    Returns:
        A string containing the name that should be used for the Docker image.
        If username is not provided, a known string is substituted.
        Note the prefix "gmlb" means "Gigantum-Managed LabBook".
    """
    return f"gmlb-{username}-{owner}-{labbook_name}"


def ps_search(lb_container: Container, ps_name: str='jupyter') -> List[str]:
    """Exec ps and grep in the container to check for a process

    ps_name should NOT include any extra quotes (it will be surrounded by single-quotes in the shell command)
    """
    ec, ps_list = lb_container.exec_run(
        f'sh -c "ps aux | grep \'{ps_name}\'| grep -v \' grep \'"')
    return [l for l in ps_list.decode().split('\n') if l]

