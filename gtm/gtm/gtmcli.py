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
import argparse
import sys
import os

from gtm import client
from gtm import circleci
from gtm.common.logreader import show_log
from gtm import common
from gtm.client.dev import DevClientRunner


def format_action_help(actions):
    """Method to format a help string for actions in a component

    Args:
        actions(list): list of supported actions

    Returns:
        str
    """
    response = ""
    for action in actions:
        response = "{}      {}: {}\n".format(response, action[0], action[1])

    return response


def format_component_help(components):
    """Method to format a help string for all the components

    Args:
        components(dict): Dictionary of supported components

    Returns:
        str
    """
    response = ""
    for component in components:
        response = "{}  {}\n{}".format(response, component, format_action_help(components[component]))

    return response


def client_actions(args):
    """Method to provide logic and perform actions for building and client containers

    Args:
        args(Namespace): Parsed arguments

    Returns:
        None
    """
    builder = client.build.ClientBuilder("gigantum/labmanager")
    if "override_name" in args:
        if args.override_name:
            builder.image_name = args.override_name

    if args.action == "build":
        build_args = {"build_dir": os.path.join("build", "client"),
                      "supervisor_file": os.path.join("resources", "client", "supervisord-local.conf"),
                      "config_override_file": os.path.join("resources", "client",
                                                           "labmanager-config-override.yaml")}

        docker_args = {"CLIENT_CONFIG_FILE": os.path.join(build_args['build_dir'], "labmanager-config.yaml"),
                       "NGINX_UI_CONFIG": "resources/client/nginx_ui.conf",
                       "NGINX_API_CONFIG": "resources/client/nginx_api.conf",
                       "SUPERVISOR_CONFIG": os.path.join(build_args['build_dir'], "supervisord.conf"),
                       "ENTRYPOINT_FILE": "resources/client/entrypoint.sh"}

        builder.write_empty_testing_requirements_file()
        builder.build_image(no_cache=args.no_cache, build_args=build_args, docker_args=docker_args)

        # Print Name of image
        print("\n\n*** Built Gigantum Client Image: {}\n".format(builder.image_name))

    elif args.action == "publish":
        image_tag = None
        builder.publish(image_tag=image_tag, verbose=args.verbose)

        # Print Name of image
        if not image_tag:
            image_tag = "latest"
        print("\n\n*** Published Gigantum Client Image: gigantum/labmanager:{}\n".format(image_tag))

    elif args.action == "publish-edge":
        image_tag = None
        if "override_name" in args:
            if args.override_name:
                image_tag = args.override_name

        builder.publish_edge(image_tag=image_tag, verbose=args.verbose)

        # Print Name of image
        if not image_tag:
            image_tag = "latest"
        print("\n\n*** Published Gigantum Client Edge Image: gigantum/labmanager-edge:{}\n".format(image_tag))

    elif args.action == "prune":
        builder.cleanup("gigantum/labmanager")

    elif args.action == "prune-edge":
        builder.cleanup("gigantum/labmanager-edge")

    elif args.action == "run":
        print("Error: Unsupported action provided: `{}`. Did you mean `start`?".format(args.action), file=sys.stderr)
        sys.exit(1)
    elif args.action == "log":
        show_log()
    elif args.action == "start" or args.action == "stop":
        # If not a tagged version, force to latest
        if ":" not in builder.image_name:
            image_name = "{}:latest".format(builder.image_name)
        else:
            image_name = builder.image_name

        launcher = client.run.ClientRunner(image_name=image_name, container_name=builder.container_name,
                                           show_output=args.verbose)

        if args.action == "start":
            if not launcher.is_running:
                launcher.launch()
                print("*** Ran: {}".format(image_name))
            else:
                print("Error: Docker container by name `{}' is already started.".format(builder.image_name), file=sys.stderr)
                sys.exit(1)
        elif args.action == "stop":
            remove_all = False
            if "all" in args:
                remove_all = args.all

            launcher.stop(remove_all=remove_all)

    elif args.action == "test":
        tester = client.test.LabManagerTester(builder.container_name)
        tester.test()
    else:
        print("Error: Unsupported action provided: `{}`".format(args.action), file=sys.stderr)
        sys.exit(1)


def demo_actions(args):
    """Method to provide logic and perform actions for the LabManager component

    Args:
        args(Namespace): Parsed arguments

    Returns:
        None
    """

    builder = client.build.ClientBuilder("gigantum/gigantum-cloud-demo")
    if "override_name" in args:
        if args.override_name:
            builder.image_name = args.override_name

    if args.action == "build":

        build_args = {"build_dir": os.path.join("build", "demo"),
                      "supervisor_file": os.path.join("resources", "client", "supervisord-demo.conf"),
                      "config_override_file": os.path.join("resources", "client",
                                                           "demo-config-override.yaml")}

        docker_args = {"CLIENT_CONFIG_FILE": os.path.join(build_args['build_dir'], "labmanager-config.yaml"),
                       "NGINX_UI_CONFIG": "resources/client/nginx_ui.conf",
                       "NGINX_API_CONFIG": "resources/client/nginx_api.conf",
                       "SUPERVISOR_CONFIG": os.path.join(build_args['build_dir'], "supervisord.conf"),
                       "ENTRYPOINT_FILE": "resources/client/entrypoint.sh"}

        builder.write_empty_testing_requirements_file()

        builder.build_image(no_cache=args.no_cache, build_args=build_args, docker_args=docker_args)

        # Print Name of image
        print("\n\n*** Built LabManager Image with Demo configuration: {}\n".format(builder.image_name))

    elif args.action == "publish":
        image_tag = None
        if "override_name" in args:
            if args.override_name:
                image_tag = args.override_name

        builder.publish(image_tag=image_tag, verbose=args.verbose)

        # Print Name of image
        if not image_tag:
            image_tag = "latest"
        print("\n\n*** Published Demo Image: gigantum/gigantum-cloud-demo:{}\n".format(image_tag))

    elif args.action == "prune":
        builder.cleanup("gigantum/gigantum-cloud-demo")

    else:
        print("Error: Unsupported action provided: `{}`".format(args.action), file=sys.stderr)
        sys.exit(1)


def developer_actions(args):
    """Method to provide logic and perform actions for the developer component

    Args:
        args(Namespace): Parsed arguments

    Returns:
        None
    """
    dc = common.config.UserConfig()
    builder = client.build.ClientBuilder("gigantum/labmanager-dev")

    if args.action == "build":
        if "override_name" in args:
            if args.override_name:
                builder.image_name = args.override_name

        # Based on developer config, set variables
        config = dc.load_config_file()
        build_args = {"build_dir": os.path.join("build", "developer"),
                      "config_override_file": os.path.join("resources", "developer",
                                                           "labmanager-config-override.yaml")}

        docker_args = {"CLIENT_CONFIG_FILE": os.path.join(build_args['build_dir'], "labmanager-config.yaml"),
                       "NGINX_UI_CONFIG": "resources/client/nginx_null",
                       "NGINX_API_CONFIG": "resources/client/nginx_null",
                       "SUPERVISOR_CONFIG": os.path.join(build_args['build_dir'], "supervisord.conf"),
                       "ENTRYPOINT_FILE": "resources/developer/entrypoint.sh"}

        if config.get("is_backend") is True:
            build_args["supervisor_file"] = os.path.join("resources", "developer", "supervisord_backend.conf")
            docker_args["NGINX_UI_CONFIG"] = "resources/client/nginx_ui.conf"
        else:
            build_args["supervisor_file"] = os.path.join("resources", "developer", "supervisord_frontend.conf")
            docker_args["NGINX_API_CONFIG"] = "resources/client/nginx_api.conf"

        # Setup testing dependencies
        builder.merge_requirements_files([os.path.join("packages", "gtmapi", "requirements-testing.txt"),
                                          os.path.join("packages", "gtmcore", "requirements-testing.txt")])

        builder.build_image(no_cache=args.no_cache, build_args=build_args, docker_args=docker_args)

        # Print Name of image
        print("\n\n*** Built LabManager Dev Image: {}\n".format(builder.image_name))

    elif args.action == "prune":
        builder.cleanup("gigantum/labmanager-dev")
    elif args.action == "setup":
        dc.configure()
    elif args.action == "start":
        du = DevClientRunner()
        du.run()
    elif args.action == "run":
        print("Error: Unsupported action provided: `{}`. Did you mean `start`?".format(args.action), file=sys.stderr)
        sys.exit(1)
    elif args.action == "attach":
        du = DevClientRunner()
        du.attach()
    elif args.action == "log":
        show_log()
    else:
        print("Error: Unsupported action provided: {}".format(args.action), file=sys.stderr)
        sys.exit(1)


def circleci_actions(args):
    """Method to provide logic and perform actions for the circleci component

    Args:
        args(Namespace): Parsed arguments

    Returns:
        None
    """
    builder = circleci.CircleCIImageBuilder()

    if args.action == 'update':
        builder.update(verbose=args.verbose, no_cache=args.no_cache)
    else:
        print("Error: Unsupported action provided: {}".format(args.action), file=sys.stderr)
        sys.exit(1)


def main():
    # Setup supported components and commands
    components = dict()
    components['client'] = [["build", "Build the Production configuration Docker image"],
                            ["start", "Start a Production configuration Docker image"],
                            ["stop", "Stop a Production configuration Docker image"],
                            ["test", "Run internal tests on a Production configuration Docker image"],
                            ["publish", "Publish the latest build to Docker Hub"],
                            ["publish-edge", "Publish the latest build to Docker Hub as an Edge release"],
                            ["prune", "Remove all images except the latest Production configuration build"],
                            ["prune-edge", "Remove all edge build images except the latest"],
                            ["log", "Show the client log file in real-time"],
                            ]

    components['demo'] = [["build", "Build the LabManager Docker image"],
                          ["prune", "Remove all images except the latest build"],
                          ["publish", "Publish the latest build to Docker Hub as a Demo release"]]

    components['dev'] = [["setup", "Generate configuration for development. YOU MUST RUN THIS BEFORE USING GTM."],
                         ["build", "Build the Client Development Docker image"],
                         ["start", "Start the Client Development container (not applicable to PyCharm configs)"],
                         ["attach", "Attach to the running dev container"],
                         ["prune", "Remove all images except the latest Client Development build"],
                         ["log", "Show the client log file"]]

    components['circleci'] = [["update", "Build and publish the container for circleci"]]

    # Prep the help string
    help_str = format_component_help(components)
    component_str = ", ".join(list(components.keys()))

    description_str = "Developer command line tool for the Gigantum Client. \n\n"
    description_str = description_str + "** Get started by running `gtm dev setup` before any other commands! **\n\n"
    description_str = description_str + "The following components and actions are supported:\n\n{}".format(help_str)

    parser = argparse.ArgumentParser(description=description_str,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("--override-name", "-n",
                        default=None,
                        metavar="<alternative name>",
                        help="Alternative image target for base-image or labmanager")
    parser.add_argument("--verbose", "-v",
                        default=False,
                        action='store_true',
                        help="Boolean indicating if detail status should be printed")
    parser.add_argument("--all", "-a",
                        default=False,
                        action='store_true',
                        help="Boolean indicating if all containers should be removed during `gtm client stop`. "
                             "This will stop and prune ALL running docker containers")
    parser.add_argument("--no-cache",
                        default=False,
                        action='store_true',
                        help="Boolean indicating if docker cache should be ignored")
    parser.add_argument("component",
                        choices=list(components.keys()),
                        metavar="component",
                        help="System to interact with. Supported components: {}".format(component_str))
    parser.add_argument("action", help="Action to perform on a component")

    args = parser.parse_args()

    if args.component == "client":
        # LabManager Selected
        client_actions(args)
    elif args.component == "dev":
        # Base Image Selected
        developer_actions(args)
    elif args.component == "circleci":
        # CircleCI Selected
        circleci_actions(args)
    elif args.component == "demo":
        demo_actions(args)


if __name__ == '__main__':
    main()
