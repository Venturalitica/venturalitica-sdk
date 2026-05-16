"""Builders that transform SDK ComplianceResult objects into OSCAL documents.

The builders act as an adapter layer: the SDK's internal representation
(ComplianceResult) remains unchanged for backward compatibility, while
the OSCAL layer produces standards-compliant Assessment Results and POA&M.
"""

import json
from typing import Any, Dict, List, Optional

from ..models import ComplianceResult
from .models import (
    AssessmentResults,
    CharacterizationFacet,
    ControlSelection,
    FindingTarget,
    FindingTargetStatus,
    ImportAP,
    IncludeControl,
    ObservationRef,
    OSCALFinding,
    OSCALMetadata,
    OSCALObservation,
    OSCALProp,
    OSCALResult,
    OSCALRisk,
    PlanOfActionAndMilestones,
    POAMItem,
    RelevantEvidence,
    ReviewedControls,
    RiskCharacterization,
    RiskRef,
)


class AssessmentResultsBuilder:
    """Builds an OSCAL Assessment Results document from ComplianceResult list."""

    @staticmethod
    def build(
        results: List[ComplianceResult],
        *,
        title: str = "AI Assurance Assessment Results",
        policy_href: str = "",
        start_time: str = "",
        end_time: str = "",
        evidence_artifacts: Optional[Dict[str, str]] = None,
        ai_system_uuid: str = "",
        ai_system_version_uuid: str = "",
        trace_id: str = "",
        probe_results: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> AssessmentResults:
        """Convert enforce() results into an OSCAL Assessment Results document.

        Args:
            results: List of ComplianceResult from enforce().
            title: Human-readable title for the assessment.
            policy_href: Path to the OSCAL policy file used.
            start_time: ISO 8601 timestamp of assessment start.
            end_time: ISO 8601 timestamp of assessment end.
            evidence_artifacts: Map of artifact names to file paths/hashes
                                (from probes) to link as evidence.

        Returns:
            A fully populated AssessmentResults ready for serialization.
        """
        evidence_artifacts = evidence_artifacts or {}

        observations: List[OSCALObservation] = []
        findings: List[OSCALFinding] = []
        risks: List[OSCALRisk] = []
        control_selections: List[ControlSelection] = []

        for cr in results:
            # --- Observation ---
            evidence_refs = [
                RelevantEvidence(href=href, description=name)
                for name, href in evidence_artifacts.items()
            ]

            # `types=['control-objective']` is the discriminator the SaaS AR
            # ingester (`oscal-ar-ingestion.service.ts:extractMetricsFromResult`)
            # uses to tell metric-evaluation observations apart from BOM
            # component declarations. The structured `props` carry the
            # ComplianceResult fields verbatim — without them the platform
            # parser drops the observation and `TechnicalMetric` /
            # `RiskEvaluation` rows stay empty.
            obs_props: List[OSCALProp] = [
                OSCALProp(name="control-id", value=cr.control_id),
                OSCALProp(name="metric-key", value=cr.metric_key),
                OSCALProp(name="actual-value", value=str(cr.actual_value)),
                OSCALProp(name="threshold", value=str(cr.threshold)),
                OSCALProp(name="operator", value=cr.operator),
            ]
            if cr.severity:
                obs_props.append(OSCALProp(name="severity", value=cr.severity))

            obs = OSCALObservation(
                title=f"Evaluation of {cr.control_id}",
                description=(
                    f"Metric {cr.metric_key} evaluated: "
                    f"{cr.actual_value} {cr.operator} {cr.threshold}. "
                    f"Result: {'PASS' if cr.passed else 'FAIL'}."
                ),
                types=["control-objective"],
                collected=end_time or "",
                relevant_evidence=evidence_refs,
                props=obs_props,
            )
            observations.append(obs)

            # --- Finding ---
            state = "satisfied" if cr.passed else "not-satisfied"
            finding = OSCALFinding(
                title=f"{'Conformity' if cr.passed else 'Non-conformity'}: {cr.control_id}",
                description=cr.description,
                target=FindingTarget(
                    target_id=cr.control_id,
                    status=FindingTargetStatus(state=state),
                ),
                related_observations=[ObservationRef(observation_uuid=obs.uuid)],
            )

            # --- Risk (only for failures) ---
            if not cr.passed:
                # Base facets: the computation itself.
                facets = [
                    CharacterizationFacet(name="metric", value=cr.metric_key),
                    CharacterizationFacet(name="actual-value", value=str(cr.actual_value)),
                    CharacterizationFacet(name="threshold", value=str(cr.threshold)),
                    CharacterizationFacet(name="operator", value=cr.operator),
                ]
                # Additional facets: profile metadata propagated from the policy
                # (e.g., risk_id, treatment_id, policy_id, objective_id,
                # lifecycle_phase, enforcement_mode, risk_acceptance_criteria,
                # threshold_justification, stakeholder_consultation_ref).
                # OSCAL facet names use kebab-case convention.
                reserved = {"metric", "actual-value", "threshold", "operator"}
                for key, value in (cr.metadata or {}).items():
                    if value is None:
                        continue
                    facet_name = key.replace("_", "-")
                    if facet_name in reserved:
                        continue
                    facets.append(
                        CharacterizationFacet(name=facet_name, value=str(value))
                    )

                risk = OSCALRisk(
                    title=f"Non-conformity: {cr.control_id}",
                    description=(
                        f"Control {cr.control_id} failed: "
                        f"{cr.metric_key}={cr.actual_value} "
                        f"does not satisfy {cr.operator} {cr.threshold}."
                    ),
                    statement=(
                        f"If {cr.metric_key} remains at {cr.actual_value} "
                        f"(threshold: {cr.operator} {cr.threshold}), "
                        f"the system may not meet the requirements of "
                        f"the applicable regulation."
                    ),
                    status="open",
                    characterizations=[RiskCharacterization(facets=facets)],
                )
                risks.append(risk)
                finding.related_risks = [RiskRef(risk_uuid=risk.uuid)]

            findings.append(finding)

            # --- Reviewed control ---
            control_selections.append(
                IncludeControl(control_id=cr.control_id)
            )

        # --- Assemble result ---
        oscal_result = OSCALResult(
            title=title,
            description=f"Assessment of {len(results)} controls",
            start=start_time,
            end=end_time,
            reviewed_controls=ReviewedControls(
                control_selections=[
                    ControlSelection(include_controls=control_selections)
                ]
            ),
            observations=observations,
            findings=findings,
            risks=risks,
        )

        # Paper-coherent tenant binding: the platform's AR ingester reads
        # these props to resolve AISystemVersion by UUID (no "latest" fallback).
        binding_props: List[OSCALProp] = []
        if ai_system_uuid:
            binding_props.append(OSCALProp(name="ai-system-uuid", value=ai_system_uuid))
        if ai_system_version_uuid:
            binding_props.append(
                OSCALProp(name="ai-system-version-uuid", value=ai_system_version_uuid)
            )
        if trace_id:
            binding_props.append(OSCALProp(name="trace-id", value=trace_id))

        # Probe telemetry — one prop per probe with a JSON-encoded value
        # so the SaaS ingester can surface the full payload (carbon, BOM,
        # handshake attestation, …) on the AssuranceTrace cockpit. Prop
        # name prefix `probe.` (NIST regex forbids `:`); mirrors the
        # `input.` convention used elsewhere in the contract.
        for probe_name, payload in (probe_results or {}).items():
            if not isinstance(payload, dict) or not payload:
                continue
            try:
                encoded = json.dumps(payload, default=str, sort_keys=True)
            except (TypeError, ValueError):
                continue
            binding_props.append(
                OSCALProp(name=f"probe.{probe_name}", value=encoded)
            )

        return AssessmentResults(
            metadata=OSCALMetadata(title=title, props=binding_props),
            # NIST OSCAL assessment-results requires import-ap; when no
            # policy path was provided, emit a fragment-only self-reference
            # (the SaaS ingester stores the href as opaque metadata and does
            # not dereference it).
            import_ap=ImportAP(href=policy_href or "#assessment-plan"),
            results=[oscal_result],
        )


class POAMBuilder:
    """Builds an OSCAL POA&M document from Assessment Results."""

    @staticmethod
    def build(ar: AssessmentResults) -> Optional[PlanOfActionAndMilestones]:
        """Generate a POA&M from failed controls in assessment results.

        Returns None if all controls passed (no remediation needed).
        """
        all_risks: List[OSCALRisk] = []
        poam_items: List[POAMItem] = []

        for result in ar.results:
            for finding in result.findings:
                if finding.target and finding.target.status.state == "not-satisfied":
                    # Extract risk UUIDs from RiskRef objects
                    risk_uuids = [rr.risk_uuid for rr in finding.related_risks]
                    related_risks_objs = [
                        r for r in result.risks if r.uuid in risk_uuids
                    ]
                    all_risks.extend(related_risks_objs)

                    poam_items.append(
                        POAMItem(
                            title=f"Remediate: {finding.target.target_id}",
                            description=(
                                f"Address non-conformity identified in control "
                                f"{finding.target.target_id}. {finding.description}"
                            ),
                            related_findings=[finding.uuid],
                            related_risks=risk_uuids,
                            status="open",
                        )
                    )

        if not poam_items:
            return None

        return PlanOfActionAndMilestones(
            metadata=OSCALMetadata(
                title="AI Assurance Plan of Action and Milestones"
            ),
            risks=all_risks,
            poam_items=poam_items,
        )
