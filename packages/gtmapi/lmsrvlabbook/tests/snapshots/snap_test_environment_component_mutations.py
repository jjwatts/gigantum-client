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
                        'schema': 1,
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
                        'schema': 1,
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
                        'schema': 1,
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
