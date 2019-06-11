from typing import (List, Dict, Optional)

from gtmcore.environment.packagemanager import PackageManager, PackageResult, PackageMetadata
from gtmcore.container.container import ContainerOperations
from gtmcore.labbook import LabBook
from gtmcore.logging import LMLogger

logger = LMLogger.get_logger()


class AptPackageManager(PackageManager):
    """Class to implement the apt package manager

    Note: apt is somewhat limiting in the ability to access old versions of packages
    """

    def search(self, search_str: str, labbook: LabBook, username: str) -> List[str]:
        """Method to search a package manager for packages based on a string. The string can be a partial string.

        Args:
            search_str: The string to search on
            labbook: Subject LabBook
            username: username of current user

        Returns:
            list(str): The list of package names that match the search string
        """
        result = ContainerOperations.run_command(f"apt-cache search {search_str}", labbook, username,
                                                 fallback_image=self.fallback_image(labbook))

        packages = []
        if result:
            lines = result.decode('utf-8').split('\n')
            for l in lines:
                if l:
                    packages.append(l.split(" - ")[0])

        return packages

    def list_versions(self, package_name: str, labbook: LabBook, username: str) -> List[str]:
        """Method to list all available versions of a package based on the package name

        Args:
            package_name: Name of the package to query
            labbook: Subject LabBook
            username: Username of current user

        Returns:
            list(str): Version strings
        """
        result = ContainerOperations.run_command(f"apt-cache madison {package_name}", labbook, username,
                                                 override_image_tag=self.fallback_image(labbook))

        package_versions: List[str] = []
        if result:
            lines = result.decode('utf-8').split('\n')
            for l in lines:
                if l:
                    parts = l.split(" | ")
                    if parts[1] not in package_versions:
                        package_versions.append(parts[1].strip())
        else:
            raise ValueError(f"Package {package_name} not found in apt.")

        return package_versions

    def list_installed_packages(self, labbook: LabBook, username: str) -> List[Dict[str, str]]:
        """Method to get a list of all packages that are currently installed

        Note, this will return results for the computer/container in which it is executed. To get the properties of
        a LabBook container, a docker exec command would be needed from the Gigantum application container.

        return format is a list of dicts with the format (name: <package name>, version: <version string>)

        Returns:
            list
        """
        result = ContainerOperations.run_command("apt list --installed", labbook, username,
                                                 fallback_image=self.fallback_image(labbook))

        packages = []
        if result:
            lines = result.decode('utf-8').split('\n')
            for line in lines:
                if line is not None and line != "Listing..." and "/" in line:
                    parts = line.split(" ")
                    package_name, _ = parts[0].split("/")
                    version = parts[1].strip()
                    packages.append({'name': package_name, 'version': version})

        return packages

    def validate_packages(self, package_list: List[Dict[str, str]], labbook: LabBook, username: str) \
            -> List[PackageResult]:
        """Method to validate a list of packages, and if needed fill in any missing versions

        Should check both the provided package name and version. If the version is omitted, it should be generated
        from the latest version.

        Args:
            package_list: A list of dictionaries of packages to validate
            labbook: The labbook instance
            username: The username for the logged in user

        Returns:
            namedtuple: namedtuple indicating if the package and version are valid
        """
        result = list()
        for package in package_list:
            pkg_result = PackageResult(package=package['package'], version=package.get('version'), error=True)

            try:
                version_list = self.list_versions(package['package'], labbook, username)
            except ValueError:
                result.append(pkg_result)
                continue

            if not version_list:
                # If here, no versions found for the package...so invalid
                result.append(pkg_result)
            else:
                if package.get('version'):
                    if package.get('version') in version_list:
                        # Both package name and version are valid
                        result.append(PackageResult(package=package['package'],
                                                    version=package.get('version'),
                                                    error=False))

                    else:
                        # The package version is not in the list, so invalid
                        result.append(pkg_result)

                else:
                    # You need to set the latest version
                    result.append(PackageResult(package=package['package'],
                                                version=version_list[0],
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
        results = list()
        for package in package_list:
            result = ContainerOperations.run_command(f"apt-cache search {package}", labbook, username,
                                                     fallback_image=self.fallback_image(labbook))
            description = None
            latest_version = None
            if result:
                lines = result.decode('utf-8').split('\n')
                for l in lines:
                    if l:
                        pkg_name, pkg_description = l.split(" - ")
                        if pkg_name == package:
                            description = pkg_description.strip()
                            break

            # Get the latest version of the package
            try:
                versions = self.list_versions(package, labbook, username)
                if versions:
                    latest_version = versions[0]
            except ValueError:
                # If package isn't found, just set to None
                pass

            results.append(PackageMetadata(package_manager="apt", package=package, latest_version=latest_version,
                                           description=description, docs_url=None))

        return results

    def generate_docker_install_snippet(self, packages: List[Dict[str, str]], single_line: bool = False) -> List[str]:
        """Method to generate a docker snippet to install 1 or more packages

        Args:
            packages(list(dict)): A list of package names and versions to install
            single_line(bool): If true, collapse

        Returns:
            list
        """
        package_strings = [f"{x['name']}" for x in packages]

        if single_line:
            return [f"RUN apt-get -y --no-install-recommends install {' '.join(package_strings)}"]
        else:
            docker_strings = [f"RUN apt-get -y --no-install-recommends install {x}" for x in package_strings]
            return docker_strings
