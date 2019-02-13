# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestDatasetRemoteOperations.test_list_remote_datasets_az 1'] = {
    'data': {
        'datasetList': {
            'remoteDatasets': {
                'edges': [
                    {
                        'cursor': 'eyJwYWdlIjogMSwgIml0ZW0iOiAxfQ==',
                        'node': {
                            'creationDateUtc': '2018-08-30T18:01:33.312Z',
                            'description': 'No Description',
                            'id': 'UmVtb3RlRGF0YXNldDp0ZXN0ZXImdGVzdC1kYXRhLTE=',
                            'isLocal': False,
                            'modifiedDateUtc': '2018-08-30T18:01:33.312Z',
                            'name': 'test-data-1',
                            'owner': 'tester'
                        }
                    },
                    {
                        'cursor': 'eyJwYWdlIjogMSwgIml0ZW0iOiAzfQ==',
                        'node': {
                            'creationDateUtc': '2018-08-29T18:01:33.312Z',
                            'description': 'No Description',
                            'id': 'UmVtb3RlRGF0YXNldDp0ZXN0ZXImdGVzdC1kYXRhLTI=',
                            'isLocal': False,
                            'modifiedDateUtc': '2018-09-01T18:01:33.312Z',
                            'name': 'test-data-2',
                            'owner': 'tester'
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

snapshots['TestDatasetRemoteOperations.test_list_remote_datasets_az 2'] = {
    'data': {
        'datasetList': {
            'remoteDatasets': {
                'edges': [
                    {
                        'cursor': 'eyJwYWdlIjogMSwgIml0ZW0iOiAzfQ==',
                        'node': {
                            'creationDateUtc': '2018-08-29T18:01:33.312Z',
                            'description': 'No Description',
                            'id': 'UmVtb3RlRGF0YXNldDp0ZXN0ZXImdGVzdC1kYXRhLTI=',
                            'modifiedDateUtc': '2018-09-01T18:01:33.312Z',
                            'name': 'test-data-2',
                            'owner': 'tester'
                        }
                    },
                    {
                        'cursor': 'eyJwYWdlIjogMSwgIml0ZW0iOiAxfQ==',
                        'node': {
                            'creationDateUtc': '2018-08-30T18:01:33.312Z',
                            'description': 'No Description',
                            'id': 'UmVtb3RlRGF0YXNldDp0ZXN0ZXImdGVzdC1kYXRhLTE=',
                            'modifiedDateUtc': '2018-08-30T18:01:33.312Z',
                            'name': 'test-data-1',
                            'owner': 'tester'
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

snapshots['TestDatasetRemoteOperations.test_list_remote_datasets_modified 1'] = {
    'data': {
        'datasetList': {
            'remoteDatasets': {
                'edges': [
                    {
                        'cursor': 'eyJwYWdlIjogMSwgIml0ZW0iOiAzfQ==',
                        'node': {
                            'creationDateUtc': '2018-08-29T18:01:33.312Z',
                            'description': 'No Description',
                            'id': 'UmVtb3RlRGF0YXNldDp0ZXN0ZXImdGVzdC1kYXRhLTI=',
                            'isLocal': False,
                            'modifiedDateUtc': '2018-09-01T18:01:33.312Z',
                            'name': 'test-data-2',
                            'owner': 'tester'
                        }
                    },
                    {
                        'cursor': 'eyJwYWdlIjogMSwgIml0ZW0iOiAxfQ==',
                        'node': {
                            'creationDateUtc': '2018-08-30T18:01:33.312Z',
                            'description': 'No Description',
                            'id': 'UmVtb3RlRGF0YXNldDp0ZXN0ZXImdGVzdC1kYXRhLTE=',
                            'isLocal': False,
                            'modifiedDateUtc': '2018-08-30T18:01:33.312Z',
                            'name': 'test-data-1',
                            'owner': 'tester'
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

snapshots['TestDatasetRemoteOperations.test_list_remote_datasets_modified 2'] = {
    'data': {
        'datasetList': {
            'remoteDatasets': {
                'edges': [
                    {
                        'cursor': 'eyJwYWdlIjogMSwgIml0ZW0iOiAxfQ==',
                        'node': {
                            'creationDateUtc': '2018-08-30T18:01:33.312Z',
                            'description': 'No Description',
                            'id': 'UmVtb3RlRGF0YXNldDp0ZXN0ZXImdGVzdC1kYXRhLTE=',
                            'modifiedDateUtc': '2018-08-30T18:01:33.312Z',
                            'name': 'test-data-1',
                            'owner': 'tester'
                        }
                    },
                    {
                        'cursor': 'eyJwYWdlIjogMSwgIml0ZW0iOiAzfQ==',
                        'node': {
                            'creationDateUtc': '2018-08-29T18:01:33.312Z',
                            'description': 'No Description',
                            'id': 'UmVtb3RlRGF0YXNldDp0ZXN0ZXImdGVzdC1kYXRhLTI=',
                            'modifiedDateUtc': '2018-09-01T18:01:33.312Z',
                            'name': 'test-data-2',
                            'owner': 'tester'
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

snapshots['TestDatasetRemoteOperations.test_list_remote_datasets_created 1'] = {
    'data': {
        'datasetList': {
            'remoteDatasets': {
                'edges': [
                    {
                        'cursor': 'eyJwYWdlIjogMSwgIml0ZW0iOiAxfQ==',
                        'node': {
                            'creationDateUtc': '2018-08-30T18:01:33.312Z',
                            'description': 'No Description',
                            'id': 'UmVtb3RlRGF0YXNldDp0ZXN0ZXImdGVzdC1kYXRhLTE=',
                            'isLocal': False,
                            'modifiedDateUtc': '2018-08-30T18:01:33.312Z',
                            'name': 'test-data-1',
                            'owner': 'tester'
                        }
                    },
                    {
                        'cursor': 'eyJwYWdlIjogMSwgIml0ZW0iOiAzfQ==',
                        'node': {
                            'creationDateUtc': '2018-08-29T18:01:33.312Z',
                            'description': 'No Description',
                            'id': 'UmVtb3RlRGF0YXNldDp0ZXN0ZXImdGVzdC1kYXRhLTI=',
                            'isLocal': False,
                            'modifiedDateUtc': '2018-09-01T18:01:33.312Z',
                            'name': 'test-data-2',
                            'owner': 'tester'
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

snapshots['TestDatasetRemoteOperations.test_list_remote_datasets_created 2'] = {
    'data': {
        'datasetList': {
            'remoteDatasets': {
                'edges': [
                    {
                        'cursor': 'eyJwYWdlIjogMSwgIml0ZW0iOiAzfQ==',
                        'node': {
                            'creationDateUtc': '2018-08-29T18:01:33.312Z',
                            'description': 'No Description',
                            'id': 'UmVtb3RlRGF0YXNldDp0ZXN0ZXImdGVzdC1kYXRhLTI=',
                            'modifiedDateUtc': '2018-09-01T18:01:33.312Z',
                            'name': 'test-data-2',
                            'owner': 'tester'
                        }
                    },
                    {
                        'cursor': 'eyJwYWdlIjogMSwgIml0ZW0iOiAxfQ==',
                        'node': {
                            'creationDateUtc': '2018-08-30T18:01:33.312Z',
                            'description': 'No Description',
                            'id': 'UmVtb3RlRGF0YXNldDp0ZXN0ZXImdGVzdC1kYXRhLTE=',
                            'modifiedDateUtc': '2018-08-30T18:01:33.312Z',
                            'name': 'test-data-1',
                            'owner': 'tester'
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

snapshots['TestDatasetRemoteOperations.test_list_remote_datasets_page 1'] = {
    'data': {
        'datasetList': {
            'remoteDatasets': {
                'edges': [
                    {
                        'cursor': 'eyJwYWdlIjogMSwgIml0ZW0iOiAxfQ==',
                        'node': {
                            'creationDateUtc': '2018-08-30T18:01:33.312Z',
                            'description': 'No Description',
                            'id': 'UmVtb3RlRGF0YXNldDp0ZXN0ZXImdGVzdC1kYXRhLTE=',
                            'isLocal': False,
                            'modifiedDateUtc': '2018-08-30T18:01:33.312Z',
                            'name': 'test-data-1',
                            'owner': 'tester'
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

snapshots['TestDatasetRemoteOperations.test_list_remote_datasets_page 2'] = {
    'data': {
        'datasetList': {
            'remoteDatasets': {
                'edges': [
                    {
                        'cursor': 'eyJwYWdlIjogMSwgIml0ZW0iOiAzfQ==',
                        'node': {
                            'creationDateUtc': '2018-08-29T18:01:33.312Z',
                            'description': 'No Description',
                            'id': 'UmVtb3RlRGF0YXNldDp0ZXN0ZXImdGVzdC1kYXRhLTI=',
                            'modifiedDateUtc': '2018-09-01T18:01:33.312Z',
                            'name': 'test-data-2',
                            'owner': 'tester'
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
