import pytest

from gtmcore.exceptions import GigantumException
from gtmcore.dataset.storage import get_storage_backend, get_storage_backend_descriptions
from gtmcore.dataset.storage.gigantum import GigantumObjectStore


class TestStorageBackendParent(object):
    def test_get_storage_backend_descriptions(self):
        metadata = get_storage_backend_descriptions()

        assert len(metadata) == 1
        assert metadata[0].get("name") == "Gigantum Cloud"
        assert metadata[0].get("tags") == ['gigantum']
        assert metadata[0].get("storage_type") == 'gigantum_object_v1'
        assert "iVBOR" in metadata[0].get("icon")

    def test_get_storage_backend(self):
        sb = get_storage_backend("gigantum_object_v1")

        assert isinstance(sb, GigantumObjectStore)

    def test_get_storage_backend_invalid(self):

        with pytest.raises(GigantumException):
            get_storage_backend("dfsakjldfghkljfgds")


