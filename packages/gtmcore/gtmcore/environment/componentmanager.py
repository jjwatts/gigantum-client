from pathlib import Path

import datetime
import os
import yaml
from typing import (Any, List, Dict, Tuple)
import glob

from typing import Optional


from gtmcore.labbook import LabBook
from gtmcore.environment.repository import BaseRepository  # type: ignore
from gtmcore.logging import LMLogger
from gtmcore.activity import ActivityStore, ActivityType, ActivityRecord, ActivityDetailType, ActivityDetailRecord, \
    ActivityAction
from gtmcore.labbook.schemas import CURRENT_SCHEMA

logger = LMLogger.get_logger()

PROJECT_ENTRYPOINT = \
"""#!/bin/bash

USER_ID=${LOCAL_USER_ID:-9001}

echo "Starting with UID: $USER_ID"
useradd --shell /bin/bash -u $USER_ID -o -c "" -m giguser
export HOME=/home/giguser

# Setup /mnt/ as a safe place to put user runnable code
mkdir /mnt/labbook
chown -R giguser:root /mnt/labbook

# Setup docker sock to run as the user
chown giguser:root /run/docker.sock
chmod 777 /var/run/docker.sock

export JUPYTER_RUNTIME_DIR=/mnt/share/jupyter/runtime
chown -R giguser:root /mnt/share/

# Run the Docker Command
exec gosu giguser "$@"
"""

def strip_package_and_version(package_manager: str, package_str: str) -> Tuple[str, Optional[str]]:
    """For a particular package encoded with version, this strips off the version and returns a tuple
    containing (package-name, version). If version is not specified, it is None.
    """
    if package_manager not in ['pip3', 'pip2', 'pip', 'apt', 'conda', 'conda2', 'conda3']:
        raise ValueError(f'Unsupported package manager: {package_manager}')

    if package_manager in ['pip', 'pip2', 'pip3']:
        if '==' in package_str:
            t = package_str.split('==')
            return t[0], t[1]
        else:
            return package_str, None

    if package_manager == 'apt' or package_manager in ['conda', 'conda2', 'conda3']:
        if '=' in package_str:
            t = package_str.split('=')
            return t[0], t[1]
        else:
            return package_str, None

    raise ValueError(f'Unsupported package manager: {package_manager}')


class ComponentManager(object):
    """Class to manage the Environment Components of a given LabBook
    """

    DEFAULT_CUSTOM_DOCKER_NAME = 'user-custom-docker'

    def __init__(self, labbook: LabBook) -> None:
        """Constructor

        Args:
            labbook(LabBook): A gtmcore.labbook.LabBook instance for the LabBook you wish to manage
        """
        # Save labbook instance
        self.labbook = labbook
        # Create a base repo instance using the same config file
        self.bases = BaseRepository(config_file=self.labbook.client_config.config_file)
        # Make sure the LabBook's environment directory is ready to go
        self._initialize_env_dir()

    @property
    # This could be converted to return a Path, which would be a bit more ergonomic
    # Probably not worth the effort unless we're doing a refactor
    def env_dir(self) -> str:
        """The environment directory in the given labbook"""
        return os.path.join(self.labbook.root_dir, '.gigantum', 'env')

    def _initialize_env_dir(self) -> None:
        """Method to populate the environment directory if any content is missing

        Returns:
            None
        """
        # Create/validate directory structure
        subdirs = ['base',
                   'package_manager',
                   'custom',
                   'docker']

        for subdir in subdirs:
            os.makedirs(os.path.join(self.env_dir, subdir), exist_ok=True)

        # Add entrypoint.sh file if missing
        entrypoint_file = os.path.join(self.env_dir, 'entrypoint.sh')
        if os.path.exists(entrypoint_file) is False:
            with open(entrypoint_file, 'wt') as ef:
                ef.write(PROJECT_ENTRYPOINT)

            short_message = "Adding missing entrypoint.sh, required for container automation"
            self.labbook.git.add(entrypoint_file)
            self.labbook.git.commit(short_message)

    def add_docker_snippet(self, name: str, docker_content: List[str], description: Optional[str] = None) -> None:
        """ Add a custom docker snippet to the environment (replacing custom dependency).

        Args:
            name: Name or identifier of the custom docker snippet
            docker_content: Content of the docker material (May make this a list of strings instead)
            description: Human-readable verbose description of what the snippet is intended to accomplish.

        Returns:
            None
        """

        if not name:
            raise ValueError('Argument `name` cannot be None or empty')

        if not name.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Argument `name` must be alphanumeric string (- and _ accepted)')

        if not docker_content:
            docker_content = []

        file_data = {
            'name': name,
            'timestamp_utc': datetime.datetime.utcnow().isoformat(),
            'description': description or "",
            'content': docker_content
        }

        docker_dir = os.path.join(self.labbook.root_dir, '.gigantum', 'env', 'docker')
        docker_file = os.path.join(docker_dir, f'{name}.yaml')
        os.makedirs(docker_dir, exist_ok=True)
        yaml_dump = yaml.safe_dump(file_data, default_flow_style=False)
        with open(docker_file, 'w') as df:
            df.write(yaml_dump)

        logger.info(f"Wrote custom Docker snippet `{name}` to {str(self.labbook)}")
        short_message = f"Wrote custom Docker snippet `{name}`"
        self.labbook.git.add(docker_file)
        commit = self.labbook.git.commit(short_message)
        adr = ActivityDetailRecord(ActivityDetailType.ENVIRONMENT, show=False, action=ActivityAction.CREATE)
        adr.add_value('text/plain', '\n'.join(docker_content))
        ar = ActivityRecord(ActivityType.ENVIRONMENT,
                            message=short_message,
                            show=True,
                            linked_commit=commit.hexsha,
                            tags=["environment", "docker", "snippet"])
        ar.add_detail_object(adr)
        ars = ActivityStore(self.labbook)
        ars.create_activity_record(ar)

    def remove_docker_snippet(self, name: str) -> None:
        """Remove a custom docker snippet

        Args:
            name: Name or identifer of snippet to remove

        Returns:
            None
        """
        docker_dir = os.path.join(self.labbook.root_dir, '.gigantum', 'env', 'docker')
        docker_file = os.path.join(docker_dir, f'{name}.yaml')

        if not os.path.exists(docker_file):
            raise ValueError(f'Docker snippet name `{name}` does not exist')

        self.labbook.git.remove(docker_file, keep_file=False)
        short_message = f"Removed custom Docker snippet `{name}`"
        logger.info(short_message)
        commit = self.labbook.git.commit(short_message)
        adr = ActivityDetailRecord(ActivityDetailType.ENVIRONMENT, show=False, action=ActivityAction.DELETE)
        adr.add_value('text/plain', short_message)
        ar = ActivityRecord(ActivityType.ENVIRONMENT,
                            message=short_message,
                            show=False,
                            linked_commit=commit.hexsha,
                            tags=["environment", "docker", "snippet"])
        ar.add_detail_object(adr)
        ars = ActivityStore(self.labbook)
        ars.create_activity_record(ar)

    def add_packages(self, package_manager: str, packages: List[dict],
                     force: bool = False, from_base: bool = False) -> None:
        """Add a new yaml file describing the new package and its context to the labbook.

        Args:
            package_manager: The package manager (eg., "apt" or "pip3")
            packages: A dictionary of packages to install (package & version are main keys needed)
            force: Force overwriting a component if it already exists (e.g. you want to update the version)
            from_base: If a package in a base image, not deletable. Otherwise, can be deleted by LB user.

        Returns:
            None
        """
        if not package_manager:
            raise ValueError('Argument package_manager cannot be None or empty')

        # Create activity record
        ar = ActivityRecord(ActivityType.ENVIRONMENT,
                            show=True,
                            message="",
                            linked_commit="",
                            tags=["environment", 'package_manager', package_manager])

        update_cnt = 0
        add_cnt = 0
        for pkg in packages:
            version_str = f'"{pkg["version"]}"' if pkg["version"] else 'latest'

            yaml_lines = [f'# Generated on: {datetime.datetime.now()}',
                          f'manager: "{package_manager}"',
                          f'package: "{pkg["package"]}"',
                          f'version: {version_str}',
                          f'from_base: {str(from_base).lower()}',
                          f'schema: {CURRENT_SCHEMA}']
            yaml_filename = f'{package_manager}_{pkg["package"]}.yaml'
            package_yaml_path = os.path.join(self.env_dir, 'package_manager', yaml_filename)

            # Check if package already exists
            if os.path.exists(package_yaml_path):
                if force:
                    # You are updating, since force is set and package already exists.
                    logger.warning("Updating package file at {}".format(package_yaml_path))
                    detail_msg = "Update {} managed package: {} {}".format(package_manager, pkg["package"], version_str)
                    adr = ActivityDetailRecord(ActivityDetailType.ENVIRONMENT, show=False, action=ActivityAction.EDIT)
                    update_cnt += 1
                else:
                    raise ValueError("The package {} already exists in this LabBook.".format(pkg["package"]) +
                                     " Use `force` to overwrite")
            else:
                add_cnt += 1
                detail_msg = "Add {} managed package: {} {}".format(package_manager, pkg["package"], version_str)
                adr = ActivityDetailRecord(ActivityDetailType.ENVIRONMENT, show=False, action=ActivityAction.CREATE)

            # Write the YAML to the file
            with open(package_yaml_path, 'w') as package_yaml_file:
                package_yaml_file.write(os.linesep.join(yaml_lines))

            # Create activity record
            adr.add_value('text/plain', detail_msg)
            ar.add_detail_object(adr)
            logger.info("Added package {} to labbook at {}".format(pkg["package"], self.labbook.root_dir))

        # Set activity message
        ar_msg = ""
        if add_cnt > 0:
            ar_msg = f"Added {add_cnt} {package_manager} package(s). "

        if update_cnt > 0:
            ar_msg = f"{ar_msg}Updated {update_cnt} {package_manager} package(s)"

        # Add to git
        self.labbook.git.add_all(self.env_dir)
        commit = self.labbook.git.commit(ar_msg)
        ar.linked_commit = commit.hexsha
        ar.message = ar_msg

        # Store
        ars = ActivityStore(self.labbook)
        ars.create_activity_record(ar)

    def remove_packages(self, package_manager: str, package_names: List[str]) -> None:
        """Remove yaml files describing a package and its context to the labbook.

        Args:
            package_manager: The package manager (eg., "apt" or "pip3")
            package_names: A list of packages to uninstall

        Returns:
            None
        """
        # Create activity record
        ar = ActivityRecord(ActivityType.ENVIRONMENT,
                            message="",
                            show=True,
                            linked_commit="",
                            tags=["environment", 'package_manager', package_manager])

        for pkg in package_names:
            yaml_filename = '{}_{}.yaml'.format(package_manager, pkg)
            package_yaml_path = os.path.join(self.env_dir, 'package_manager', yaml_filename)

            # Check for package to exist
            if not os.path.exists(package_yaml_path):
                raise ValueError(f"{package_manager} installed package {pkg} does not exist.")

            # Check to make sure package isn't from the base. You cannot remove packages from the base yet.
            with open(package_yaml_path, 'rt') as cf:
                package_data = yaml.safe_load(cf)

            if not package_data:
                raise IOError("Failed to load package description")

            if package_data['from_base'] is True:
                raise ValueError("Cannot remove a package installed in the Base")

            # Delete the yaml file, which on next Dockerfile gen/rebuild will remove the dependency
            os.remove(package_yaml_path)
            if os.path.exists(package_yaml_path):
                raise ValueError(f"Failed to remove package.")

            self.labbook.git.remove(package_yaml_path)

            # Create detail record
            adr = ActivityDetailRecord(ActivityDetailType.ENVIRONMENT, show=False, action=ActivityAction.DELETE)
            adr.add_value('text/plain', f"Removed {package_manager} managed package: {pkg}")
            ar.add_detail_object(adr)
            logger.info(f"Removed {package_manager} managed package: {pkg}")

        # Add to git
        short_message = f"Removed {len(package_names)} {package_manager} managed package(s)"
        commit = self.labbook.git.commit(short_message)
        ar.linked_commit = commit.hexsha
        ar.message = short_message

        # Store
        ars = ActivityStore(self.labbook)
        ars.create_activity_record(ar)

    def add_base(self, repository: str, base_id: str, revision: int) -> None:
        """Method to add a base to a LabBook's environment

        Note that if this is run after packages have been configured, it will leave user-specified packages alone (and
        not override them with the base-installed package) even if the base provides a newer version of the  package.

        Args:
            repository: The Environment Component repository the component is in
            base_id: The name of the component
            revision: The revision to use, specified *inside* yaml file.

        Returns:
            None
        """
        if not repository:
            raise ValueError('repository cannot be None or empty')

        if not base_id:
            raise ValueError('component cannot be None or empty')

        # Get the base
        base_data = self.bases.get_base(repository, base_id, revision)
        base_filename = f"{repository}_{base_id}.yaml"
        base_final_path = os.path.join(self.env_dir, 'base', base_filename)

        short_message = f"Added base: {base_id} r{revision}"
        # Count number of YAML files in our base dir - should be 0
        existing_bases = sum(1 for base_path in Path(self.env_dir, 'base').iterdir()
                             if base_path.suffix == '.yaml')
        if existing_bases:
            # This shouldn't ever happen - but we don't trust the front-end
            raise ValueError(f"Found {existing_bases} base(s) already in this project")

        with open(base_final_path, 'wt') as cf:
            cf.write(yaml.safe_dump(base_data, default_flow_style=False))

        # We construct a
        installed_packages = {}
        for package in self.get_component_list("package_manager"):
            # Build dictionary of packages
            if package['from_base']:
                # We are removing the base - so the package isn't guaranteed
                installed_packages.setdefault(package['manager'], []).append(package["package"])

        for manager in base_data['package_managers']:
            packages = list()
            # Build dictionary of packages
            for p_manager in manager.keys():
                if manager[p_manager]:
                    for pkg in manager[p_manager]:
                        pkg_name, pkg_version = strip_package_and_version(p_manager, pkg)
                        if pkg_name in installed_packages.get(p_manager, []):
                            # If package is already installed by this package manager, we expect it gets overwritten
                            # If it's a different package manger, it won't! We may want to alert the user, but how?
                            continue
                        packages.append({"package": pkg_name, "version": pkg_version, "manager": p_manager})

                    self.add_packages(package_manager=p_manager, packages=packages,
                                      force=True, from_base=True)

        self.labbook.git.add(base_final_path)
        commit = self.labbook.git.commit(short_message)
        logger.info(f"Added base from {repository}: {base_id} rev{revision}")

        # Create a ActivityRecord
        long_message = "\n".join((f"Added base {base_id}\n",
                                  f"{base_data['description']}\n",
                                  f"  - repository: {repository}",
                                  f"  - component: {base_id}",
                                  f"  - revision: {revision}"))

        # Create detail record
        adr = ActivityDetailRecord(ActivityDetailType.ENVIRONMENT, show=False, action=ActivityAction.CREATE)
        adr.add_value('text/plain', long_message)

        # Create activity record
        ar = ActivityRecord(ActivityType.ENVIRONMENT,
                            message=short_message,
                            linked_commit=commit.hexsha,
                            tags=["environment", "base"],
                            show=True)
        ar.add_detail_object(adr)

        # Store
        ars = ActivityStore(self.labbook)
        ars.create_activity_record(ar)

    def change_base(self, repository: str, base_id: str, revision: int) -> None:
        """Delete existing base, create an activity record, call add_base

        Note that all packages that were installed by the current base will be removed from the environment (in
        env/package_manager). Even if the new base installs a newer version of a user-installed package,
        that package will remain in effect - this avoids actively breaking a working package selection and is easy
        enough for a user to update.

        In case it's useful, this method is robust to multiple base images (this might happen, for example, after a
        merge). If multiple base image files are found, all will be removed prior to installing the specified base.

        Args:
             repository: name of git repo for base images, e.g. 'gigantum_base-images'
             base_id: name of base image, e.g. 'python3-minimal'
             revision: The revision number specified INSIDE the YAML file for that base image
        """
        # We'll populate detail records as we go
        detail_records = []

        current_base_dir = Path(self.env_dir) / "base"
        matching_fnames = list(current_base_dir.glob('*.yaml'))

        if len(matching_fnames) != 1:
            # The project is misconfigured with more than one base. Let's fix that.
            logger.warning(f"Project misconfigured. Found {len(matching_fnames)} base configuration files.")
            short_message = f"Removing all bases from project with {len(matching_fnames)} base configuration files."
            for base_fname in matching_fnames:
                self.labbook.git.remove(str(base_fname), keep_file=False)
                # XXX DC delete before merge!
                assert not base_fname.exists()
                # The repository includes an underscore where the slash is for e.g.,
                # .gigantum/env/base/gigantum_base-images_r-tidyverse.yaml
                curr_repo, curr_base_name = base_fname.stem.rsplit('_', 1)
                long_message = f"Removing base from {curr_repo}: {curr_base_name} r{curr_revision}"

                # Create detail record
                adr = ActivityDetailRecord(ActivityDetailType.ENVIRONMENT, show=False, action=ActivityAction.CREATE)
                adr.add_value('text/plain', long_message)
                detail_records.append(adr)

        else:
            base_fname = matching_fnames[0]

            # We have a properly configured Labbook, and we report more detail
            base_data = self.base_fields
            curr_revision = base_data['revision']

            # The repository includes an underscore where the slash is for e.g.,
            # .gigantum/env/base/gigantum_base-images_r-tidyverse.yaml
            curr_repo, curr_base_name = base_fname.stem.rsplit('_', 1)

            short_message = f"Removed base from {curr_repo}: {curr_base_name} r{curr_revision}"

            self.labbook.git.remove(str(base_fname), keep_file=False)
            # XXX DC delete before merge
            assert not base_fname.exists()
            logger.info(short_message)

            long_message = "\n".join((f"Removed base {base_id}\n",
                                      f"{base_data['description']}\n",
                                      f"  - repository: {repository}",
                                      f"  - component: {base_id}",
                                      f"  - revision: {revision}"))

            # Create detail record
            adr = ActivityDetailRecord(ActivityDetailType.ENVIRONMENT, show=False, action=ActivityAction.CREATE)
            adr.add_value('text/plain', long_message)
            detail_records.append(adr)

        commit = self.labbook.git.commit(short_message)

        # Create activity record - we populated detail_records above
        ar = ActivityRecord(ActivityType.ENVIRONMENT,
                            message=short_message,
                            linked_commit=commit.hexsha,
                            tags=["environment", "base"],
                            show=True)

        for adr in detail_records:
            ar.add_detail_object(adr)

        # Store the activity record.
        ars = ActivityStore(self.labbook)
        ars.create_activity_record(ar)

        packages_to_rm = {}
        for package in self.get_component_list("package_manager"):
            # Build dictionary of packages
            if package['from_base']:
                # We are removing the base - so the package isn't guaranteed
                packages_to_rm.setdefault(package['manager'], []).append(package["package"])

        for p_manager, package_names in packages_to_rm.items():
            # Package removal will also create activity records
            self.remove_packages(p_manager, package_names)

        # add_base currently returns None, but this will incorporate any future changes
        return self.add_base(repository, base_id, revision)

    def get_component_list(self, component_class: str) -> List[Dict[str, Any]]:
        """Method to get the YAML contents for a given component class

        Args:
            component_class(str): The class of component you want to access

        Returns:
            list
        """
        # Get component dir
        component_dir = os.path.join(self.env_dir, component_class)
        if not os.path.exists(component_dir):
            raise ValueError("No components found for component class: {}".format(component_class))

        # Get all YAML files in dir
        yaml_files = glob.glob(os.path.join(component_dir, "*.yaml"))
        yaml_files = sorted(yaml_files)
        data = []

        # Read YAML files and write data to dictionary
        for yf in yaml_files:
            with open(yf, 'rt') as yf_file:
                yaml_data = yaml.safe_load(yf_file)
                data.append(yaml_data)
        return sorted(data, key=lambda elt: elt.get('id') or elt.get('manager'))

    @property
    def base_fields(self) -> Dict[str, Any]:
        """Load the base data for this LabBook from disk"""
        base_yaml_file = glob.glob(os.path.join(self.env_dir, 'base', '*.yaml'))

        if len(base_yaml_file) != 1:
            raise ValueError(f"Project misconfigured. Found {len(base_yaml_file)} base configurations.")

        # If you got 1 base, load from disk
        with open(base_yaml_file[0], 'rt') as bf:
            data = yaml.safe_load(bf)

        return data
