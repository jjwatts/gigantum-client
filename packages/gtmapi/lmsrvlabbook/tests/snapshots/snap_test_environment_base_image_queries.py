# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestEnvironmentBaseImageQueries.test_get_base_image_by_node 1'] = {
    'data': {
        'node': {
            'componentId': 'quickstart-jupyterlab',
            'description': 'Data Science Quickstart using Jupyterlab, numpy, and Matplotlib. A great base for any analysis.',
            'developmentTools': [
                'jupyterlab'
            ],
            'dockerImageNamespace': 'gigantum',
            'dockerImageRepository': 'python3-minimal',
            'dockerImageServer': 'hub.docker.com',
            'dockerImageTag': '826b6f24-2018-02-09',
            'icon': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
            'id': 'QmFzZUNvbXBvbmVudDpnaWdhbnR1bV9iYXNlLWltYWdlcy10ZXN0aW5nJnF1aWNrc3RhcnQtanVweXRlcmxhYiYx',
            'languages': [
                'python3'
            ],
            'license': 'MIT',
            'name': 'Data Science Quickstart with JupyterLab',
            'osClass': 'ubuntu',
            'osRelease': '16.04',
            'packageManagers': [
                'apt',
                'pip3'
            ],
            'readme': 'Empty for now',
            'tags': [
                'ubuntu',
                'python3',
                'jupyterlab'
            ],
            'url': None
        }
    }
}

snapshots['TestEnvironmentBaseImageQueries.test_get_available_base_images 1'] = {
    'data': {
        'availableBases': {
            'edges': [
                {
                    'node': {
                        'componentId': 'quickstart-jupyterlab',
                        'cudaVersion': None,
                        'description': 'Data Science Quickstart using Jupyterlab, numpy, and Matplotlib. A great base for any analysis.',
                        'developmentTools': [
                            'jupyterlab'
                        ],
                        'dockerImageNamespace': 'gigantum',
                        'dockerImageRepository': 'python3-minimal',
                        'dockerImageServer': 'hub.docker.com',
                        'dockerImageTag': '1effaaea-2018-05-23',
                        'icon': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
                        'id': 'QmFzZUNvbXBvbmVudDpnaWdhbnR1bV9iYXNlLWltYWdlcy10ZXN0aW5nJnF1aWNrc3RhcnQtanVweXRlcmxhYiYy',
                        'installedPackages': [
                            'apt|vim|2:7.4.1689-3ubuntu1.2',
                            'pip3|numpy|1.14.0',
                            'pip3|matplotlib|2.1.1',
                            'pip3|jupyter|1.0.0',
                            'pip3|jupyterlab|0.31.1',
                            'pip3|ipywidgets|7.1.0',
                            'pip3|pandas|0.22.0'
                        ],
                        'languages': [
                            'python3'
                        ],
                        'license': 'MIT',
                        'name': 'Data Science Quickstart with JupyterLab',
                        'osClass': 'ubuntu',
                        'osRelease': '18.04',
                        'packageManagers': [
                            'apt',
                            'pip3'
                        ],
                        'readme': 'Empty for now',
                        'schema': 1,
                        'tags': [
                            'ubuntu',
                            'python3',
                            'jupyterlab'
                        ],
                        'url': None
                    }
                },
                {
                    'node': {
                        'componentId': 'ut-busybox',
                        'cudaVersion': None,
                        'description': 'Super lightweight image for build testing',
                        'developmentTools': [
                        ],
                        'dockerImageNamespace': 'library',
                        'dockerImageRepository': 'busybox',
                        'dockerImageServer': 'hub.docker.com',
                        'dockerImageTag': '1.28.0',
                        'icon': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
                        'id': 'QmFzZUNvbXBvbmVudDpnaWdhbnR1bV9iYXNlLWltYWdlcy10ZXN0aW5nJnV0LWJ1c3lib3gmMA==',
                        'installedPackages': [
                        ],
                        'languages': [
                        ],
                        'license': 'MIT',
                        'name': 'Unit Test Busybox',
                        'osClass': 'busybox',
                        'osRelease': '1.28',
                        'packageManagers': [
                            'apt'
                        ],
                        'readme': 'Empty for now',
                        'schema': 1,
                        'tags': [
                            'busybox'
                        ],
                        'url': None
                    }
                },
                {
                    'node': {
                        'componentId': 'ut-jupyterlab-1',
                        'cudaVersion': None,
                        'description': 'Unit Test 1',
                        'developmentTools': [
                            'jupyterlab'
                        ],
                        'dockerImageNamespace': 'gigdev',
                        'dockerImageRepository': 'gm-quickstart',
                        'dockerImageServer': 'hub.docker.com',
                        'dockerImageTag': '9718fedc-2018-01-16',
                        'icon': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
                        'id': 'QmFzZUNvbXBvbmVudDpnaWdhbnR1bV9iYXNlLWltYWdlcy10ZXN0aW5nJnV0LWp1cHl0ZXJsYWItMSYw',
                        'installedPackages': [
                            'apt|supervisor|latest',
                            'apt|curl|latest',
                            'apt|gosu|latest',
                            'apt|build-essential|latest',
                            'apt|python3-dev|latest',
                            'apt|python3-pip|latest',
                            'apt|git|latest',
                            'apt|curl|latest',
                            'apt|vim|latest',
                            'pip3|numpy|1.14.0',
                            'pip3|matplotlib|2.1.1',
                            'pip3|jupyter|1.0.0',
                            'pip3|jupyterlab|0.31.1',
                            'pip3|ipywidgets|7.1.0',
                            'pip3|pandas|0.22.0'
                        ],
                        'languages': [
                            'python3'
                        ],
                        'license': 'MIT',
                        'name': 'Unit Test1',
                        'osClass': 'ubuntu',
                        'osRelease': '16.04',
                        'packageManagers': [
                            'apt',
                            'pip3'
                        ],
                        'readme': 'Empty for now',
                        'schema': 1,
                        'tags': [
                            'ubuntu',
                            'python3',
                            'jupyterlab'
                        ],
                        'url': None
                    }
                },
                {
                    'node': {
                        'componentId': 'ut-jupyterlab-2',
                        'cudaVersion': None,
                        'description': 'Unit Test 2',
                        'developmentTools': [
                            'jupyterlab'
                        ],
                        'dockerImageNamespace': 'gigdev',
                        'dockerImageRepository': 'gm-quickstart',
                        'dockerImageServer': 'hub.docker.com',
                        'dockerImageTag': '9718fedc-2018-01-16',
                        'icon': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
                        'id': 'QmFzZUNvbXBvbmVudDpnaWdhbnR1bV9iYXNlLWltYWdlcy10ZXN0aW5nJnV0LWp1cHl0ZXJsYWItMiYw',
                        'installedPackages': [
                            'apt|supervisor|latest',
                            'apt|python3-dev|latest',
                            'apt|python3-pip|latest',
                            'apt|git|latest',
                            'apt|curl|latest',
                            'apt|vim|latest',
                            'pip3|numpy|1.14.0',
                            'pip3|matplotlib|2.1.1',
                            'pip3|jupyter|1.0.0',
                            'pip3|jupyterlab|0.31.1'
                        ],
                        'languages': [
                            'python3'
                        ],
                        'license': 'MIT',
                        'name': 'Unit Test 2',
                        'osClass': 'ubuntu',
                        'osRelease': '16.04',
                        'packageManagers': [
                            'apt',
                            'pip3'
                        ],
                        'readme': 'Empty for now',
                        'schema': 1,
                        'tags': [
                            'ubuntu',
                            'python3',
                            'jupyterlab'
                        ],
                        'url': None
                    }
                },
                {
                    'node': {
                        'componentId': 'ut-jupyterlab-3',
                        'cudaVersion': None,
                        'description': 'Unit Test 3',
                        'developmentTools': [
                            'jupyterlab'
                        ],
                        'dockerImageNamespace': 'gigdev',
                        'dockerImageRepository': 'gm-quickstart',
                        'dockerImageServer': 'hub.docker.com',
                        'dockerImageTag': '9718fedc-2018-01-16',
                        'icon': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
                        'id': 'QmFzZUNvbXBvbmVudDpnaWdhbnR1bV9iYXNlLWltYWdlcy10ZXN0aW5nJnV0LWp1cHl0ZXJsYWItMyYw',
                        'installedPackages': [
                            'apt|supervisor|latest',
                            'apt|python3-dev|latest',
                            'apt|python3-pip|latest',
                            'apt|git|latest',
                            'apt|curl|latest',
                            'pip3|jupyter|1.0.0',
                            'pip3|jupyterlab|0.31.1'
                        ],
                        'languages': [
                            'python3'
                        ],
                        'license': 'MIT',
                        'name': 'Unit Test 3',
                        'osClass': 'ubuntu',
                        'osRelease': '16.04',
                        'packageManagers': [
                            'apt',
                            'pip3'
                        ],
                        'readme': 'Empty for now',
                        'schema': 1,
                        'tags': [
                            'ubuntu',
                            'python3',
                            'jupyterlab'
                        ],
                        'url': None
                    }
                }
            ]
        }
    }
}

snapshots['TestEnvironmentBaseImageQueries.test_get_available_base_images_pagination 1'] = {
    'data': {
        'availableBases': {
            'edges': [
                {
                    'cursor': 'MA==',
                    'node': {
                        'componentId': 'quickstart-jupyterlab',
                        'description': 'Data Science Quickstart using Jupyterlab, numpy, and Matplotlib. A great base for any analysis.',
                        'developmentTools': [
                            'jupyterlab'
                        ],
                        'dockerImageNamespace': 'gigantum',
                        'dockerImageRepository': 'python3-minimal',
                        'dockerImageServer': 'hub.docker.com',
                        'dockerImageTag': '1effaaea-2018-05-23',
                        'icon': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
                        'id': 'QmFzZUNvbXBvbmVudDpnaWdhbnR1bV9iYXNlLWltYWdlcy10ZXN0aW5nJnF1aWNrc3RhcnQtanVweXRlcmxhYiYy',
                        'languages': [
                            'python3'
                        ],
                        'license': 'MIT',
                        'name': 'Data Science Quickstart with JupyterLab',
                        'osClass': 'ubuntu',
                        'osRelease': '18.04',
                        'packageManagers': [
                            'apt',
                            'pip3'
                        ],
                        'readme': 'Empty for now',
                        'tags': [
                            'ubuntu',
                            'python3',
                            'jupyterlab'
                        ],
                        'url': None
                    }
                }
            ],
            'pageInfo': {
                'hasNextPage': True
            }
        }
    }
}

snapshots['TestEnvironmentBaseImageQueries.test_get_available_base_images_pagination 2'] = {
    'data': {
        'availableBases': {
            'edges': [
                {
                    'cursor': 'Mg==',
                    'node': {
                        'componentId': 'ut-jupyterlab-1',
                        'description': 'Unit Test 1',
                        'developmentTools': [
                            'jupyterlab'
                        ],
                        'dockerImageNamespace': 'gigdev',
                        'dockerImageRepository': 'gm-quickstart',
                        'dockerImageServer': 'hub.docker.com',
                        'dockerImageTag': '9718fedc-2018-01-16',
                        'icon': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
                        'id': 'QmFzZUNvbXBvbmVudDpnaWdhbnR1bV9iYXNlLWltYWdlcy10ZXN0aW5nJnV0LWp1cHl0ZXJsYWItMSYw',
                        'languages': [
                            'python3'
                        ],
                        'license': 'MIT',
                        'name': 'Unit Test1',
                        'osClass': 'ubuntu',
                        'osRelease': '16.04',
                        'packageManagers': [
                            'apt',
                            'pip3'
                        ],
                        'readme': 'Empty for now',
                        'tags': [
                            'ubuntu',
                            'python3',
                            'jupyterlab'
                        ],
                        'url': None
                    }
                },
                {
                    'cursor': 'Mw==',
                    'node': {
                        'componentId': 'ut-jupyterlab-2',
                        'description': 'Unit Test 2',
                        'developmentTools': [
                            'jupyterlab'
                        ],
                        'dockerImageNamespace': 'gigdev',
                        'dockerImageRepository': 'gm-quickstart',
                        'dockerImageServer': 'hub.docker.com',
                        'dockerImageTag': '9718fedc-2018-01-16',
                        'icon': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
                        'id': 'QmFzZUNvbXBvbmVudDpnaWdhbnR1bV9iYXNlLWltYWdlcy10ZXN0aW5nJnV0LWp1cHl0ZXJsYWItMiYw',
                        'languages': [
                            'python3'
                        ],
                        'license': 'MIT',
                        'name': 'Unit Test 2',
                        'osClass': 'ubuntu',
                        'osRelease': '16.04',
                        'packageManagers': [
                            'apt',
                            'pip3'
                        ],
                        'readme': 'Empty for now',
                        'tags': [
                            'ubuntu',
                            'python3',
                            'jupyterlab'
                        ],
                        'url': None
                    }
                }
            ],
            'pageInfo': {
                'hasNextPage': True
            }
        }
    }
}

snapshots['TestEnvironmentBaseImageQueries.test_get_available_base_images_pagination 3'] = {
    'data': {
        'availableBases': {
            'edges': [
                {
                    'cursor': 'Mg==',
                    'node': {
                        'componentId': 'ut-jupyterlab-1',
                        'description': 'Unit Test 1',
                        'developmentTools': [
                            'jupyterlab'
                        ],
                        'dockerImageNamespace': 'gigdev',
                        'dockerImageRepository': 'gm-quickstart',
                        'dockerImageServer': 'hub.docker.com',
                        'dockerImageTag': '9718fedc-2018-01-16',
                        'icon': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
                        'id': 'QmFzZUNvbXBvbmVudDpnaWdhbnR1bV9iYXNlLWltYWdlcy10ZXN0aW5nJnV0LWp1cHl0ZXJsYWItMSYw',
                        'languages': [
                            'python3'
                        ],
                        'license': 'MIT',
                        'name': 'Unit Test1',
                        'osClass': 'ubuntu',
                        'osRelease': '16.04',
                        'packageManagers': [
                            'apt',
                            'pip3'
                        ],
                        'readme': 'Empty for now',
                        'tags': [
                            'ubuntu',
                            'python3',
                            'jupyterlab'
                        ],
                        'url': None
                    }
                }
            ],
            'pageInfo': {
                'hasNextPage': True
            }
        }
    }
}

snapshots['TestEnvironmentBaseImageQueries.test_get_available_base_images_pagination_reverse 1'] = {
    'data': {
        'availableBases': {
            'edges': [
                {
                    'cursor': 'NA==',
                    'node': {
                        'componentId': 'ut-jupyterlab-3',
                        'description': 'Unit Test 3',
                        'developmentTools': [
                            'jupyterlab'
                        ],
                        'dockerImageNamespace': 'gigdev',
                        'dockerImageRepository': 'gm-quickstart',
                        'dockerImageServer': 'hub.docker.com',
                        'dockerImageTag': '9718fedc-2018-01-16',
                        'icon': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
                        'id': 'QmFzZUNvbXBvbmVudDpnaWdhbnR1bV9iYXNlLWltYWdlcy10ZXN0aW5nJnV0LWp1cHl0ZXJsYWItMyYw',
                        'languages': [
                            'python3'
                        ],
                        'license': 'MIT',
                        'name': 'Unit Test 3',
                        'osClass': 'ubuntu',
                        'osRelease': '16.04',
                        'packageManagers': [
                            'apt',
                            'pip3'
                        ],
                        'readme': 'Empty for now',
                        'tags': [
                            'ubuntu',
                            'python3',
                            'jupyterlab'
                        ],
                        'url': None
                    }
                }
            ],
            'pageInfo': {
                'hasNextPage': False,
                'hasPreviousPage': True
            }
        }
    }
}

snapshots['TestEnvironmentBaseImageQueries.test_get_available_base_images_pagination_reverse 2'] = {
    'data': {
        'availableBases': {
            'edges': [
                {
                    'cursor': 'MA==',
                    'node': {
                        'componentId': 'quickstart-jupyterlab',
                        'description': 'Data Science Quickstart using Jupyterlab, numpy, and Matplotlib. A great base for any analysis.',
                        'developmentTools': [
                            'jupyterlab'
                        ],
                        'dockerImageNamespace': 'gigantum',
                        'dockerImageRepository': 'python3-minimal',
                        'dockerImageServer': 'hub.docker.com',
                        'dockerImageTag': '1effaaea-2018-05-23',
                        'icon': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
                        'id': 'QmFzZUNvbXBvbmVudDpnaWdhbnR1bV9iYXNlLWltYWdlcy10ZXN0aW5nJnF1aWNrc3RhcnQtanVweXRlcmxhYiYy',
                        'languages': [
                            'python3'
                        ],
                        'license': 'MIT',
                        'name': 'Data Science Quickstart with JupyterLab',
                        'osClass': 'ubuntu',
                        'osRelease': '18.04',
                        'packageManagers': [
                            'apt',
                            'pip3'
                        ],
                        'readme': 'Empty for now',
                        'tags': [
                            'ubuntu',
                            'python3',
                            'jupyterlab'
                        ],
                        'url': None
                    }
                }
            ],
            'pageInfo': {
                'hasNextPage': False,
                'hasPreviousPage': False
            }
        }
    }
}

