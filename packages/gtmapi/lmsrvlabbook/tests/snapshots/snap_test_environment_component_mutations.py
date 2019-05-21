# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestAddComponentMutations.test_add_package 1'] = {
    'data': {
        'addPackageComponents': {
            'clientMutationId': None,
            'newPackageComponentEdges': [
                {
                    'cursor': 'MA==',
                    'node': {
                        'fromBase': False,
                        'id': 'UGFja2FnZUNvbXBvbmVudDpjb25kYTMmcHl0aG9uLWNvdmVyYWxscyYyLjkuMQ==',
                        'manager': 'conda3',
                        'package': 'python-coveralls',
                        'version': '2.9.1'
                    }
                }
            ]
        }
    }
}

snapshots['TestAddComponentMutations.test_add_multiple_packages 1'] = {
    'data': {
        'addPackageComponents': {
            'clientMutationId': None,
            'newPackageComponentEdges': [
                {
                    'cursor': 'MA==',
                    'node': {
                        'fromBase': False,
                        'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAzJmd0bXVuaXQxJjAuMTIuNA==',
                        'manager': 'pip3',
                        'package': 'gtmunit1',
                        'version': '0.12.4'
                    }
                },
                {
                    'cursor': 'MQ==',
                    'node': {
                        'fromBase': False,
                        'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAzJmd0bXVuaXQyJjEuMTQuMQ==',
                        'manager': 'pip3',
                        'package': 'gtmunit2',
                        'version': '1.14.1'
                    }
                }
            ]
        }
    }
}

snapshots['TestAddComponentMutations.test_remove_package 1'] = {
    'data': {
        'addPackageComponents': {
            'clientMutationId': None,
            'newPackageComponentEdges': [
                {
                    'node': {
                        'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAzJmd0bXVuaXQxJjAuMTIuNA=='
                    }
                },
                {
                    'node': {
                        'id': 'UGFja2FnZUNvbXBvbmVudDpwaXAzJmd0bXVuaXQyJjEuMTQuMQ=='
                    }
                }
            ]
        }
    }
}

snapshots['TestAddComponentMutations.test_remove_package 2'] = {
    'data': {
        'removePackageComponents': {
            'clientMutationId': None,
            'success': True
        }
    }
}

snapshots['TestAddComponentMutations.test_update_base 1'] = {
    'data': {
        'changeLabbookBase': {
            'labbook': {
                'environment': {
                    'base': {
                        'componentId': 'quickstart-jupyterlab',
                        'name': 'Data Science Quickstart with JupyterLab',
                        'repository': 'gigantum_base-images-testing',
                        'revision': 2
                    }
                },
            }
        }
    }
}

snapshots['TestAddComponentMutations.test_change_base 1'] = {
    'data': {
        'changeLabbookBase': {
            'labbook': {
                'environment': {
                    'base': {
                        'componentId': 'ut-busybox',
                        'name': 'Unit Test Busybox',
                        'repository': 'gigantum_base-images-testing',
                        'revision': 0
                    }
                }
            }
        }
    }
}
