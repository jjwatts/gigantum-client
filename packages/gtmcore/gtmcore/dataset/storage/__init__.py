import importlib
from typing import List
from gtmcore.exceptions import GigantumException
from gtmcore.dataset.storage.backend import StorageBackend

SUPPORTED_STORAGE_BACKENDS = {"gigantum_object_v1": ("gtmcore.dataset.storage.gigantum", "GigantumObjectStore")}


def get_storage_backend(storage_type: str) -> StorageBackend:
    """

    Args:
        storage_type(str): Identifier to load class

    Returns:
        gtmcore.dataset.storage.backend.StorageBackend
    """
    if storage_type in SUPPORTED_STORAGE_BACKENDS.keys():
        module, package = SUPPORTED_STORAGE_BACKENDS.get(storage_type)  # type: ignore
        imported = importlib.import_module(module, package)
        class_instance = getattr(imported, package)
        return class_instance()
    else:
        raise GigantumException(f"Unsupported Dataset Storage Type: {storage_type}")


def get_storage_backend_descriptions() -> List[dict]:
    """

    Returns:

    """
    result = list()
    for backend in SUPPORTED_STORAGE_BACKENDS:
        result.append(get_storage_backend(backend).metadata)

    return result
