#!/usr/bin/python3
import shutil
import os
import base64
import asyncio
import threading

from confhttpproxy import ProxyRouter
from flask import Flask, jsonify, request, abort
import flask
from flask_cors import CORS, cross_origin
import redis
import blueprint
import yaml


from gtmcore.configuration import Configuration
from gtmcore.logging import LMLogger
from gtmcore.environment import RepositoryManager
from gtmcore.auth.identity import AuthenticationError, get_identity_manager
from gtmcore.labbook.lock import reset_all_locks
from gtmcore.inventory.inventory import InventoryManager
from lmsrvcore.auth.user import get_logged_in_author
from lmsrvcore import service_telemetry

logger = LMLogger.get_logger()

# Create Flask app
app = Flask("lmsrvlabbook")

# Load configuration class into the flask application
user_conf_path = "/mnt/gigantum/.labmanager/config.yaml"
if os.path.exists(user_conf_path):
    logger.info(f"Using custom user configuration from {user_conf_path}")
    try:
        with open(user_conf_path) as user_file:
            yaml.safe_load(user_file)
        shutil.copyfile(user_conf_path, os.path.expanduser("~/user-config.yaml"))
    except Exception as e:
        logger.error("Error parsing user config, cannot proceed")
        raise
else:
    logger.info("No custom user configuration found")


random_bytes = os.urandom(32)
app.config["SECRET_KEY"] = base64.b64encode(random_bytes).decode('utf-8')
app.config["LABMGR_CONFIG"] = config = Configuration()
app.config["LABMGR_ID_MGR"] = get_identity_manager(Configuration())

if config.config["flask"]["allow_cors"]:
    # Allow CORS
    CORS(app, max_age=7200)

# Set Debug mode
app.config['DEBUG'] = config.config["flask"]["DEBUG"]

# Register LabBook service
app.register_blueprint(blueprint.complete_labbook_service)

# Configure CHP
try:
    api_prefix = app.config["LABMGR_CONFIG"].config['proxy']["labmanager_api_prefix"]
    apparent_proxy_port = app.config["LABMGR_CONFIG"].config['proxy']["apparent_proxy_port"]
    api_port = app.config["LABMGR_CONFIG"].config['proxy']['api_port']

    proxy_router = ProxyRouter.get_proxy(app.config["LABMGR_CONFIG"].config['proxy'])
    proxy_router.add("http://localhost:10001", "api")
    logger.info(f"Proxy routes ({type(proxy_router)}): {proxy_router.routes}")
except Exception as e:
    logger.exception(e)


# Set auth error handler
@app.errorhandler(AuthenticationError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response


@app.route(f"{api_prefix}/sysinfo")
@cross_origin(headers=["Content-Type", "Authorization"], max_age=7200)
def sysinfo():
    return jsonify(service_telemetry())


# Set Unauth'd route for API health-check
@app.route(f"{api_prefix}/ping/")
@cross_origin(headers=["Content-Type", "Authorization"], max_age=7200)
def ping():
    """Unauthorized endpoint for validating the API is up"""
    app_name, built_on, revision = config.config['build_info'].split(' :: ')
    return jsonify({
        "application": app_name ,
        "built_on": built_on,
        "revision": revision
    })


@app.route(f"{api_prefix}/version/")
@cross_origin(headers=["Content-Type", "Authorization"], max_age=7200)
def version():
    """Unauthorized endpoint for validating the API is up.

    Note: /api/version endpoint added due to popup blockers starting to block /api/ping/

    """
    app_name, built_on, revision = config.config['build_info'].split(' :: ')
    return jsonify({
        "application": app_name ,
        "built_on": built_on,
        "revision": revision
    })


@app.route(f'{api_prefix}/savehook/<username>/<owner>/<labbook_name>')
def savehook(username, owner, labbook_name):
    try:
        changed_file = request.args.get('file')
        jupyter_token = request.args.get('jupyter_token')
        logger.debug(f"Received save hook for {changed_file} in {username}/{owner}/{labbook_name}")

        redis_conn = redis.Redis(db=1)
        lb_jupyter_token_key = '-'.join(['gmlb', username, owner, labbook_name, 'jupyter-token'])
        lb_active_key = f"{'|'.join([username, owner, labbook_name])}&is-busy*"

        r = redis_conn.get(lb_jupyter_token_key.encode())
        if r is None:
            logger.error(f"Could not find jupyter token for {username}/{owner}/{labbook_name}")
            abort(400)

        if r.decode() != jupyter_token:
            raise ValueError("Incoming jupyter token must be valid")

        if len(redis_conn.keys(lb_active_key.encode())) > 0:
            # A kernel in this project is still active. Don't save auto-commit because it can blow up the
            # repository size depending on what the user is doing
            logger.info(f"Skipping jupyter savehook for {username}/{owner}/{labbook_name} due to active kernel")
            return 'success'

        lb = InventoryManager().load_labbook(username, owner, labbook_name,
                                             author=get_logged_in_author())
        with lb.lock():
            lb.sweep_uncommitted_changes()

        logger.info(f"Jupyter save hook saved {changed_file} from {str(lb)}")
        return 'success'
    except Exception as err:
        logger.error(err)
        return abort(400)


# TEMPORARY KLUDGE
# Due to GitPython implementation, resources leak. This block deletes all GitPython instances at the end of the request
# Future work will remove GitPython, at which point this block should be removed.
@app.after_request
def cleanup_git(response):
    loader = getattr(flask.request, 'labbook_loader', None)
    if loader:
        for key in loader.__dict__["_promise_cache"]:
            try:
                lb = loader.__dict__["_promise_cache"][key].value
                lb.git.repo.__del__()
            except AttributeError:
                continue
    return response
# TEMPORARY KLUDGE


logger.info("Cloning/Updating environment repositories.")

try:
    erm = RepositoryManager()
    update_successful = erm.update_repositories()
    if update_successful:
        logger.info("Indexing environment repositories.")
        erm.index_repositories()
        logger.info("Environment repositories updated and ready.")

    else:
        logger.info("Unable to update environment repositories at startup, most likely due to lack of internet access.")
except Exception as e:
    logger.error(e)
    raise

# Empty container-container share dir as it is ephemeral
share_dir = os.path.join(os.path.sep, 'mnt', 'share')
logger.info("Emptying container-container share folder: {}.".format(share_dir))
try:
    for item in os.listdir(share_dir):
        item_path = os.path.join(share_dir, item)
        if os.path.isfile(item_path):
            os.unlink(item_path)
        else:
            shutil.rmtree(item_path)
except Exception as e:
    logger.error(f"Failed to empty share folder: {e}.")
    raise

post_save_hook_code = """
import subprocess, os
def post_save_hook(os_path, model, contents_manager, **kwargs):
    try:
        labmanager_ip = open('/home/giguser/labmanager_ip').read().strip()
        tokens = open('/home/giguser/jupyter_token').read().strip()
        username, owner, lbname, jupyter_token = tokens.split(',')
        url_args = "file={}&jupyter_token={}".format(os.path.basename(os_path), jupyter_token)
        url = "http://{}:10001/api/savehook/{}/{}/{}?{}".format(labmanager_ip,username,owner,lbname,url_args)
        subprocess.run(['wget', '--spider', url], cwd='/tmp')
    except Exception as e:
        print(e)

"""
os.makedirs(os.path.join(share_dir, 'jupyterhooks'))
with open(os.path.join(share_dir, 'jupyterhooks', '__init__.py'), 'w') as initpy:
    initpy.write(post_save_hook_code)


# Reset distributed lock, if desired
if config.config["lock"]["reset_on_start"]:
    logger.info("Resetting ALL distributed locks")
    reset_all_locks(config.config['lock'])


def main(debug=False) -> None:
    try:
        # Run app on 0.0.0.0, assuming not an issue since it should be in a container
        # Please note: Debug mode must explicitly be set to False when running integration
        # tests, due to properties of Flask werkzeug dynamic package reloading.
        if debug:
            # This is to support integration tests, which will call main
            # with debug=False in order to avoid runtime reloading of Python code
            # which causes the interpreter to crash.
            app.run(host="0.0.0.0", port=10001, debug=debug)
        else:
            # If debug arg is not explicitly given then it is loaded from config
            app.run(host="0.0.0.0", port=10001)
    except Exception as e:
        logger.exception(e)
        raise


if __name__ == '__main__':
    main()
