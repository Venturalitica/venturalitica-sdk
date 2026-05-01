"""
OSCAL assessment-plan round-trip contract test.

Source of truth: docs/contracts/oscal-assessment-plan-v1.md
Canonical fixture: tests/fixtures/oscal/assessment-plan.canonical.json

Every prop the IEEE Computer paper's Listing 1 names must survive a
full JSON round-trip. The SDK is the authoritative reader on the
training side; this test fails on any silent prop loss.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURE = (
    Path(__file__).parent / "fixtures" / "oscal" / "assessment-plan.canonical.json"
)


def _load_canonical() -> dict:
    with FIXTURE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _requirements(doc: dict) -> list[dict]:
    plan = doc.get("assessment-plan")
    assert plan is not None, "Fixture MUST have an assessment-plan root (v1 contract §1)"
    impls = plan.get("control-implementations") or []
    return [
        req
        for impl in impls
        for req in (impl.get("implemented-requirements") or [])
    ]


def _props(requirement: dict) -> dict[str, list[str]]:
    """Return {prop_name: [values]} — lists because some props (lifecycle_phase, input:*) repeat."""
    out: dict[str, list[str]] = {}
    for p in requirement.get("props", []) or []:
        out.setdefault(p["name"], []).append(p["value"])
    return out


# ────────────────────────────────────────────────────────────────────────────
# Envelope
# ────────────────────────────────────────────────────────────────────────────


def test_root_is_assessment_plan_only():
    doc = _load_canonical()
    assert list(doc.keys()) == ["assessment-plan"], (
        "Canonical fixture MUST have exactly one root, 'assessment-plan' (v1 §1)."
    )
    assert "system-security-plan" not in doc


def test_metadata_carries_contract_required_fields():
    doc = _load_canonical()
    plan = doc["assessment-plan"]
    assert plan["uuid"], "assessment-plan.uuid MUST be present"
    meta = plan["metadata"]
    assert meta["oscal-version"] == "1.1.2"
    assert meta.get("title")
    assert meta.get("last-modified")


def test_exactly_one_control_implementation_with_requirements():
    doc = _load_canonical()
    impls = doc["assessment-plan"]["control-implementations"]
    assert len(impls) == 1
    assert impls[0]["component-uuid"]
    reqs = impls[0]["implemented-requirements"]
    assert len(reqs) >= 1, "Fixture MUST carry ≥ 1 implemented-requirement"


# ────────────────────────────────────────────────────────────────────────────
# §3 mandatory execution props (every requirement)
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "prop_name",
    [
        "metric_key",
        "operator",
        "threshold",
        "severity",
        "enforcement_mode",
        "evaluation_method",
        "target_type",
        "lifecycle_phase",
    ],
)
def test_every_requirement_has_mandatory_execution_prop(prop_name: str):
    doc = _load_canonical()
    for req in _requirements(doc):
        props = _props(req)
        assert prop_name in props, (
            f"Requirement {req['uuid']} missing mandatory prop '{prop_name}' (v1 §3)."
        )


def test_operator_values_are_symbolic():
    doc = _load_canonical()
    symbolic = {"<", "<=", ">", ">=", "=="}
    for req in _requirements(doc):
        op = _props(req).get("operator", [""])[0]
        assert op in symbolic, f"operator '{op}' must be symbolic (v1 §4)"


def test_enforcement_mode_values_are_canonical():
    doc = _load_canonical()
    canonical = {"block", "warn", "monitor"}
    for req in _requirements(doc):
        em = _props(req).get("enforcement_mode", [""])[0]
        assert em in canonical, f"enforcement_mode '{em}' must be canonical (v1 §4)"


def test_severity_values_are_canonical():
    doc = _load_canonical()
    canonical = {"block", "warn", "info"}
    for req in _requirements(doc):
        sev = _props(req).get("severity", [""])[0]
        assert sev in canonical


def test_evaluation_method_values_are_canonical():
    doc = _load_canonical()
    canonical = {"automated", "human", "hybrid"}
    for req in _requirements(doc):
        em = _props(req).get("evaluation_method", [""])[0]
        assert em in canonical


# ────────────────────────────────────────────────────────────────────────────
# §3 traceability props — at least one requirement uses each
# ────────────────────────────────────────────────────────────────────────────


def test_traceability_props_exercised_somewhere():
    doc = _load_canonical()
    props_used: set[str] = set()
    for req in _requirements(doc):
        props_used.update(_props(req).keys())

    for trace_prop in {
        "risk_id",
        "risk_title",
        "treatment_id",
        "policy_id",
        "objective_id",
        "threshold_justification",
        "risk_acceptance_criteria",
    }:
        assert trace_prop in props_used, (
            f"Canonical fixture MUST exercise '{trace_prop}' on at least one "
            f"requirement so the round-trip test covers it."
        )


def test_input_bindings_are_exercised():
    doc = _load_canonical()
    found = False
    for req in _requirements(doc):
        inputs = [p for p in (req.get("props") or []) if p["name"].startswith("input:")]
        if inputs:
            found = True
            break
    assert found, "Canonical fixture MUST exercise ≥ 1 input:* binding"


# ────────────────────────────────────────────────────────────────────────────
# Round-trip: serialize → parse → every prop survives
# ────────────────────────────────────────────────────────────────────────────


def test_json_roundtrip_preserves_every_prop_byte_for_byte():
    doc = _load_canonical()
    serialized = json.dumps(doc, ensure_ascii=False, sort_keys=False)
    reloaded = json.loads(serialized)

    for orig, copy in zip(_requirements(doc), _requirements(reloaded)):
        assert _props(orig) == _props(copy), (
            f"Requirement {orig['uuid']} prop set changed across JSON round-trip."
        )


def test_yaml_roundtrip_preserves_every_prop():
    # YAML round-trip must not drop repeated keys (lifecycle_phase, input:*).
    yaml = pytest.importorskip("yaml")
    doc = _load_canonical()
    text = yaml.dump(doc, sort_keys=False)
    reloaded = yaml.safe_load(text)
    for orig, copy in zip(_requirements(doc), _requirements(reloaded)):
        assert _props(orig) == _props(copy), (
            f"Requirement {orig['uuid']} prop set changed across YAML round-trip."
        )


# ────────────────────────────────────────────────────────────────────────────
# Negative: no SSP leakage in the fixture
# ────────────────────────────────────────────────────────────────────────────


def test_no_system_security_plan_leakage():
    text = FIXTURE.read_text(encoding="utf-8")
    assert "system-security-plan" not in text, (
        "Canonical fixture MUST NOT reference system-security-plan."
    )
