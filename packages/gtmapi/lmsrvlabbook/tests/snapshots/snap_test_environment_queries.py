# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestEnvironmentServiceQueries.test_get_environment_status 1'] = {
    'data': {
        'labbook': {
            'environment': {
                'containerStatus': 'NOT_RUNNING',
                'imageStatus': 'DOES_NOT_EXIST'
            }
        }
    }
}

snapshots['TestEnvironmentServiceQueries.test_get_base 1'] = {
    'data': {
        'createLabbook': {
            'labbook': {
                'description': 'my test 1',
                'id': 'TGFiYm9vazpkZWZhdWx0JmxhYmJvb2stYmFzZS10ZXN0',
                'name': 'labbook-base-test'
            }
        }
    }
}

snapshots['TestEnvironmentServiceQueries.test_get_base 2'] = {
    'data': {
        'labbook': {
            'description': 'my test 1',
            'environment': {
                'base': {
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
            },
            'name': 'labbook-base-test'
        }
    }
}

snapshots['TestEnvironmentServiceQueries.test_package_query_with_errors 1'] = {
    'data': {
        'labbook': {
            'checkPackages': [
                {
                    'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAmZ3RtdW5pdDEmMC4yLjQ=',
                    'isValid': True,
                    'manager': 'pip',
                    'package': 'gtmunit1',
                    'version': '0.2.4'
                },
                {
                    'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAmZ3RtdW5pdDImMTAwLjAw',
                    'isValid': False,
                    'manager': 'pip',
                    'package': 'gtmunit2',
                    'version': '100.00'
                },
                {
                    'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAmZ3RtdW5pdDMmNS4w',
                    'isValid': True,
                    'manager': 'pip',
                    'package': 'gtmunit3',
                    'version': '5.0'
                },
                {
                    'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAmYXNkZmFzZGZhc2RmJg==',
                    'isValid': False,
                    'manager': 'pip',
                    'package': 'asdfasdfasdf',
                    'version': ''
                }
            ],
            'id': 'TGFiYm9vazpkZWZhdWx0JmxhYmJvb2s1'
        }
    }
}

snapshots['TestEnvironmentServiceQueries.test_package_query 1'] = {
    'data': {
        'labbook': {
            'checkPackages': [
                {
                    'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAmZ3RtdW5pdDEmMC4yLjQ=',
                    'isValid': True,
                    'manager': 'pip',
                    'package': 'gtmunit1',
                    'version': '0.2.4'
                },
                {
                    'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAmZ3RtdW5pdDImMTIuMg==',
                    'isValid': True,
                    'manager': 'pip',
                    'package': 'gtmunit2',
                    'version': '12.2'
                }
            ],
            'id': 'TGFiYm9vazpkZWZhdWx0JmxhYmJvb2s2'
        }
    }
}

snapshots['TestEnvironmentServiceQueries.test_get_package_manager 1'] = {
    'data': {
        'labbook': {
            'environment': {
                'packageDependencies': {
                    'edges': [
                    ],
                    'pageInfo': {
                        'hasNextPage': False
                    }
                }
            }
        }
    }
}

snapshots['TestEnvironmentServiceQueries.test_get_package_manager 2'] = {
    'data': {
        'labbook': {
            'environment': {
                'packageDependencies': {
                    'edges': [
                        {
                            'cursor': 'MA==',
                            'node': {
                                'fromBase': False,
                                'id': 'UGFja2FnZUNvbXBvbmVudDphcHQmbHhtbCYzLjQ=',
                                'manager': 'apt',
                                'package': 'lxml',
                                'version': '3.4'
                            }
                        },
                        {
                            'cursor': 'MQ==',
                            'node': {
                                'fromBase': False,
                                'id': 'UGFja2FnZUNvbXBvbmVudDpjb25kYTMmY2R1dGlsJjguMQ==',
                                'manager': 'conda3',
                                'package': 'cdutil',
                                'version': '8.1'
                            }
                        },
                        {
                            'cursor': 'Mg==',
                            'node': {
                                'fromBase': False,
                                'id': 'UGFja2FnZUNvbXBvbmVudDpjb25kYTMmbmx0ayYzLjIuNQ==',
                                'manager': 'conda3',
                                'package': 'nltk',
                                'version': '3.2.5'
                            }
                        },
                        {
                            'cursor': 'Mw==',
                            'node': {
                                'fromBase': False,
                                'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAmZ3RtdW5pdDEmMC4yLjQ=',
                                'manager': 'pip',
                                'package': 'gtmunit1',
                                'version': '0.2.4'
                            }
                        },
                        {
                            'cursor': 'NA==',
                            'node': {
                                'fromBase': False,
                                'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAmbnVtcHkmMS4xMg==',
                                'manager': 'pip',
                                'package': 'numpy',
                                'version': '1.12'
                            }
                        },
                        {
                            'cursor': 'NQ==',
                            'node': {
                                'fromBase': False,
                                'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAmcmVxdWVzdHMmMS4z',
                                'manager': 'pip',
                                'package': 'requests',
                                'version': '1.3'
                            }
                        }
                    ],
                    'pageInfo': {
                        'hasNextPage': False
                    }
                }
            }
        }
    }
}

snapshots['TestEnvironmentServiceQueries.test_get_package_manager 3'] = {
    'data': {
        'labbook': {
            'environment': {
                'packageDependencies': {
                    'edges': [
                        {
                            'cursor': 'MQ==',
                            'node': {
                                'fromBase': False,
                                'id': 'UGFja2FnZUNvbXBvbmVudDpjb25kYTMmY2R1dGlsJjguMQ==',
                                'manager': 'conda3',
                                'package': 'cdutil',
                                'version': '8.1'
                            }
                        },
                        {
                            'cursor': 'Mg==',
                            'node': {
                                'fromBase': False,
                                'id': 'UGFja2FnZUNvbXBvbmVudDpjb25kYTMmbmx0ayYzLjIuNQ==',
                                'manager': 'conda3',
                                'package': 'nltk',
                                'version': '3.2.5'
                            }
                        }
                    ],
                    'pageInfo': {
                        'hasNextPage': True
                    }
                }
            }
        }
    }
}

snapshots['TestEnvironmentServiceQueries.test_get_package_manager_metadata 1'] = {
    'data': {
        'labbook': {
            'environment': {
                'packageDependencies': {
                    'edges': [
                    ],
                    'pageInfo': {
                        'hasNextPage': False
                    }
                }
            }
        }
    }
}

snapshots['TestEnvironmentServiceQueries.test_get_package_manager_metadata 2'] = {
    'data': {
        'labbook': {
            'environment': {
                'packageDependencies': {
                    'edges': [
                        {
                            'cursor': 'MA==',
                            'node': {
                                'description': 'A set of tools to manipulate climate data',
                                'docsUrl': 'http://anaconda.org/conda-forge/cdutil',
                                'fromBase': False,
                                'id': 'UGFja2FnZUNvbXBvbmVudDpjb25kYTMmY2R1dGlsJjguMQ==',
                                'latestVersion': '8.1',
                                'manager': 'conda3',
                                'package': 'cdutil',
                                'version': '8.1'
                            }
                        },
                        {
                            'cursor': 'MQ==',
                            'node': {
                                'description': 'Python interface to coveralls.io API\\n',
                                'docsUrl': 'http://anaconda.org/conda-forge/python-coveralls',
                                'fromBase': False,
                                'id': 'UGFja2FnZUNvbXBvbmVudDpjb25kYTMmcHl0aG9uLWNvdmVyYWxscyYyLjUuMA==',
                                'latestVersion': '2.9.1',
                                'manager': 'conda3',
                                'package': 'python-coveralls',
                                'version': '2.5.0'
                            }
                        },
                        {
                            'cursor': 'Mg==',
                            'node': {
                                'description': 'Package 1 for Gigantum Client unit testing.',
                                'docsUrl': 'https://github.com/gigantum/gigantum-client',
                                'fromBase': False,
                                'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAmZ3RtdW5pdDEmMC4yLjE=',
                                'latestVersion': '0.12.4',
                                'manager': 'pip',
                                'package': 'gtmunit1',
                                'version': '0.2.1'
                            }
                        },
                        {
                            'cursor': 'Mw==',
                            'node': {
                                'description': 'Package 1 for Gigantum Client unit testing.',
                                'docsUrl': 'https://github.com/gigantum/gigantum-client',
                                'fromBase': False,
                                'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAmZ3RtdW5pdDImMTIuMg==',
                                'latestVersion': '12.2',
                                'manager': 'pip',
                                'package': 'gtmunit2',
                                'version': '12.2'
                            }
                        },
                        {
                            'cursor': 'NA==',
                            'node': {
                                'description': 'Package 1 for Gigantum Client unit testing.',
                                'docsUrl': 'https://github.com/gigantum/gigantum-client',
                                'fromBase': False,
                                'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAmZ3RtdW5pdDMmNS4w',
                                'latestVersion': '5.0',
                                'manager': 'pip',
                                'package': 'gtmunit3',
                                'version': '5.0'
                            }
                        }
                    ],
                    'pageInfo': {
                        'hasNextPage': False
                    }
                }
            }
        }
    }
}
