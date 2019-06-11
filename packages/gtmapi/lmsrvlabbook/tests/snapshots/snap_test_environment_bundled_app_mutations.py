# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestBundledAppMutations.test_add_bundled_app 1'] = {
    'data': {
        'labbook': {
            'environment': {
                'bundledApps': [
                ],
                'id': 'RW52aXJvbm1lbnQ6ZGVmYXVsdCZ0ZXN0LWFwcA=='
            },
            'id': 'TGFiYm9vazpkZWZhdWx0JnRlc3QtYXBw'
        }
    }
}

snapshots['TestBundledAppMutations.test_add_bundled_app 2'] = {
    'data': {
        'setBundledApp': {
            'clientMutationId': None,
            'environment': {
                'bundledApps': [
                    {
                        'appName': 'my app',
                        'command': 'python /opt/app.py',
                        'description': 'a cool app to do things',
                        'id': 'QnVuZGxlZEFwcDpkZWZhdWx0JnRlc3QtYXBwJm15IGFwcA==',
                        'port': 9999
                    }
                ],
                'id': 'RW52aXJvbm1lbnQ6ZGVmYXVsdCZ0ZXN0LWFwcA=='
            }
        }
    }
}

snapshots['TestBundledAppMutations.test_add_bundled_app 3'] = {
    'data': {
        'labbook': {
            'environment': {
                'bundledApps': [
                    {
                        'appName': 'my app',
                        'command': 'python /opt/app.py',
                        'description': 'a cool app to do things',
                        'id': 'QnVuZGxlZEFwcDpkZWZhdWx0JnRlc3QtYXBwJm15IGFwcA==',
                        'port': 9999
                    }
                ],
                'id': 'RW52aXJvbm1lbnQ6ZGVmYXVsdCZ0ZXN0LWFwcA=='
            },
            'id': 'TGFiYm9vazpkZWZhdWx0JnRlc3QtYXBw'
        }
    }
}

snapshots['TestBundledAppMutations.test_add_bundled_app 4'] = {
    'data': {
        'setBundledApp': {
            'clientMutationId': None,
            'environment': {
                'bundledApps': [
                    {
                        'appName': 'my app',
                        'command': 'python /opt/app2.py',
                        'description': 'a cooler app to do things',
                        'id': 'QnVuZGxlZEFwcDpkZWZhdWx0JnRlc3QtYXBwJm15IGFwcA==',
                        'port': 9900
                    }
                ],
                'id': 'RW52aXJvbm1lbnQ6ZGVmYXVsdCZ0ZXN0LWFwcA=='
            }
        }
    }
}

snapshots['TestBundledAppMutations.test_add_bundled_app 5'] = {
    'data': {
        'labbook': {
            'environment': {
                'bundledApps': [
                    {
                        'appName': 'my app',
                        'command': 'python /opt/app2.py',
                        'description': 'a cooler app to do things',
                        'id': 'QnVuZGxlZEFwcDpkZWZhdWx0JnRlc3QtYXBwJm15IGFwcA==',
                        'port': 9900
                    }
                ],
                'id': 'RW52aXJvbm1lbnQ6ZGVmYXVsdCZ0ZXN0LWFwcA=='
            },
            'id': 'TGFiYm9vazpkZWZhdWx0JnRlc3QtYXBw'
        }
    }
}

snapshots['TestBundledAppMutations.test_remove_bundled_app 1'] = {
    'data': {
        'labbook': {
            'environment': {
                'bundledApps': [
                    {
                        'appName': 'dash app 1',
                        'command': 'python /mnt/labbook/code/dash1.py',
                        'description': 'my example bundled app 1',
                        'id': 'QnVuZGxlZEFwcDpkZWZhdWx0JnRlc3QtYXBwLTImZGFzaCBhcHAgMQ==',
                        'port': 9999
                    },
                    {
                        'appName': 'dash app 2',
                        'command': 'python /mnt/labbook/code/dash2.py',
                        'description': 'my example bundled app 2',
                        'id': 'QnVuZGxlZEFwcDpkZWZhdWx0JnRlc3QtYXBwLTImZGFzaCBhcHAgMg==',
                        'port': 8822
                    },
                    {
                        'appName': 'dash app 3',
                        'command': 'python /mnt/labbook/code/dash3.py',
                        'description': 'my example bundled app 3',
                        'id': 'QnVuZGxlZEFwcDpkZWZhdWx0JnRlc3QtYXBwLTImZGFzaCBhcHAgMw==',
                        'port': 9966
                    }
                ],
                'id': 'RW52aXJvbm1lbnQ6ZGVmYXVsdCZ0ZXN0LWFwcC0y'
            },
            'id': 'TGFiYm9vazpkZWZhdWx0JnRlc3QtYXBwLTI='
        }
    }
}

snapshots['TestBundledAppMutations.test_remove_bundled_app 2'] = {
    'data': {
        'removeBundledApp': {
            'clientMutationId': None,
            'environment': {
                'bundledApps': [
                    {
                        'appName': 'dash app 1',
                        'command': 'python /mnt/labbook/code/dash1.py',
                        'description': 'my example bundled app 1',
                        'id': 'QnVuZGxlZEFwcDpkZWZhdWx0JnRlc3QtYXBwLTImZGFzaCBhcHAgMQ==',
                        'port': 9999
                    },
                    {
                        'appName': 'dash app 3',
                        'command': 'python /mnt/labbook/code/dash3.py',
                        'description': 'my example bundled app 3',
                        'id': 'QnVuZGxlZEFwcDpkZWZhdWx0JnRlc3QtYXBwLTImZGFzaCBhcHAgMw==',
                        'port': 9966
                    }
                ],
                'id': 'RW52aXJvbm1lbnQ6ZGVmYXVsdCZ0ZXN0LWFwcC0y'
            }
        }
    }
}

snapshots['TestBundledAppMutations.test_remove_bundled_app 3'] = {
    'data': {
        'labbook': {
            'environment': {
                'bundledApps': [
                    {
                        'appName': 'dash app 1',
                        'command': 'python /mnt/labbook/code/dash1.py',
                        'description': 'my example bundled app 1',
                        'id': 'QnVuZGxlZEFwcDpkZWZhdWx0JnRlc3QtYXBwLTImZGFzaCBhcHAgMQ==',
                        'port': 9999
                    },
                    {
                        'appName': 'dash app 3',
                        'command': 'python /mnt/labbook/code/dash3.py',
                        'description': 'my example bundled app 3',
                        'id': 'QnVuZGxlZEFwcDpkZWZhdWx0JnRlc3QtYXBwLTImZGFzaCBhcHAgMw==',
                        'port': 9966
                    }
                ],
                'id': 'RW52aXJvbm1lbnQ6ZGVmYXVsdCZ0ZXN0LWFwcC0y'
            },
            'id': 'TGFiYm9vazpkZWZhdWx0JnRlc3QtYXBwLTI='
        }
    }
}

snapshots['TestBundledAppMutations.test_start_bundled_app 1'] = {
    'data': {
        'labbook': {
            'environment': {
                'bundledApps': [
                    {
                        'appName': 'dash app 1',
                        'command': 'echo test',
                        'description': 'my example bundled app 1',
                        'id': 'QnVuZGxlZEFwcDpkZWZhdWx0JnRlc3QtYXBwLTEmZGFzaCBhcHAgMQ==',
                        'port': 9999
                    }
                ],
                'id': 'RW52aXJvbm1lbnQ6ZGVmYXVsdCZ0ZXN0LWFwcC0x'
            },
            'id': 'TGFiYm9vazpkZWZhdWx0JnRlc3QtYXBwLTE='
        }
    }
}

snapshots['TestBundledAppMutations.test_start_bundled_app 2'] = {
    'data': {
        'removeBundledApp': None
    },
    'errors': [
        {
            'locations': [
                {
                    'column': 11,
                    'line': 3
                }
            ],
            'message': 'App dash app 2 does not exist. Cannot remove.',
            'path': [
                'removeBundledApp'
            ]
        }
    ]
}
