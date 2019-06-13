import pytest

from gtmcore.exceptions import GigantumException
from gtmcore.fixtures.datasets import mock_enable_unmanaged_for_testing
from gtmcore.dataset.storage import get_storage_backend, get_storage_backend_descriptions
from gtmcore.dataset.storage.gigantum import GigantumObjectStore
from gtmcore.dataset.storage.local import LocalFilesystem


class TestStorageBackendParent(object):
    def test_get_storage_backend_descriptions(self, mock_enable_unmanaged_for_testing):
        metadata = get_storage_backend_descriptions()

        assert len(metadata) == 3
        assert metadata[0].get("name") == "Gigantum Cloud"
        assert metadata[0].get("tags") == ['gigantum']
        assert metadata[0].get("storage_type") == 'gigantum_object_v1'
        assert "iVBOR" in metadata[0].get("icon")

    def test_get_storage_backend_managed(self):
        sb = get_storage_backend("gigantum_object_v1")

        assert isinstance(sb, GigantumObjectStore)

    def test_get_storage_backend_unmanaged(self, mock_enable_unmanaged_for_testing):
        sb = get_storage_backend("local_filesystem")

        assert isinstance(sb, LocalFilesystem)

    def test_get_storage_backend_invalid(self):
        with pytest.raises(GigantumException):
            get_storage_backend("dfsakjldfghkljfgds")


