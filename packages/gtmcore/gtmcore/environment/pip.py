from typing import List, Dict, Optional
import requests
import json
from gtmcore.container.container import ContainerOperations
from gtmcore.labbook import LabBook
from gtmcore.http import ConcurrentRequestManager, ConcurrentRequest

from packaging import version

from gtmcore.environment.packagemanager import PackageManager, PackageResult, PackageMetadata


class PipPackageManager(PackageManager):
    """Class to implement the pip package manager
    """
    def __init__(self):
        self.request_mgr = ConcurrentRequestManager()

    def search(self, search_str: str, labbook: LabBook, username: str) -> List[str]:
        """Method to search a package manager for packages based on a string. The string can be a partial string.

        Args:
            search_str: The string to search on
            labbook: Subject LabBook
            username: username of current user

        Returns:
            list(str): The list of package names that match the search string
        """
        search_result = ContainerOperations.run_command(
            f'pip search {search_str}', labbook, username,
            fallback_image=self.fallback_image(labbook))

        lines = search_result.decode().splitlines()
        packages = [x.split(' ')[0] for x in lines]
        return sorted(packages)

    def _extract_versions(self, response: dict) -> List[str]:
        version_list = list(response["releases"].keys())

        # Don't include release candidates that have been pushed to pip
        version_list = [version.parse(v) for v in version_list if not version.parse(v).is_prerelease]

        # Sort and return
        version_list.sort(reverse=True)
        version_list = [str(v) for v in version_list]
        return version_list

    def list_versions(self, package_name: str, labbook: LabBook, username: str) -> List[str]:
        """Method to list all available versions of a package based on the package name

        Args:
            package_name: Name of the package to query
            labbook: Subject LabBook
            username: username of current user

        Returns:
            list(str): Version strings
        """
        url = f"https://pypi.python.org/pypi/{package_name}/json"
        result = requests.get(url)
        if result.status_code == 404:
            # Didn't find the package
            raise ValueError("Package not found in package index")
        if result.status_code != 200:
            raise IOError("Failed to query package index for package versions. Check internet connection.")

        return self._extract_versions(result.json())

    def list_installed_packages(self, labbook: LabBook, username: str) -> List[Dict[str, str]]:
        """Method to get a list of all packages that are currently installed

        Note, this will return results for the computer/container in which it is executed. To get the properties of
        a LabBook container, a docker exec command would be needed from the Gigantum application container.

        return format is a list of dicts with the format (name: <package name>, version: <version string>)

        Returns:
            list
        """
        packages = ContainerOperations.run_command('pip list --format=json', labbook, username,
                                                   fallback_image=self.fallback_image(labbook))
        return json.loads(packages.decode())

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
        result = list()

        # Run async version lookups
        request_list = list()
        for pkg in package_list:
            request_list.append(ConcurrentRequest(f"https://pypi.python.org/pypi/{pkg['package']}/json",
                                                  headers={'Accept': 'application/json'}))
        responses = self.request_mgr.resolve_many(request_list)

        for package, response in zip(package_list, responses):
            if response.status_code != 200:
                result.append(PackageResult(package=package['package'], version=package['version'], error=True))
                continue

            if package['version']:
                # Package has been set, so validate it
                if package['version'] in self._extract_versions(response.json):
                    # Both package name and version are valid
                    result.append(PackageResult(package=package['package'], version=package['version'], error=False))

                else:
                    # The package version is not in the list, so invalid
                    result.append(PackageResult(package=package['package'], version=package['version'], error=True))

            else:
                # You need to look up the latest version since not included
                result.append(PackageResult(package=package['package'], version=response.json['info']['version'],
                                            error=False))

        return result

    def get_packages_metadata(self, package_list: List[str], labbook: LabBook, username: str) -> List[PackageMetadata]:
        """Method to get package metadata

        Args:
            package_list: List of package names
            labbook(str): The labbook instance
            username(str): The username for the logged in user

        Returns:
            list
        """
        def _extract_metadata(data):
            """Extraction method to pull out the docs URL and description"""
            latest_val = None
            description_val = None
            docs_val = None

            info = data.get('info')
            if info:
                latest_val = info.get('version')
                description_val = info.get('summary').strip()
                docs_val = info.get('docs_url')

                if not docs_val:
                    docs_val = info.get('home_page')

            return latest_val, description_val, docs_val

        result = list()
        request_list = list()
        for pkg in package_list:
            request_list.append(ConcurrentRequest(f"https://pypi.python.org/pypi/{pkg}/json",
                                                  headers={'Accept': 'application/json'},
                                                  extraction_function=_extract_metadata))
        responses = self.request_mgr.resolve_many(request_list)
        for package, response in zip(package_list, responses):
            if response.status_code != 200:
                result.append(PackageMetadata(package_manager="pip", package=package, latest_version=None,
                                              description=None, docs_url=None))
            else:
                latest_version, description, docs_url = response.extracted_json
                result.append(PackageMetadata(package_manager="pip", package=package, latest_version=latest_version,
                                              description=description, docs_url=docs_url))

        return result

    def generate_docker_install_snippet(self, packages: List[Dict[str, str]], single_line: bool = False) -> List[str]:
        """Method to generate a docker snippet to install 1 or more packages

        Args:
             packages(list(dict)): A list of package names and versions to install
            single_line(bool): If true, collapse

        Returns:
            list
        """
        package_strings = [f"{x['name']}=={x['version']}" for x in packages]

        if single_line:
            return [f"RUN pip install {' '.join(package_strings)}"]
        else:
            docker_strings = [f"RUN pip install {x}" for x in package_strings]
            return docker_strings
