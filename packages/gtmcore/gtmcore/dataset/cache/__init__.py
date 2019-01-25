import importlib
from typing import Callable
from gtmcore.exceptions import GigantumException
from gtmcore.dataset.cache.cache import CacheManager
from gtmcore.configuration import Configuration

SUPPORTED_CACHE_MANAGERS = {"host": ("gtmcore.dataset.cache.filesystem",
                                     "HostFilesystemCache")}


def get_cache_manager_class(config: Configuration) -> Callable:
    """

    Args:
        config(Configuration): Configuration for the client

    Returns:
        gtmcore.dataset.cache.CacheManager
    """
    dataset_config = config.config.get('datasets')
    if not dataset_config:
        # Fallback to default host manager
        manager_str = 'host'
    else:
        manager_str = dataset_config.get('cache_manager')

    if manager_str in SUPPORTED_CACHE_MANAGERS.keys():
        module, package = SUPPORTED_CACHE_MANAGERS.get(manager_str)  # type: ignore
        imported = importlib.import_module(module, package)
        class_instance = getattr(imported, package)
        return class_instance
    else:
        raise GigantumException(f"Unsupported Dataset File Cache Manager: {manager_str}")
