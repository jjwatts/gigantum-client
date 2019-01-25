# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestDatasetQueries.test_pagination_noargs 1'] = {
    'data': {
        'datasetList': {
            'localDatasets': {
                'edges': [
                    {
                        'cursor': 'MA==',
                        'node': {
                            'description': 'Cats 1',
                            'name': 'dataset1'
                        }
                    },
                    {
                        'cursor': 'MQ==',
                        'node': {
                            'description': 'Cats 2',
                            'name': 'dataset2'
                        }
                    },
                    {
                        'cursor': 'Mg==',
                        'node': {
                            'description': 'Cats 3',
                            'name': 'dataset3'
                        }
                    },
                    {
                        'cursor': 'Mw==',
                        'node': {
                            'description': 'Cats 4',
                            'name': 'dataset4'
                        }
                    },
                    {
                        'cursor': 'NA==',
                        'node': {
                            'description': 'Cats 5',
                            'name': 'dataset5'
                        }
                    },
                    {
                        'cursor': 'NQ==',
                        'node': {
                            'description': 'Cats 6',
                            'name': 'dataset6'
                        }
                    },
                    {
                        'cursor': 'Ng==',
                        'node': {
                            'description': 'Cats 7',
                            'name': 'dataset7'
                        }
                    },
                    {
                        'cursor': 'Nw==',
                        'node': {
                            'description': 'Cats 8',
                            'name': 'dataset8'
                        }
                    },
                    {
                        'cursor': 'OA==',
                        'node': {
                            'description': 'Cats 9',
                            'name': 'dataset9'
                        }
                    },
                    {
                        'cursor': 'OQ==',
                        'node': {
                            'description': 'Cats other',
                            'name': 'dataset-other'
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
}

snapshots['TestDatasetQueries.test_pagination_sort_az_reverse 1'] = {
    'data': {
        'datasetList': {
            'localDatasets': {
                'edges': [
                    {
                        'cursor': 'MA==',
                        'node': {
                            'datasetType': {
                                'description': 'Scalable Dataset storage provided by your Gigantum account',
                                'name': 'Gigantum Cloud',
                                'storageType': 'gigantum_object_v1'
                            },
                            'description': 'Cats other',
                            'id': 'RGF0YXNldDp0ZXN0MyZkYXRhc2V0LW90aGVy',
                            'name': 'dataset-other'
                        }
                    },
                    {
                        'cursor': 'MQ==',
                        'node': {
                            'datasetType': {
                                'description': 'Scalable Dataset storage provided by your Gigantum account',
                                'name': 'Gigantum Cloud',
                                'storageType': 'gigantum_object_v1'
                            },
                            'description': 'Cats 9',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ5',
                            'name': 'dataset9'
                        }
                    },
                    {
                        'cursor': 'Mg==',
                        'node': {
                            'datasetType': {
                                'description': 'Scalable Dataset storage provided by your Gigantum account',
                                'name': 'Gigantum Cloud',
                                'storageType': 'gigantum_object_v1'
                            },
                            'description': 'Cats 8',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ4',
                            'name': 'dataset8'
                        }
                    },
                    {
                        'cursor': 'Mw==',
                        'node': {
                            'datasetType': {
                                'description': 'Scalable Dataset storage provided by your Gigantum account',
                                'name': 'Gigantum Cloud',
                                'storageType': 'gigantum_object_v1'
                            },
                            'description': 'Cats 7',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ3',
                            'name': 'dataset7'
                        }
                    },
                    {
                        'cursor': 'NA==',
                        'node': {
                            'datasetType': {
                                'description': 'Scalable Dataset storage provided by your Gigantum account',
                                'name': 'Gigantum Cloud',
                                'storageType': 'gigantum_object_v1'
                            },
                            'description': 'Cats 6',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ2',
                            'name': 'dataset6'
                        }
                    },
                    {
                        'cursor': 'NQ==',
                        'node': {
                            'datasetType': {
                                'description': 'Scalable Dataset storage provided by your Gigantum account',
                                'name': 'Gigantum Cloud',
                                'storageType': 'gigantum_object_v1'
                            },
                            'description': 'Cats 5',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ1',
                            'name': 'dataset5'
                        }
                    },
                    {
                        'cursor': 'Ng==',
                        'node': {
                            'datasetType': {
                                'description': 'Scalable Dataset storage provided by your Gigantum account',
                                'name': 'Gigantum Cloud',
                                'storageType': 'gigantum_object_v1'
                            },
                            'description': 'Cats 4',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ0',
                            'name': 'dataset4'
                        }
                    },
                    {
                        'cursor': 'Nw==',
                        'node': {
                            'datasetType': {
                                'description': 'Scalable Dataset storage provided by your Gigantum account',
                                'name': 'Gigantum Cloud',
                                'storageType': 'gigantum_object_v1'
                            },
                            'description': 'Cats 3',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQz',
                            'name': 'dataset3'
                        }
                    },
                    {
                        'cursor': 'OA==',
                        'node': {
                            'datasetType': {
                                'description': 'Scalable Dataset storage provided by your Gigantum account',
                                'name': 'Gigantum Cloud',
                                'storageType': 'gigantum_object_v1'
                            },
                            'description': 'Cats 2',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQy',
                            'name': 'dataset2'
                        }
                    },
                    {
                        'cursor': 'OQ==',
                        'node': {
                            'datasetType': {
                                'description': 'Scalable Dataset storage provided by your Gigantum account',
                                'name': 'Gigantum Cloud',
                                'storageType': 'gigantum_object_v1'
                            },
                            'description': 'Cats 1',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQx',
                            'name': 'dataset1'
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
}

snapshots['TestDatasetQueries.test_pagination_sort_create 1'] = {
    'data': {
        'datasetList': {
            'localDatasets': {
                'edges': [
                    {
                        'cursor': 'MA==',
                        'node': {
                            'description': 'Cats 2',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQy',
                            'name': 'dataset2'
                        }
                    },
                    {
                        'cursor': 'MQ==',
                        'node': {
                            'description': 'Cats 3',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQz',
                            'name': 'dataset3'
                        }
                    },
                    {
                        'cursor': 'Mg==',
                        'node': {
                            'description': 'Cats 4',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ0',
                            'name': 'dataset4'
                        }
                    },
                    {
                        'cursor': 'Mw==',
                        'node': {
                            'description': 'Cats 5',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ1',
                            'name': 'dataset5'
                        }
                    },
                    {
                        'cursor': 'NA==',
                        'node': {
                            'description': 'Cats 6',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ2',
                            'name': 'dataset6'
                        }
                    },
                    {
                        'cursor': 'NQ==',
                        'node': {
                            'description': 'Cats 7',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ3',
                            'name': 'dataset7'
                        }
                    },
                    {
                        'cursor': 'Ng==',
                        'node': {
                            'description': 'Cats 8',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ4',
                            'name': 'dataset8'
                        }
                    },
                    {
                        'cursor': 'Nw==',
                        'node': {
                            'description': 'Cats 9',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ5',
                            'name': 'dataset9'
                        }
                    },
                    {
                        'cursor': 'OA==',
                        'node': {
                            'description': 'Cats other',
                            'id': 'RGF0YXNldDp0ZXN0MyZkYXRhc2V0LW90aGVy',
                            'name': 'dataset-other'
                        }
                    },
                    {
                        'cursor': 'OQ==',
                        'node': {
                            'description': 'Cats 1',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQx',
                            'name': 'dataset1'
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
}

snapshots['TestDatasetQueries.test_pagination_sort_create_desc 1'] = {
    'data': {
        'datasetList': {
            'localDatasets': {
                'edges': [
                    {
                        'cursor': 'MA==',
                        'node': {
                            'description': 'Cats 1',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQx',
                            'name': 'dataset1'
                        }
                    },
                    {
                        'cursor': 'MQ==',
                        'node': {
                            'description': 'Cats other',
                            'id': 'RGF0YXNldDp0ZXN0MyZkYXRhc2V0LW90aGVy',
                            'name': 'dataset-other'
                        }
                    },
                    {
                        'cursor': 'Mg==',
                        'node': {
                            'description': 'Cats 9',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ5',
                            'name': 'dataset9'
                        }
                    },
                    {
                        'cursor': 'Mw==',
                        'node': {
                            'description': 'Cats 8',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ4',
                            'name': 'dataset8'
                        }
                    },
                    {
                        'cursor': 'NA==',
                        'node': {
                            'description': 'Cats 7',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ3',
                            'name': 'dataset7'
                        }
                    },
                    {
                        'cursor': 'NQ==',
                        'node': {
                            'description': 'Cats 6',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ2',
                            'name': 'dataset6'
                        }
                    },
                    {
                        'cursor': 'Ng==',
                        'node': {
                            'description': 'Cats 5',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ1',
                            'name': 'dataset5'
                        }
                    },
                    {
                        'cursor': 'Nw==',
                        'node': {
                            'description': 'Cats 4',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ0',
                            'name': 'dataset4'
                        }
                    },
                    {
                        'cursor': 'OA==',
                        'node': {
                            'description': 'Cats 3',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQz',
                            'name': 'dataset3'
                        }
                    },
                    {
                        'cursor': 'OQ==',
                        'node': {
                            'description': 'Cats 2',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQy',
                            'name': 'dataset2'
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
}

snapshots['TestDatasetQueries.test_pagination_sort_modified 1'] = {
    'data': {
        'datasetList': {
            'localDatasets': {
                'edges': [
                    {
                        'cursor': 'MA==',
                        'node': {
                            'description': 'Cats 1',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQx',
                            'name': 'dataset1'
                        }
                    },
                    {
                        'cursor': 'MQ==',
                        'node': {
                            'description': 'Cats other',
                            'id': 'RGF0YXNldDp0ZXN0MyZkYXRhc2V0LW90aGVy',
                            'name': 'dataset-other'
                        }
                    },
                    {
                        'cursor': 'Mg==',
                        'node': {
                            'description': 'Cats 9',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ5',
                            'name': 'dataset9'
                        }
                    },
                    {
                        'cursor': 'Mw==',
                        'node': {
                            'description': 'Cats 8',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ4',
                            'name': 'dataset8'
                        }
                    },
                    {
                        'cursor': 'NA==',
                        'node': {
                            'description': 'Cats 7',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ3',
                            'name': 'dataset7'
                        }
                    },
                    {
                        'cursor': 'NQ==',
                        'node': {
                            'description': 'Cats 6',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ2',
                            'name': 'dataset6'
                        }
                    },
                    {
                        'cursor': 'Ng==',
                        'node': {
                            'description': 'Cats 5',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ1',
                            'name': 'dataset5'
                        }
                    },
                    {
                        'cursor': 'Nw==',
                        'node': {
                            'description': 'Cats 4',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ0',
                            'name': 'dataset4'
                        }
                    },
                    {
                        'cursor': 'OA==',
                        'node': {
                            'description': 'Cats 3',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQz',
                            'name': 'dataset3'
                        }
                    },
                    {
                        'cursor': 'OQ==',
                        'node': {
                            'description': 'Cats 2',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQy',
                            'name': 'dataset2'
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
}

snapshots['TestDatasetQueries.test_pagination_sort_modified 2'] = {
    'data': {
        'datasetList': {
            'localDatasets': {
                'edges': [
                    {
                        'cursor': 'MA==',
                        'node': {
                            'description': 'Cats 4',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ0',
                            'name': 'dataset4'
                        }
                    },
                    {
                        'cursor': 'MQ==',
                        'node': {
                            'description': 'Cats 1',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQx',
                            'name': 'dataset1'
                        }
                    },
                    {
                        'cursor': 'Mg==',
                        'node': {
                            'description': 'Cats other',
                            'id': 'RGF0YXNldDp0ZXN0MyZkYXRhc2V0LW90aGVy',
                            'name': 'dataset-other'
                        }
                    },
                    {
                        'cursor': 'Mw==',
                        'node': {
                            'description': 'Cats 9',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ5',
                            'name': 'dataset9'
                        }
                    },
                    {
                        'cursor': 'NA==',
                        'node': {
                            'description': 'Cats 8',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ4',
                            'name': 'dataset8'
                        }
                    },
                    {
                        'cursor': 'NQ==',
                        'node': {
                            'description': 'Cats 7',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ3',
                            'name': 'dataset7'
                        }
                    },
                    {
                        'cursor': 'Ng==',
                        'node': {
                            'description': 'Cats 6',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ2',
                            'name': 'dataset6'
                        }
                    },
                    {
                        'cursor': 'Nw==',
                        'node': {
                            'description': 'Cats 5',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ1',
                            'name': 'dataset5'
                        }
                    },
                    {
                        'cursor': 'OA==',
                        'node': {
                            'description': 'Cats 3',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQz',
                            'name': 'dataset3'
                        }
                    },
                    {
                        'cursor': 'OQ==',
                        'node': {
                            'description': 'Cats 2',
                            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQy',
                            'name': 'dataset2'
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
}

snapshots['TestDatasetQueries.test_pagination 1'] = {
    'data': {
        'datasetList': {
            'localDatasets': {
                'edges': [
                    {
                        'cursor': 'MA==',
                        'node': {
                            'description': 'Cats 1',
                            'name': 'dataset1'
                        }
                    },
                    {
                        'cursor': 'MQ==',
                        'node': {
                            'description': 'Cats 2',
                            'name': 'dataset2'
                        }
                    }
                ],
                'pageInfo': {
                    'hasNextPage': True,
                    'hasPreviousPage': False
                }
            }
        }
    }
}

snapshots['TestDatasetQueries.test_pagination 2'] = {
    'data': {
        'datasetList': {
            'localDatasets': {
                'edges': [
                    {
                        'cursor': 'Mg==',
                        'node': {
                            'description': 'Cats 3',
                            'name': 'dataset3'
                        }
                    },
                    {
                        'cursor': 'Mw==',
                        'node': {
                            'description': 'Cats 4',
                            'name': 'dataset4'
                        }
                    },
                    {
                        'cursor': 'NA==',
                        'node': {
                            'description': 'Cats 5',
                            'name': 'dataset5'
                        }
                    },
                    {
                        'cursor': 'NQ==',
                        'node': {
                            'description': 'Cats 6',
                            'name': 'dataset6'
                        }
                    },
                    {
                        'cursor': 'Ng==',
                        'node': {
                            'description': 'Cats 7',
                            'name': 'dataset7'
                        }
                    }
                ],
                'pageInfo': {
                    'hasNextPage': True,
                    'hasPreviousPage': False
                }
            }
        }
    }
}

snapshots['TestDatasetQueries.test_pagination 3'] = {
    'data': {
        'datasetList': {
            'localDatasets': {
                'edges': [
                    {
                        'cursor': 'Nw==',
                        'node': {
                            'description': 'Cats 8',
                            'name': 'dataset8'
                        }
                    },
                    {
                        'cursor': 'OA==',
                        'node': {
                            'description': 'Cats 9',
                            'name': 'dataset9'
                        }
                    },
                    {
                        'cursor': 'OQ==',
                        'node': {
                            'description': 'Cats other',
                            'name': 'dataset-other'
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
}

snapshots['TestDatasetQueries.test_pagination 4'] = {
    'data': {
        'datasetList': {
            'localDatasets': {
                'edges': [
                ],
                'pageInfo': {
                    'hasNextPage': False,
                    'hasPreviousPage': False
                }
            }
        }
    }
}

snapshots['TestDatasetQueries.test_get_dataset_all_fields 1'] = {
    'data': {
        'dataset': {
            'activityRecords': {
                'edges': [
                    {
                        'node': {
                            'importance': 255,
                            'message': 'Created new Dataset: default/dataset8',
                            'show': True,
                            'tags': [
                            ],
                            'type': 'DATASET'
                        }
                    },
                    {
                        'node': {
                            'importance': 255,
                            'message': 'Updated Dataset storage backend configuration',
                            'show': True,
                            'tags': [
                                'config'
                            ],
                            'type': 'DATASET'
                        }
                    }
                ],
                'pageInfo': {
                    'hasNextPage': True,
                    'hasPreviousPage': False
                }
            },
            'datasetType': {
                'description': 'Scalable Dataset storage provided by your Gigantum account',
                'icon': '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',
                'id': 'RGF0YXNldFR5cGU6Z2lnYW50dW1fb2JqZWN0X3Yx',
                'name': 'Gigantum Cloud',
                'readme': '''Gigantum Cloud Datasets are backed by a scalable object storage service that is linked to
your Gigantum account and credentials. It provides efficient storage at the file level and works seamlessly with the 
Client.

This dataset type is fully managed. That means as you modify data, each version will be tracked independently. Syncing
to Gigantum Cloud will count towards your storage quota and include all versions of files.
''',
                'storageType': 'gigantum_object_v1',
                'tags': [
                    'gigantum'
                ]
            },
            'description': 'Cats 8',
            'id': 'RGF0YXNldDpkZWZhdWx0JmRhdGFzZXQ4',
            'name': 'dataset8',
            'schemaVersion': 1
        }
    }
}
