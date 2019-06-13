![Gigantum Banner](docs/img/Readme-Banner.png)

[Home](https://gigantum.com)
&middot; [Demo](https://try.gigantum.com)
&middot; [Docs](https://docs.gigantum.com)
&middot; [Twitter](https://twitter.com/gigantumscience)
&middot; [Community &amp; Support](https://spectrum.chat/gigantum)
&middot; [Feedback](https://portal.prodpad.com/d47eb9fe-c779-11e8-97cd-06df22ffaf6f)

[![CircleCI](https://circleci.com/gh/gigantum/gigantum-client/tree/master.svg?style=svg)](https://circleci.com/gh/gigantum/gigantum-client/tree/master)
[![codecov](https://codecov.io/gh/gigantum/gigantum-client/branch/master/graph/badge.svg?token=1k6CENUN8G)](https://codecov.io/gh/gigantum/gigantum-client)
[![FOSSA Status](https://app.fossa.io/api/projects/custom%2B6007%2FGigantum%20Client.svg?type=small)](https://app.fossa.io/projects/custom%2B6007%2FGigantum%20Client?ref=badge_small)

The **Gigantum Client** is a web application to manage the creation and sharing of data science projects. It is run 
locally and is delivered via a Docker container. The Client is the core component of a larger ecosystem of tools 
and services, including:
- [Gigantum Cloud](https://gigantum.com) - A public repository for storage and sharing of Projects
- [Gigantum Desktop](https://github.com/gigantum/gigantum-desktop) - A desktop app to install and launch the Client 
- [Gigantum CLI](https://github.com/gigantum/gigantum-cli) - A simple command line tool to install and launch the Client

## Installation Quickstart

Gigantum is `pip`-installable, note that Docker needs to be installed (See instructions below). Once installed, just open your browser to http://localhost:10000!

```bash
pip install gigantum
gigantum install && gigantum start
```

Gigantum can also be delivered as a convenient desktop application, available on our [Downloads page](https://gigantum.com/download).

## Build and Run Gigantum from Source

### 1) Install Docker 

Developing the Gigantum Client requires that you have Docker installed locally. Visit the Gigantum 
[user docs](https://docs.gigantum.com/docs/configuring-docker) for instructions if needed.

Note, Docker must be running to build/run/test the Client.


### 2) Clone gigantum-client

```bash
git clone git@github.com:gigantum/gigantum-client.git
cd gigantum-client
git submodule update --init --recursive
```

To get started, clone the `gigantum-client` repository locally. If you plan to contribute, be sure to create a fork
first so you can easily create a PR. 

The `integration` branch is the current "working" branch with the latest functional changes that have yet to be 
released as stable.
The `master` branch is the last version released as stable (i.e. what you get when you install the Gigantum Desktop
app)


### 3) Create virtual environment

```bash
python -m venv gtm-env
source gtm-env/bin/activate
cd gtm && pip install -e . && cd ..
```

`gtm` is a command line tool to help build and configure the Client. This is a Python 3 application, so you must have
Python 3 installed. For detailed instruction see [gtm/README.md](gtm/README.md).

The command `gtm` is now available. Run `gtm -h` to see available commands.

### 4) Configure your development environment

```bash
gtm dev setup
```

`gtm` must be configured before use. This will ask a few questions and write configuration data to disk for future use.

"Backend" development mode is a configuration primarily used when working on the API. It configures the development
 container so that when started, the UI is served but the API does not start automatically. 

"Frontend" development mode is a configuration primarily used when working on the Javascript UI. It configures the
development container so that the API starts automatically, but the UI bundle is not served. This lets you run the Node
 server locally (on your host) so hot-loading and other dev features work well.

### 5) Build application client container and start working

```bash
gtm dev -v build
```

Once complete, you'll have a container available for use either via your terminal or from PyCharm.


### 6) Starting and stopping the gigantum client from terminal

```bash
gtm dev start
```

In a new console session, enter the container and kick off the application:

```bash
gtm dev attach
/opt/setup.sh
python3 service.py
```

Open your web browser to http://localhost:10000 to access the application.

When finished, run:

```bash
gtm dev stop
```
 

### 7) Starting and stopping the gigantum client from PyCharm

See [Pycharm dev notes](docs/pycharm-dev.md) for more details on how to set up Pycharm to use the development
container



## Users

### Installing the Client
If you are simply interested in *using* the Gigantum Client, please follow the [download
instructions](https://gigantum.com/download) at gigantum.com. For most users, installing then Desktop app is the
 recommended way of getting the Client. 


### Try It Out
If you want to try out Gigantum before installing, you can use the online demo at
 [https://try.gigantum.com](https://try.gigantum.com).

This demo will stop any Project container that runs longer than 1 hr and remove your work after ~1 day.


### More Information
For more information visit [gigantum.com](https://gigantum.com) and check out the user docs at
[docs.gigantum.com](https://docs.gigantum.com).


## Development

### Overview of Monorepo Structure

`gigantum-client` is organized as a monorepo, which means it contains multiple packages. While this has a few drawbacks
(e.g. larger repo, code possibly looks more intimidating, can't pip/npm install from Github), it has lots of benefits. 
By bundling all of the components and tooling into a single repository, it makes it easier to develop, build, and release 
the Gigantum Client. It also provides a single place to report issues, makes it easier to coordinate complex changes
across components, and makes testing easier. Finally, by maintaining parts of the code base as independent, 
but related packages, it makes it easier re-use code in different parts of the platform.

This may seem odd, but lots of open source tools do it. Check out [React](https://github.com/facebook/react/tree/master/packages),
 [Meteor](https://github.com/meteor/meteor/tree/devel/packages), 
 [Ember](https://github.com/emberjs/ember.js/tree/master/packages), 
 [Babel](https://github.com/babel/babel/blob/master/doc/design/monorepo.md), and
 [nteract](https://github.com/nteract/nteract) for example.

Due to the added complexity of managing multiple packages in a single repository, `gigantum-client` includes a developer
tool called `gtm`. This tool manages building, testing, and deploying the Gigantum Client in several different
configurations. Refer to [gtm README](gtm/README.md) for more details.

The repo is organized as follows:

- `docs/`: Additional documentation and instructions for developers (in progress and possibly out of date)
- `gtm/`: A python package containing the developer tool `gtm` 
- `packages/confhttpproxy`: A python package for interfacing with the [configurable proxy](https://github.com/jupyterhub/configurable-http-proxy) currently used by the Client
- `packages/gtmapi`: A python package containing the Client's GraphQL API.
- `packages/gtmcore`: A python package with many subpackages that make up the "core" library used by the Client. This
                      package will be broken up in the future into more granular, related packages.
- `resources/client`: Files and configuration data required for building the "production" configured container
- `resources/developer`: Files and configuration data required for building the "developer" configured container
- `resources/docker`: Dockerfiles for building the Client container
- `ui`: The javascript frontend and associated build scripts and configuration


### Contributing

You can view contributors by visiting the
 [contributors page](https://github.com/gigantum/gigantum-client/graphs/contributors) on GitHub.

If you want to contribute to the Gigantum Client, the best place to start is the
 [contributing guide](docs/contributing.md).

This project follows the [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected 
to follow this code. Please report unacceptable behavior to conduct@gigantum.com.


### License

The Gigantum Client is released under an [MIT license](LICENSE)

[![FOSSA Status](https://app.fossa.io/api/projects/custom%2B6007%2FGigantum%20Client.svg?type=large)](https://app.fossa.io/projects/custom%2B6007%2FGigantum%20Client?ref=badge_large)

