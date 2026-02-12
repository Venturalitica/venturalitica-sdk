from typing import Dict, Any, Optional, List
from .base import BaseProbe


class ArtifactProbe(BaseProbe):
    """
    Captures input datasets and output artifacts (models, plots).
    Tracks deep metadata (hashes, URIs, SQL queries) to ensure data lineage.
    """

    def __init__(
        self, inputs: Optional[List[Any]] = None, outputs: Optional[List[Any]] = None
    ):
        super().__init__("Data & Artifacts")
        self.inputs = self._normalize_artifacts(inputs or [])
        self.outputs = self._normalize_artifacts(outputs or [])
        self._start_snapshots: Dict[str, Any] = {}

    def _normalize_artifacts(self, items: list) -> list:
        from venturalitica.artifacts import Artifact, FileArtifact

        normalized = []
        for item in items:
            if isinstance(item, str):
                normalized.append(FileArtifact(item))
            elif isinstance(item, Artifact):
                normalized.append(item)
        return normalized

    def start(self):
        # Snapshot input state at start
        for inp in self.inputs:
            self._start_snapshots[inp.name] = inp.to_dict()

    def stop(self) -> Dict[str, Any]:
        # Snapshot output state at stop
        output_snapshots = {}
        for out in self.outputs:
            output_snapshots[out.name] = out.to_dict()

        self.results = {"inputs": self._start_snapshots, "outputs": output_snapshots}
        return self.results

    def get_summary(self) -> str:
        in_count = len(self.inputs)
        out_count = len(self.outputs)
        return f"  💾 [Artifacts] Inputs: {in_count} | Outputs: {out_count} (Deep Integration)"
