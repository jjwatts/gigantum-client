import os
import platform
import shutil
import sys

import yaml

from gtm.utils import dockerize_windows_path
from gtm.common.console import ask_question

CONFIG_FILE = os.path.expanduser("~/.gtm/config.yaml")


class UserConfig(object):
    """Class to manage configuring gtm for a user
    """
    def __init__(self):
        self.user_config = None

        self.resources_root = None
        self.compose_file_root = None
        self.gigantum_client_root = None

        if self.user_config:
            self.resources_root = os.path.join(self.user_config['root_dir'], 'resources')
            self.compose_file_root = os.path.join(self.resources_root, 'developer', 'docker_compose')

    @staticmethod
    def load_config_file():
        config_file_path = CONFIG_FILE
        if os.path.exists(config_file_path):
            with open(config_file_path, 'rt') as cf:
                data = yaml.load(cf)
            return data
        else:
            print("No gtm config file found. Run `gtm dev setup` to configure your environment")
            sys.exit(0)

    @staticmethod
    def save_config_file(data):
        config_file_path = CONFIG_FILE
        with open(config_file_path, 'wt') as cf:
            cf.write(yaml.dump(data, default_flow_style=False))

    @staticmethod
    def prompt_with_default(question: str, default: str) -> str:
        """

        Args:
            question:
            default:

        Returns:

        """
        print("{} [{}]: ".format(question, default), end="")
        choice = input().lower().strip()

        if not choice:
            choice = default

        return choice

    def update_template_data(self, is_windows: bool, use_pycharm: bool, is_backend: bool,
                             working_dir: str, uid: str) -> str:
        """Method to select a docker-compose template and update variables

        Args:
            is_windows:
            use_pycharm:
            working_dir:
            is_backend:
            uid:

        Returns:

        """
        if is_windows:
            if use_pycharm:
                template_file = os.path.join(self.compose_file_root, 'pycharm-windows.yml')
            elif is_backend is False:
                template_file = os.path.join(self.compose_file_root, 'shell-ui-windows.yml')
            else:
                template_file = os.path.join(self.compose_file_root, 'shell-windows.yml')
        else:
            if use_pycharm:
                template_file = os.path.join(self.compose_file_root, 'pycharm-nix.yml')
            elif is_backend is False:
                template_file = os.path.join(self.compose_file_root, 'shell-ui-nix.yml')
            else:
                template_file = os.path.join(self.compose_file_root, 'shell-nix.yml')

        # Load template
        with open(template_file, 'rt') as template:
            data = template.read()

        # Replace values
        # Note that different templates (chosen above) have a different number of variables. This is reflected in the
        # logic below.
        if is_windows:
            data = data.replace('{% WORKING_DIR %}', dockerize_windows_path(working_dir))
            if not use_pycharm:
                data = data.replace('{% GTM_DIR %}', dockerize_windows_path(self.user_config['root_dir']))
        else:
            data = data.replace('{% WORKING_DIR %}', working_dir)
            data = data.replace('{% USER_ID %}', str(uid))
            if not use_pycharm:
                data = data.replace('{% GTM_DIR %}', self.user_config['root_dir'])

        data = data.replace('{% HELPER_SCRIPT %}',
                            os.path.join(self.gigantum_client_root, 'build', 'developer', 'setup.sh'))

        return data

    def write_helper_script(self):
        """Write a helper script for shell developers"""

        # newline to output files with unix line endings on all platforms
        with open(os.path.join(self.gigantum_client_root, 'build', 'developer', 'setup.sh'),
                  'wt', newline='\n') as template:
            script = """#!/bin/bash
export PYTHONPATH=$PYTHONPATH:/opt/project/packages/gtmcore
export JUPYTER_RUNTIME_DIR=/mnt/share
cd /opt/project/packages/gtmapi
su giguser
            """

            template.write(script)

    def configure(self) -> None:
        """Method to configure gtm for building and using dev containers

        Returns:
            None
        """
        # Check if *nix or windows
        if platform.system() == 'Windows':
            is_windows = True
        else:
            is_windows = False

        # Check if doing frontend or backend dev
        is_backend = ask_question("I want to configure gtm for BACKEND development ('n' for frontend)")
        use_pycharm = False
        import_run_configs = False
        if is_backend:
            # If backend, check if using pycharm
            use_pycharm = ask_question("I want to use PYCHARM for development")
            if use_pycharm:
                # If using pycharm, check if user wants to import run configurations
                import_run_configs = ask_question("I want to import run configurations into my `gtm` PyCharm project")

        # Prompt for working dir
        # TODO: Check that this path is actually mounted inside Moby (or whatever the root VM is called)
        working_dir = self.prompt_with_default("Gigantum Working Directory",
                                               os.path.expanduser(os.path.join("~", 'gigantum')))

        # Prompt for UID if needed
        uid = None
        if not is_windows:
            # Set user id
            uid = self.prompt_with_default("Desired User ID", os.getuid())

        gigantum_client_root = input("Path to the gigantum-client repository: ")
        gigantum_client_root = os.path.expanduser(gigantum_client_root)

        # Save our answers
        answer_fname = CONFIG_FILE
        if os.path.exists(os.path.dirname(answer_fname)) is False:
            os.makedirs(os.path.dirname(answer_fname))

        answers = {'is_windows':  is_windows,
                   'is_backend':  is_backend,
                   'use_pycharm': use_pycharm,
                   'working_dir': working_dir,
                   'root_dir': gigantum_client_root,
                   'uid':         uid}
        self.save_config_file(answers)
        self.user_config = self.load_config_file()

        self.gigantum_client_root = gigantum_client_root
        self.resources_root = os.path.join(gigantum_client_root, 'resources')
        self.compose_file_root = os.path.join(self.resources_root, 'developer', 'docker_compose')

        print("Configuration saved to {}".format(answer_fname))

        # Get template text and update with variables
        template_data = self.update_template_data(is_windows, use_pycharm, is_backend, working_dir, uid)

        # Generate docker-compose file
        developer_build_dir = os.path.join(self.gigantum_client_root, 'build', 'developer')
        if os.path.exists(developer_build_dir) is False:
            os.makedirs(developer_build_dir)
        else:
            shutil.rmtree(developer_build_dir)
            os.makedirs(developer_build_dir)

        output_file = os.path.join(developer_build_dir, 'docker-compose.yml')
        with open(output_file, 'wt') as out_file:
            out_file.write(template_data)

        print("Docker Compose file written to {}".format(output_file))

        # Generate supervisord.conf
        if is_backend:
            supervisord_file = os.path.join(self.resources_root, 'developer', 'supervisord_backend.conf')
        else:
            supervisord_file = os.path.join(self.resources_root, 'developer', 'supervisord_frontend.conf')

        shutil.copyfile(supervisord_file, os.path.join(self.gigantum_client_root, 'build', 'developer',
                                                       'supervisord.conf'))
        # Write shell helper script
        self.write_helper_script()

        # Import run configs if needed
        if import_run_configs:
            src_run_config_dir = os.path.join(self.resources_root, 'developer', 'pycharm_run_configurations')
            run_config_dir = os.path.join(self.gigantum_client_root, '.idea', 'runConfigurations')
            # This directory does not exist by default if no configurations have been defined yet
            # (at least on Windows 10 / PyCharm 2017.3.2)
            os.makedirs(run_config_dir, exist_ok=True)

            files = os.listdir(src_run_config_dir)
            for file in files:
                src_file = os.path.join(src_run_config_dir, file)
                if os.path.isfile(src_file):
                    shutil.copy(src_file, os.path.join(run_config_dir, file))

            print("Run configurations copied to `.idea/runConfigurations`. Restart PyCharm if running")


def get_client_root():
    return UserConfig.load_config_file().get('root_dir')


def get_resources_root():
    return os.path.join(get_client_root(), "resources")
