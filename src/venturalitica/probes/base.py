from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseProbe(ABC):
    """
    Abstract base class for all monitoring probes.
    Inspired by Martin Fowler's 'Probe Architecture'.
    """

    def __init__(self, name: str):
        self.name = name
        self.results: Dict[str, Any] = {}

    @abstractmethod
    def start(self):
        """Called when the monitor starts."""
        pass

    @abstractmethod
    def stop(self) -> Dict[str, Any]:
        """Called when the monitor stops. Returns a dictionary of results."""
        pass

    def get_summary(self) -> str:
        """Returns a human-readable summary of the probe's findings."""
        return ""
