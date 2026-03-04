import hashlib
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional


class Artifact(ABC):
    """
    Abstract base class for any data asset or model artifact tracked by the assurance system.
    """
    def __init__(self, name: str, description: Optional[str] = None):
        self.name = name
        self.description = description
        self.timestamp = datetime.now().isoformat()
        self.metadata: Dict[str, Any] = {}

    @abstractmethod
    def get_fingerprint(self) -> str:
        """Returns a unique hash/fingerprint of the artifact."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Returns a JSON-serializable representation."""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "description": self.description,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }

class FileArtifact(Artifact):
    """
    Represents a local file (dataset, model, plot).
    """
    def __init__(self, path: str, description: Optional[str] = None):
        super().__init__(os.path.basename(path), description)
        self.path = os.path.abspath(path)
        
    def get_fingerprint(self) -> str:
        if not os.path.exists(self.path):
            return "MISSING"
        sha256_hash = hashlib.sha256()
        with open(self.path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "path": self.path,
            "fingerprint": self.get_fingerprint()
        })
        return data

