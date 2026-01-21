import os
import shutil
from pathlib import Path
from typing import List, Optional, Union
from .loader import OSCALPolicyLoader
from .models import InternalPolicy

class BaseStorage:
    """Abstract base class for policy storage."""
    def list_policies(self) -> List[str]:
        raise NotImplementedError
    
    def get_policy(self, name: str) -> InternalPolicy:
        raise NotImplementedError

class LocalFileSystemStorage(BaseStorage):
    """Storage implementation for local file system."""
    def __init__(self, base_path: Union[str, Path] = ".venturalitica/policies"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def list_policies(self) -> List[str]:
        """Lists all OSCAL files in the storage."""
        return [f.name for f in self.base_path.glob("*.oscal.yaml")]

    def get_policy(self, name: str) -> InternalPolicy:
        """Loads a specific policy by name or path."""
        # Check if name is a full path or just a filename in base_path
        policy_path = Path(name)
        if not policy_path.exists():
            policy_path = self.base_path / name
            if not policy_path.exists():
                # Try adding extension if missing
                if not name.endswith(".oscal.yaml"):
                    policy_path = self.base_path / f"{name}.oscal.yaml"
        
        if not policy_path.exists():
            raise FileNotFoundError(f"Policy not found: {name}")
            
        loader = OSCALPolicyLoader(policy_path)
        return loader.load()

    def store_policy(self, path: Union[str, Path]):
        """Copies an external OSCAL file to local storage."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Source policy not found: {path}")
        
        shutil.copy(path, self.base_path / path.name)
