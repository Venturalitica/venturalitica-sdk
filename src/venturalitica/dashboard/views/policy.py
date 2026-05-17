try:
    import streamlit as st
except ImportError:
    raise ImportError(
        "streamlit is required for the dashboard. "
        "Install with: pip install venturalitica[dashboard]"
    )


# AI Assurance profile properties (Table 1 of the IEEE Computer paper "An
# OSCAL Profile for AI Assurance"). The SDK loader recognises these on
# policy props and the AR builder propagates them to observations
# (oscal/builder.py::_PROFILE_PROPS). The dashboard surfaces them so an
# auditor opening a control sees the full provenance — not just the bare
# metric/threshold pair.
_STABILITY_PROPS = (
    "severity",
    "lifecycle_phase",
    "enforcement_mode",
    "evaluation_method",
    "evaluation_window",
)
_TRACEABILITY_PROPS = (
    "risk_id",
    "treatment_id",
    "policy_id",
    "objective_id",
    "risk_acceptance_criteria",
    "threshold_justification",
    "stakeholder_consultation_ref",
)


def _humanise(key: str) -> str:
    """`lifecycle_phase` → `Lifecycle Phase` for display labels."""
    return key.replace("_", " ").title()


def render_policy_view():
    st.header("Assurance & Policy Scan")

    results = st.session_state.get("results")

    if results:
        st.markdown("### Latest Audit Results")
        for r in results:
            mark = "✅" if r.get("passed") else "❌"
            label = f"{mark} {r.get('control_id')} | {r.get('description', '')[:50]}..."
            with st.expander(label):
                # --- Metric & verdict (always shown) ---
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Metric", r.get("metric_key", "—"))
                actual = r.get("actual_value")
                col_b.metric(
                    "Actual value",
                    f"{actual:.4f}" if isinstance(actual, (int, float)) else str(actual),
                )
                col_c.metric(
                    "Threshold",
                    f"{r.get('operator', '')} {r.get('threshold', '—')}",
                )

                # --- AI Assurance profile props ---
                meta = r.get("metadata") or {}
                stability = [(k, meta.get(k)) for k in _STABILITY_PROPS if meta.get(k)]
                traceability = [(k, meta.get(k)) for k in _TRACEABILITY_PROPS if meta.get(k)]

                if stability:
                    st.markdown("**Stability**")
                    line = " · ".join(
                        f"{_humanise(k)}: `{', '.join(v) if isinstance(v, list) else v}`"
                        for k, v in stability
                    )
                    st.caption(line)

                if traceability:
                    st.markdown("**Traceability**")
                    line = " · ".join(
                        f"{_humanise(k)}: `{v}`" for k, v in traceability
                    )
                    st.caption(line)

                # --- Red flag for failures ---
                if not r.get("passed"):
                    st.error(
                        f"Red flag: {meta.get('severity', r.get('severity', 'unknown'))} risk detected."
                    )
    else:
        st.info("No audit results found. Run `enforce()` in your training script.")

    st.divider()
    st.markdown("#### 💡 Assurance Recommendation")
    st.info(
        "Based on your local scan, you are missing a 'Human-in-the-Loop' mechanism for critical decisions."
    )
