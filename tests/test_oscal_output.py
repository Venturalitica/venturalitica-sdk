"""Tests for OSCAL Assessment Results and POA&M generation.

Verifies that the SDK produces valid OSCAL v1.1.2 documents from
ComplianceResult objects, with correct structure, traceability,
and conditional POA&M generation.
"""

import json

import pytest

from venturalitica.models import ComplianceResult
from venturalitica.oscal.builder import AssessmentResultsBuilder, POAMBuilder
from venturalitica.oscal.models import (
    OSCAL_VERSION,
    AssessmentResults,
    PlanOfActionAndMilestones,
)
from venturalitica.oscal.serializer import to_json


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def passing_results():
    return [
        ComplianceResult(
            control_id="credit-data-imbalance",
            description="Minority class >= 20%",
            metric_key="class_imbalance",
            threshold=0.2,
            actual_value=0.429,
            operator="gt",
            passed=True,
            severity="low",
        ),
        ComplianceResult(
            control_id="credit-data-bias",
            description="Gender DI follows Four-Fifths Rule",
            metric_key="disparate_impact",
            threshold=0.8,
            actual_value=0.818,
            operator="gt",
            passed=True,
            severity="high",
        ),
    ]


@pytest.fixture
def mixed_results():
    return [
        ComplianceResult(
            control_id="credit-data-bias",
            description="Gender DI > 0.8",
            metric_key="disparate_impact",
            threshold=0.8,
            actual_value=0.818,
            operator="gt",
            passed=True,
            severity="high",
        ),
        ComplianceResult(
            control_id="credit-age-disparate",
            description="Age DI > 0.5",
            metric_key="disparate_impact",
            threshold=0.5,
            actual_value=0.286,
            operator="gt",
            passed=False,
            severity="high",
        ),
        ComplianceResult(
            control_id="model-accuracy",
            description="Accuracy >= 0.70",
            metric_key="accuracy_score",
            threshold=0.70,
            actual_value=0.795,
            operator="gte",
            passed=True,
            severity="high",
        ),
    ]


@pytest.fixture
def failing_results():
    return [
        ComplianceResult(
            control_id="fail-1",
            description="Must pass",
            metric_key="metric_a",
            threshold=0.5,
            actual_value=0.3,
            operator="gt",
            passed=False,
            severity="critical",
        ),
        ComplianceResult(
            control_id="fail-2",
            description="Must also pass",
            metric_key="metric_b",
            threshold=0.9,
            actual_value=0.1,
            operator="gte",
            passed=False,
            severity="high",
        ),
    ]


# ---------------------------------------------------------------------------
# Assessment Results
# ---------------------------------------------------------------------------

class TestAssessmentResultsBuilder:

    def test_produces_valid_ar(self, mixed_results):
        ar = AssessmentResultsBuilder.build(mixed_results, title="Test")
        assert isinstance(ar, AssessmentResults)
        assert ar.metadata.oscal_version == OSCAL_VERSION
        assert len(ar.results) == 1

    def test_one_observation_per_result(self, mixed_results):
        ar = AssessmentResultsBuilder.build(mixed_results)
        assert len(ar.results[0].observations) == len(mixed_results)

    def test_one_finding_per_result(self, mixed_results):
        ar = AssessmentResultsBuilder.build(mixed_results)
        assert len(ar.results[0].findings) == len(mixed_results)

    def test_risk_only_for_failures(self, mixed_results):
        ar = AssessmentResultsBuilder.build(mixed_results)
        failed_count = sum(1 for r in mixed_results if not r.passed)
        assert len(ar.results[0].risks) == failed_count

    def test_no_risks_when_all_pass(self, passing_results):
        ar = AssessmentResultsBuilder.build(passing_results)
        assert len(ar.results[0].risks) == 0

    def test_finding_status_satisfied(self, passing_results):
        ar = AssessmentResultsBuilder.build(passing_results)
        for finding in ar.results[0].findings:
            assert finding.target.status.state == "satisfied"

    def test_finding_status_not_satisfied(self, failing_results):
        ar = AssessmentResultsBuilder.build(failing_results)
        for finding in ar.results[0].findings:
            assert finding.target.status.state == "not-satisfied"

    def test_observation_links_to_finding(self, mixed_results):
        ar = AssessmentResultsBuilder.build(mixed_results)
        obs_uuids = {o.uuid for o in ar.results[0].observations}
        for finding in ar.results[0].findings:
            for obs_ref in finding.related_observations:
                assert obs_ref.observation_uuid in obs_uuids

    def test_risk_links_to_finding(self, mixed_results):
        ar = AssessmentResultsBuilder.build(mixed_results)
        risk_uuids = {r.uuid for r in ar.results[0].risks}
        for finding in ar.results[0].findings:
            for risk_ref in finding.related_risks:
                assert risk_ref.risk_uuid in risk_uuids

    def test_reviewed_controls_listed(self, mixed_results):
        ar = AssessmentResultsBuilder.build(mixed_results)
        control_ids = set()
        for cs in ar.results[0].reviewed_controls.control_selections:
            for ic in cs.include_controls:
                control_ids.add(ic.control_id)
        expected = {r.control_id for r in mixed_results}
        assert control_ids == expected

    def test_timestamps_propagated(self, mixed_results):
        ar = AssessmentResultsBuilder.build(
            mixed_results,
            start_time="2026-04-04T10:00:00Z",
            end_time="2026-04-04T10:05:00Z",
        )
        assert ar.results[0].start == "2026-04-04T10:00:00Z"
        assert ar.results[0].end == "2026-04-04T10:05:00Z"

    def test_policy_href_stored(self, mixed_results):
        ar = AssessmentResultsBuilder.build(
            mixed_results, policy_href="data_policy.oscal.yaml"
        )
        assert ar.import_ap.href == "data_policy.oscal.yaml"

    def test_evidence_linked_to_observations(self, passing_results):
        evidence = {"bom.json": "/vault/bom.json", "trace.json": "/vault/trace.json"}
        ar = AssessmentResultsBuilder.build(
            passing_results, evidence_artifacts=evidence
        )
        for obs in ar.results[0].observations:
            assert len(obs.relevant_evidence) == 2


# ---------------------------------------------------------------------------
# POA&M
# ---------------------------------------------------------------------------

class TestPOAMBuilder:

    def test_no_poam_when_all_pass(self, passing_results):
        ar = AssessmentResultsBuilder.build(passing_results)
        poam = POAMBuilder.build(ar)
        assert poam is None

    def test_poam_generated_on_failure(self, mixed_results):
        ar = AssessmentResultsBuilder.build(mixed_results)
        poam = POAMBuilder.build(ar)
        assert isinstance(poam, PlanOfActionAndMilestones)

    def test_one_poam_item_per_failure(self, mixed_results):
        ar = AssessmentResultsBuilder.build(mixed_results)
        poam = POAMBuilder.build(ar)
        failed_count = sum(1 for r in mixed_results if not r.passed)
        assert len(poam.poam_items) == failed_count

    def test_poam_items_status_open(self, failing_results):
        ar = AssessmentResultsBuilder.build(failing_results)
        poam = POAMBuilder.build(ar)
        for item in poam.poam_items:
            assert item.status == "open"

    def test_poam_risks_match_ar_risks(self, mixed_results):
        ar = AssessmentResultsBuilder.build(mixed_results)
        poam = POAMBuilder.build(ar)
        ar_risk_uuids = {r.uuid for r in ar.results[0].risks}
        poam_risk_uuids = {r.uuid for r in poam.risks}
        assert poam_risk_uuids == ar_risk_uuids

    def test_poam_item_links_to_risk(self, failing_results):
        ar = AssessmentResultsBuilder.build(failing_results)
        poam = POAMBuilder.build(ar)
        risk_uuids = {r.uuid for r in poam.risks}
        for item in poam.poam_items:
            # POAMItem.related_risks are plain UUID strings (not RiskRef)
            for risk_uuid in item.related_risks:
                assert risk_uuid in risk_uuids


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class TestOSCALSerialization:

    def test_ar_json_is_valid(self, mixed_results):
        ar = AssessmentResultsBuilder.build(mixed_results)
        ar_json = to_json(ar)
        parsed = json.loads(ar_json)
        assert "assessment-results" in parsed

    def test_poam_json_is_valid(self, failing_results):
        ar = AssessmentResultsBuilder.build(failing_results)
        poam = POAMBuilder.build(ar)
        poam_json = to_json(poam)
        parsed = json.loads(poam_json)
        assert "plan-of-action-and-milestones" in parsed

    def test_kebab_case_keys(self, mixed_results):
        ar = AssessmentResultsBuilder.build(mixed_results)
        ar_json = to_json(ar)
        assert "assessment-results" in ar_json
        assert "oscal-version" in ar_json
        assert "last-modified" in ar_json
        assert "reviewed-controls" in ar_json
        assert "control-selections" in ar_json
        assert "related-observations" in ar_json
        # No snake_case keys should leak
        assert "oscal_version" not in ar_json
        assert "last_modified" not in ar_json
        assert "control_selections" not in ar_json

    def test_oscal_version_in_metadata(self, mixed_results):
        ar = AssessmentResultsBuilder.build(mixed_results)
        parsed = json.loads(to_json(ar))
        assert parsed["assessment-results"]["metadata"]["oscal-version"] == "1.1.2"

    def test_no_empty_fields_serialized(self, passing_results):
        ar = AssessmentResultsBuilder.build(passing_results)
        ar_json = to_json(ar)
        parsed = json.loads(ar_json)
        result = parsed["assessment-results"]["results"][0]
        # No risks when all pass, so 'risks' key should be absent
        assert "risks" not in result

    def test_roundtrip_finding_count(self, mixed_results):
        ar = AssessmentResultsBuilder.build(mixed_results)
        parsed = json.loads(to_json(ar))
        findings = parsed["assessment-results"]["results"][0]["findings"]
        assert len(findings) == len(mixed_results)


# ---------------------------------------------------------------------------
# Backward Compatibility
# ---------------------------------------------------------------------------

class TestBackwardCompat:

    def test_compliance_result_unchanged(self, mixed_results):
        """ComplianceResult dataclass should not be modified by OSCAL module."""
        cr = mixed_results[0]
        assert hasattr(cr, "control_id")
        assert hasattr(cr, "passed")
        assert hasattr(cr, "actual_value")
        assert not hasattr(cr, "uuid")  # UUID is only in OSCAL models


# ---------------------------------------------------------------------------
# Profile metadata pass-through (Table 2 proposed properties)
# ---------------------------------------------------------------------------

@pytest.fixture
def failing_result_with_profile_metadata():
    """Failed result carrying the full proposed profile metadata set."""
    return ComplianceResult(
        control_id="credit-age-disparate",
        description="Age DI > 0.5 (EEOC Four-Fifths Rule applied per cohort)",
        metric_key="disparate_impact",
        threshold=0.5,
        actual_value=0.286,
        operator="gt",
        passed=False,
        severity="high",
        metadata={
            # Lifecycle semantics
            "lifecycle_phase": "training",
            "enforcement_mode": "block",
            "evaluation_window": "per-run",
            "evaluation_method": "automated",
            "target_type": "dataset",
            # Traceability chain
            "risk_id": "R-042",
            "treatment_id": "T-017",
            "policy_id": "AI-POL-001",
            "objective_id": "OBJ-003",
            # New extensions from Nannini et al. review
            "risk_acceptance_criteria": "residual DI >= 0.80 after mitigation",
            "threshold_justification": "EEOC Four-Fifths Rule (1978)",
            "stakeholder_consultation_ref": "doi:10.1000/stakeholder-panel-2026",
        },
    )


class TestProfileMetadataPassThrough:
    """Verifies that profile metadata from the policy propagates into AR facets."""

    def test_profile_facets_emitted_for_failure(self, failing_result_with_profile_metadata):
        ar = AssessmentResultsBuilder.build([failing_result_with_profile_metadata])
        assert len(ar.results[0].risks) == 1
        facets = ar.results[0].risks[0].characterizations[0].facets
        facet_names = {f.name for f in facets}
        # Base computation facets remain
        assert {"metric", "actual-value", "threshold", "operator"} <= facet_names
        # Profile metadata carried through as kebab-case facet names
        assert "risk-id" in facet_names
        assert "treatment-id" in facet_names
        assert "policy-id" in facet_names
        assert "objective-id" in facet_names
        assert "lifecycle-phase" in facet_names
        assert "enforcement-mode" in facet_names

    def test_new_extensions_emitted(self, failing_result_with_profile_metadata):
        """risk_acceptance_criteria, threshold_justification, stakeholder_consultation_ref."""
        ar = AssessmentResultsBuilder.build([failing_result_with_profile_metadata])
        facets = ar.results[0].risks[0].characterizations[0].facets
        by_name = {f.name: f.value for f in facets}
        assert by_name["risk-acceptance-criteria"] == "residual DI >= 0.80 after mitigation"
        assert by_name["threshold-justification"] == "EEOC Four-Fifths Rule (1978)"
        assert by_name["stakeholder-consultation-ref"] == "doi:10.1000/stakeholder-panel-2026"

    def test_profile_facets_serialize_as_kebab_case(self, failing_result_with_profile_metadata):
        ar = AssessmentResultsBuilder.build([failing_result_with_profile_metadata])
        ar_json = to_json(ar)
        assert "risk-id" in ar_json
        assert "threshold-justification" in ar_json
        # No snake_case leaks from metadata keys
        assert "risk_id" not in ar_json
        assert "threshold_justification" not in ar_json

    def test_reserved_facets_not_duplicated(self, failing_result_with_profile_metadata):
        """Metadata keys colliding with base facets (metric, actual-value, ...) are dropped."""
        cr = failing_result_with_profile_metadata
        cr.metadata["metric"] = "should-be-ignored"
        cr.metadata["threshold"] = "999"
        ar = AssessmentResultsBuilder.build([cr])
        facets = ar.results[0].risks[0].characterizations[0].facets
        # Base facet still wins (single occurrence, keeps cr.metric_key)
        metric_facets = [f for f in facets if f.name == "metric"]
        assert len(metric_facets) == 1
        assert metric_facets[0].value == cr.metric_key
        threshold_facets = [f for f in facets if f.name == "threshold"]
        assert len(threshold_facets) == 1
        assert threshold_facets[0].value == str(cr.threshold)

    def test_no_facets_without_failure(self, passing_results):
        """Passing results do not create Risk objects; metadata stays in finding context."""
        ar = AssessmentResultsBuilder.build(passing_results)
        assert len(ar.results[0].risks) == 0
