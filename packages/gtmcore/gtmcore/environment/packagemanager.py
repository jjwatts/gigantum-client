# Copyright (c) 2017 FlashX, LLC
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
import abc
from typing import (List, Dict, Optional, NamedTuple)

from gtmcore.labbook import LabBook
import gtmcore.environment

# A namedtuple for the result of package validation
PackageResult = NamedTuple('PackageResult', [('package', str), ('version', Optional[str]), ('error', bool)])

# A namedtuple for supported package metadata
PackageMetadata = NamedTuple('PackageMetadata', [('package_manager', str), ('package', str),
                                                 ('latest_version', Optional[str]),
                                                 ('description', Optional[str]), ('docs_url', Optional[str])])


class PackageManager(metaclass=abc.ABCMeta):
    """Class to implement the standard interface for all available Package Managers
    """

    @staticmethod
    def fallback_image(labbook: LabBook) -> str:
        """ Generate the image name of the LabManager if the docker image for
            the given labbook cannot be found. """
        cm = getattr(gtmcore.environment, 'ComponentManager')(labbook)
        base = cm.base_fields
        return f"{base['image']['namespace']}" \
               f"/{base['image']['repository']}" \
               f":{base['image']['tag']}"

    @abc.abstractmethod
    def search(self, search_str: str, labbook: LabBook, username: str) -> List[str]:
        """Method to search a package manager for packages based on a string. The string can be a partial string.

        Args:
            search_str: The string to search on
            labbook: Subject LabBook
            username: username of current user

        Returns:
            list(str): The list of package names that match the search string
        """
        raise NotImplemented

    @abc.abstractmethod
    def list_versions(self, package_name: str, labbook: LabBook, username: str) -> List[str]:
        """Method to list all available versions of a package based on the package name with the latest package first

        Args:
            package_name: Name of the package to query
            labbook: Subject LabBook
            username: username of current user

        Returns:
            list(str): Version strings
        """
        raise NotImplemented

    @abc.abstractmethod
    def list_installed_packages(self, labbook: LabBook, username: str) -> List[Dict[str, str]]:
        """Method to get a list of all packages that are currently installed

        Note, this will return results for the computer/container in which it is executed. To get the properties of
        a LabBook container, a docker exec command would be needed from the Gigantum application container.

        return format is a list of dicts with the format {name: <package name>, version: <version string>}

        Returns:
            list
        """
        raise NotImplemented

    @abc.abstractmethod
    def validate_packages(self, package_list: List[Dict[str, str]], labbook: LabBook, username: str) \
            -> List[PackageResult]:
        """Method to validate a list of packages, and if needed fill in any missing versions

        Should check both the provided package name and version. If the version is omitted, it should be generated
        from the latest version.

        Args:
            package_list(list): A list of dictionaries of packages to validate
            labbook(str): The labbook instance
            username(str): The username for the logged in user

        Returns:
            namedtuple: namedtuple indicating if the package and version are valid
        """
        raise NotImplemented

    @abc.abstractmethod
    def get_packages_metadata(self, package_list: List[str], labbook: LabBook, username: str) -> List[PackageMetadata]:
        """Method to get package metadata. Currently this is the latest version, description and a url for docs

        Args:
            package_list: List of package names
            labbook(str): The labbook instance
            username(str): The username for the logged in user

        Returns:
            list
        """
        raise NotImplemented

    @abc.abstractmethod
    def generate_docker_install_snippet(self, packages: List[Dict[str, str]], single_line: bool = False) -> List[str]:
        """Method to generate a docker snippet to install 1 or more packages

        Args:
            packages(list(dict)): A list of package names and versions to install
            single_line(bool): If true, collapse

        Returns:
            str
        """
        raise NotImplemented
