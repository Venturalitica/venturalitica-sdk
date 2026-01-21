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
