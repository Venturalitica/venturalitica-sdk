from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import hashlib
from datetime import datetime

class Artifact(ABC):
    """
    Abstract base class for any data asset or model artifact tracked by the governance system.
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

class SQLArtifact(Artifact):
    """
    Represents a SQL query or table source.
    """
    def __init__(self, query: str, connection_string: str = "HIDDEN", description: Optional[str] = None):
        super().__init__("SQL Query", description)
        self.query = query
        self.connection = connection_string

    def get_fingerprint(self) -> str:
        # Hash the query logic itself
        return hashlib.sha256(self.query.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "query": self.query,
            "fingerprint": self.get_fingerprint()
        })
        return data

class S3Artifact(Artifact):
    """
    Represents an object in S3-compatible storage.
    """
    def __init__(self, bucket: str, key: str, etag: Optional[str] = None, description: Optional[str] = None):
        super().__init__(f"s3://{bucket}/{key}", description)
        self.bucket = bucket
        self.key = key
        self.etag = etag

    def get_fingerprint(self) -> str:
        # Use ETag if provided (it's usually the MD5), otherwise hash the URI
        if self.etag:
            return self.etag
        return hashlib.sha256(f"{self.bucket}/{self.key}".encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "uri": f"s3://{self.bucket}/{self.key}",
            "fingerprint": self.get_fingerprint()
        })
        return data
