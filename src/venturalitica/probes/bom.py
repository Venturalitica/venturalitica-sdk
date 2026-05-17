"""BOM (Software Bill of Materials) probe.

Emits a CycloneDX 1.6 JSON document describing the AI system's third-party
dependencies + ML model classes scanned from the run directory. The
serialised BOM is persisted to disk so `vl push` can attach it to the
OSCAL `assessment-results` back-matter (class=`cyclonedx-bom`); the SaaS
`bom-ingestion.service` upserts each component as
ManagedItem(ICT_THIRD_PARTY) + AISystemManagedItemLink(DEPENDS_ON) for
DORA Art.28(9) supply-chain inventory.

The probe envelope itself stays backward-compatible with the previous
shape (`component_count`, `bom`, `bom_path`) so the trace
(`probes/trace.py`) and CLI consumers keep working. New fields are
additive:

- `_format`          (`"CycloneDX"`)
- `_format_version`  (`"1.6"`)
- `components_count` mirror of `component_count` for readability
- `components`       — flat list of `{name, version, type, purl, license}`
  dicts so callers that don't want to parse the full CycloneDX JSON have
  a lightweight projection (matches what the SaaS ingester ultimately
  unpacks into ManagedItem rows).
"""

import json
import os
from typing import Any, Dict, List, Optional

from venturalitica.session import GovernanceSession

from .base import BaseProbe

# Schema declaration baked into the payload so downstream consumers can
# validate against the right spec without re-discovering it from the JSON.
_CYCLONEDX_FORMAT = "CycloneDX"
_CYCLONEDX_VERSION = "1.6"


def _project_components(bom_json: Dict[str, Any]) -> List[Dict[str, Optional[str]]]:
    """Flatten cyclonedx components[] into a JSON-RPC-friendly projection.

    Mirrors the fields the SaaS `bom-ingestion.service.ts` reads when
    upserting ManagedItem rows (`name`, `version`, `type`, `purl`, the
    first license id/name, `bom-ref`).
    """
    out: List[Dict[str, Optional[str]]] = []
    for comp in bom_json.get("components") or []:
        if not isinstance(comp, dict):
            continue
        license_id: Optional[str] = None
        licenses = comp.get("licenses") or []
        if licenses and isinstance(licenses[0], dict):
            lic = licenses[0].get("license")
            if isinstance(lic, dict):
                license_id = lic.get("id") or lic.get("name")
        out.append({
            "name": comp.get("name"),
            "version": comp.get("version"),
            "type": comp.get("type"),
            "purl": comp.get("purl"),
            "bom_ref": comp.get("bom-ref"),
            "license": license_id,
        })
    return out


class BOMProbe(BaseProbe):
    """Capture a CycloneDX 1.6 SBOM for the AI system under audit.

    BOM capture is a one-shot snapshot taken at `stop()` — there is no
    continuous monitoring loop. The probe scans the target directory
    once, serialises a CycloneDX 1.6 document, persists it to
    `<session>/bom.json` (or `.venturalitica/bom.json` when the probe
    runs outside a session), and returns a probe payload that embeds
    both the full BOM and a flat projection.
    """

    def __init__(self, target_dir: str = "."):
        super().__init__("bom")
        self.target_dir = target_dir

    def start(self) -> None:
        # BOM capture is a snapshot, no need for continuous monitoring.
        return None

    def stop(self) -> Dict[str, Any]:
        try:
            from venturalitica.scanner import BOMScanner

            scanner = BOMScanner(self.target_dir)
            bom_str = scanner.scan()
            bom_json = json.loads(bom_str)

            # Persist BOM next to other probe outputs so `vl push` can pick
            # it up and embed it in the AR back-matter.
            session = GovernanceSession.get_current()
            if session:
                bom_path = session.base_dir / "bom.json"
                os.makedirs(session.base_dir, exist_ok=True)
                bom_path_str = str(bom_path)
            else:
                os.makedirs(".venturalitica", exist_ok=True)
                bom_path_str = ".venturalitica/bom.json"

            with open(bom_path_str, "w") as f:
                json.dump(bom_json, f, indent=2)

            components = _project_components(bom_json)
            count = len(components)

            self.results = {
                # Back-compat keys — consumed by the trace probe + CLI.
                "component_count": count,
                "bom": bom_json,
                "bom_path": bom_path_str,
                # CycloneDX schema declaration so consumers can validate
                # without re-discovering the spec version from the JSON.
                "_format": _CYCLONEDX_FORMAT,
                "_format_version": _CYCLONEDX_VERSION,
                # Lightweight projection — same fields the SaaS ingester
                # ultimately reads when upserting ManagedItem rows.
                "components_count": count,
                "components": components,
            }
        except Exception as e:
            self.results = {"error": str(e)}

        return self.results

    def get_summary(self) -> str:
        count = self.results.get("component_count")
        if count is not None:
            return f"  📦 [Supply Chain] BOM Captured: {count} components linked."
        return f"  ⚠ [Supply Chain] Failed to capture BOM: {self.results.get('error')}"
