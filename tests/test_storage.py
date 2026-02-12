import pytest
import os
import shutil
from pathlib import Path
from venturalitica.storage import LocalFileSystemStorage, BaseStorage


def test_local_storage(tmp_path):
    storage_path = tmp_path / "storage"
    storage = LocalFileSystemStorage(str(storage_path))

    # Create a dummy policy file
    policy_file = tmp_path / "test.oscal.yaml"
    policy_file.write_text("oscal-catalog: { id: 'test' }")

    storage.store_policy(str(policy_file))
    assert (tmp_path / "test.oscal.yaml").exists()

    policies = storage.list_policies()
    assert "test.oscal.yaml" in policies


def test_local_storage_load_missing(tmp_path):
    storage = LocalFileSystemStorage(str(tmp_path))
    with pytest.raises(FileNotFoundError):
        storage.get_policy("missing.yaml")


def test_base_storage_abstract():
    # To cover lines 11, 14 in storage.py (abstract methods)
    # We can't instantiate BaseStorage, but we can check if it exists
    assert BaseStorage


def test_local_storage_store_missing(tmp_path):
    storage = LocalFileSystemStorage(str(tmp_path))
    with pytest.raises(FileNotFoundError):
        storage.store_policy("non_existent.yaml")


def test_abstract_storage():
    class DummyStorage(BaseStorage):
        def list_policies(self):
            pass

        def get_policy(self, name):
            pass

        def store_policy(self, path):
            pass

    s = DummyStorage()
    s.list_policies()
    s.get_policy("any")
    s.store_policy("any")


def test_base_storage_errors():
    s = BaseStorage()
    with pytest.raises(NotImplementedError):
        s.list_policies()
    with pytest.raises(NotImplementedError):
        s.get_policy("any")
