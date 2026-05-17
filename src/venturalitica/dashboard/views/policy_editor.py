try:
    import streamlit as st
except ImportError:
    raise ImportError(
        "streamlit is required for the dashboard. "
        "Install with: pip install venturalitica[dashboard]"
    )
from pathlib import Path

import yaml

from venturalitica.metrics import METRIC_METADATA

# Extended Metadata for Data Policies
DATA_METRIC_METADATA = {
    "k_anonymity": {
        "name": "k-Anonymity",
        "category": "privacy",
        "description": "Ensures that each record is indistinguishable from at least k-1 other records.",
        "ideal_value": ">= 5",
        "reference": "https://en.wikipedia.org/wiki/K-anonymity",
    },
    "l_diversity": {
        "name": "l-Diversity",
        "category": "privacy",
        "description": "Ensures that sensitive attributes have at least l well-represented values in each equivalence class.",
        "ideal_value": ">= 2",
        "reference": "https://en.wikipedia.org/wiki/L-diversity",
    },
    "data_retention_days": {
        "name": "Data Retention (Days)",
        "category": "governance",
        "description": "Maximum number of days data is retained before deletion.",
        "ideal_value": "<= 365",
    },
    "data_completeness": {
        "name": "Data Completeness",
        "category": "quality",
        "description": "Percentage of non-null values in critical fields.",
        "ideal_value": "1.0",
    },
}


def interpret_rule(metric_key, operator, threshold, is_data=False):
    """Generates a plain English interpretation of a risk control rule."""
    meta = DATA_METRIC_METADATA.get(metric_key, {}) if is_data else METRIC_METADATA.get(metric_key, {})
    name = meta.get("name", metric_key)

    # Base interpretation templates
    if "fairness" in meta.get("category", ""):
        if "demographic_parity" in metric_key:
            return f"Ensures the acceptance rate gap between groups is **{operator} {threshold}**. (Lower gap = Fairer)"
        if "equal_opportunity" in metric_key:
            return f"Ensures the true positive rate gap between groups is **{operator} {threshold}**."
        if "disparate_impact" in metric_key:
            return f"Ensures the ratio of acceptance rates is **{operator} {threshold}** (Standard is > 0.8)."

    if "privacy" in meta.get("category", ""):
        if "k_anonymity" in metric_key:
            return f"Ensures every record is indistinguishable from at least **{threshold}** others."
        if "data_retention" in metric_key:
            return f"Ensures data is deleted after **{threshold}** days."

    return f"Flags a risk if **{name}** is not **{operator} {threshold}**."


def load_policy(target_dir, filename):
    """Read a policy YAML and surface its controls in the UI format.

    Detects both envelopes:
      - canonical NIST `component-definition` (post 2026-05 OSCAL migration),
        in which case `is_canonical=True` is returned and the legacy form
        editor MUST refuse to write back (see save_policy_file + the banner
        in render_policy_editor).
      - legacy `assessment-plan + control-implementations[]` (kept for
        backward read-only display of policies authored before 0.6.4).
    """
    path = Path(target_dir) / filename
    if not path.exists():
        return {"title": "New Policy", "controls": [], "is_canonical": False}

    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}

    full_controls = []

    # Canonical NIST OSCAL v1.2.2 envelope (preferred). Walk the
    # `components[].control-implementations[].implemented-requirements[]`
    # tree — same path the SDK loader uses.
    canonical_root = data.get("component-definition")
    if canonical_root:
        title = canonical_root.get("metadata", {}).get("title", "Canonical Policy")
        for component in (canonical_root.get("components") or []):
            for impl in (component.get("control-implementations") or []):
                for req in (impl.get("implemented-requirements") or []):
                    ctrl = _control_from_requirement(req)
                    if "metric_key" in ctrl:
                        full_controls.append(ctrl)
        return {
            "title": title,
            "controls": full_controls,
            "is_canonical": True,
        }

    # Legacy `assessment-plan` envelope (read-only — the SDK loader no
    # longer accepts this root since 0.6.4).
    legacy_root = data.get("assessment-plan", {})
    title = legacy_root.get("metadata", {}).get("title", "New Policy")
    for impl in (legacy_root.get("control-implementations") or []):
        for req in (impl.get("implemented-requirements") or []):
            ctrl = _control_from_requirement(req)
            if "metric_key" in ctrl:
                full_controls.append(ctrl)

    return {"title": title, "controls": full_controls, "is_canonical": False}


def _control_from_requirement(req: dict) -> dict:
    """Extract the UI-facing control dict from a canonical or legacy
    implemented-requirement object. Shared by both envelope parsers."""
    ctrl = {"id": req.get("control-id"), "description": req.get("description", "")}
    for p in req.get("props", []):
        if p.get("name") in ("metric_key", "operator", "threshold", "severity"):
            val = p.get("value")
            if p["name"] == "threshold":
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    pass
            ctrl[p["name"]] = val
    return ctrl


def save_policy_file(target_dir, filename, data):
    # Hard guard: refuse to overwrite a canonical NIST `component-definition`
    # policy with the legacy `assessment-plan` envelope this form-builder
    # still emits. Doing so would silently corrupt the policy — the SDK
    # loader 0.6.4+ rejects the legacy root, so the next `vl.enforce()` call
    # would skip every control. The full editor rewrite (D2.1 in the
    # roadmap) is deferred to a dedicated sprint; until then, canonical
    # policies must be edited as YAML or re-pulled via `vl pull`.
    if data.get("is_canonical"):
        st.error(
            "🛡️ Refusing to overwrite a canonical `component-definition` "
            "policy with the legacy `assessment-plan` shape that this form "
            "currently emits.\n\n"
            "Edit the YAML directly or run `vl pull` to refresh from the "
            "Venturalítica SaaS."
        )
        return

    # Mapping UI Format -> OSCAL
    oscal_data = {
        "assessment-plan": {
            "metadata": {"title": data.get("title", "Generated Policy"), "version": "1.0"},
            "control-implementations": [
                {
                    "uuid": "impl-1",
                    "source": "venturalitica-dashboard",
                    "description": "Generated by Venturalítica AI Assurance Dashboard",
                    "implemented-requirements": [],
                }
            ],
        }
    }

    impl_reqs = oscal_data["assessment-plan"]["control-implementations"][0]["implemented-requirements"]

    for ctrl in data.get("controls", []):
        req = {
            "control-id": ctrl.get("id"),
            "description": ctrl.get("description", ""),
            "props": [
                {"name": "metric_key", "value": ctrl.get("metric_key")},
                {"name": "operator", "value": ctrl.get("operator")},
                {"name": "threshold", "value": str(ctrl.get("threshold"))},
                {"name": "severity", "value": ctrl.get("severity", "medium")},
            ],
        }

        # PERSIST ROLE MAPPINGS (Virtual Variables)
        for role_name, col_name in ctrl.get("mappings", {}).items():
            req["props"].append({"name": f"metric_role_{role_name}", "value": col_name})

        impl_reqs.append(req)

    path = Path(target_dir) / filename
    with open(path, "w") as f:
        yaml.dump(oscal_data, f, sort_keys=False)
    st.toast(f"✅ Saved {filename}!")


def render_policy_editor(target_dir):
    st.title("⚖️ Policy & Risk Definition")
    st.markdown(
        "Define the **Compliance-as-Code** rules for both your Model (Performance/Bias) and Data (Privacy/Quality)."
    )

    # Policy Selector
    policy_type = st.radio("Select Policy Scope", ["🤖 Model Policy", "🛡️ Data Policy"], horizontal=True)
    is_data_policy = "Data" in policy_type
    filename = "data_policy.oscal.yaml" if is_data_policy else "model_policy.oscal.yaml"

    # Load specific policy
    if f"policy_{filename}" not in st.session_state:
        st.session_state[f"policy_{filename}"] = load_policy(target_dir, filename)

    policy = st.session_state[f"policy_{filename}"]
    controls = policy.get("controls", [])

    # Metadata Source
    active_metadata = DATA_METRIC_METADATA if is_data_policy else METRIC_METADATA

    # Sidebar
    with st.sidebar:
        st.header(f"{policy_type} Context")
        if is_data_policy:
            st.info("Data Policies govern interaction with personal data (GDPR, Art. 10 AI Act).")
        else:
            st.info("Model Policies govern accuracy, robustness, and fairness (Art. 15 AI Act).")

        st.divider()
        st.caption(f"Editing: `{filename}`")

    # Tabs
    tab_controls, tab_preview = st.tabs(["1. Define Rules", "2. YAML Preview"])

    with tab_controls:
        # Split: Filter options
        c1, c2 = st.columns([1, 2])

        with c1:
            st.subheader("Add Control")
            with st.container(border=True):
                # Metric Selection
                metric_options = list(active_metadata.keys())
                selected_metric = st.selectbox(
                    "Risk Metric", metric_options, format_func=lambda x: f"{active_metadata[x]['name']}"
                )

                # Rule Logic
                c_op, c_th = st.columns([1, 1])
                operator = c_op.selectbox("Operator", [">", ">=", "<", "<=", "=="])
                threshold = c_th.number_input("Threshold", value=0.8, step=0.05)

                # Metadata Display
                meta = active_metadata[selected_metric]
                st.caption(f"**Metric**: {meta.get('description')}")
                st.info(f"💡 {interpret_rule(selected_metric, operator, threshold, is_data_policy)}")

                # METRIC ROLE MAPPINGS (Virtual Variables)
                # These are required for the enforce() function to know which columns to use.
                required_roles = meta.get("required_roles", [])
                mappings = {}
                if required_roles:
                    st.caption("📝 **Variable Mapping** (Required for SDK `enforce`) ")
                    for role in required_roles:
                        # Map internal role names to human-readable labels
                        label_map = {
                            "target": "Target Column (Label)",
                            "prediction": "Prediction Column",
                            "dimension": "Protected Attribute (Dimension)",
                            "features": "Feature Columns (CSV list)",
                        }
                        role_label = label_map.get(role, role.capitalize())
                        mappings[role] = st.text_input(f"{role_label}", key=f"map_{selected_metric}_{role}")

                severity = st.select_slider("Severity", options=["low", "medium", "high", "critical"], value="high")

                if st.button("➕ Add Rule", use_container_width=True):
                    # Validation: Ensure all roles are mapped
                    if any(not v for v in mappings.values()):
                        st.error("Please provide all required column mappings.")
                        return

                    new_control = {
                        "id": f"ctrl-{len(controls) + 1}",
                        "metric_key": selected_metric,
                        "operator": operator,
                        "threshold": threshold,
                        "severity": severity,
                        "description": meta.get("description"),
                        "mappings": mappings,
                    }
                    controls.append(new_control)
                    policy["controls"] = controls
                    st.rerun()

        with c2:
            st.subheader(f"Active Controls ({len(controls)})")
            if not controls:
                st.info("No controls defined yet. Add one from the left sidebar.")

            for i, ctrl in enumerate(controls):
                with st.container(border=True):
                    cols = st.columns([3, 1])
                    cols[0].markdown(f"**{ctrl['metric_key']}** {ctrl['operator']} `{ctrl['threshold']}`")
                    cols[0].caption(ctrl.get("description"))
                    if cols[1].button("🗑️", key=f"del_{filename}_{i}"):
                        controls.pop(i)
                        st.rerun()

    with tab_preview:
        col_save, col_code = st.columns([1, 3])
        with col_save:
            st.markdown("### Finalize")
            policy["title"] = st.text_input("Policy Title", value=policy.get("title", "My Policy"))
            if policy.get("is_canonical"):
                st.warning(
                    "📖 Read-only — this policy uses the canonical NIST OSCAL "
                    "`component-definition` envelope. The form editor below "
                    "still emits the legacy `assessment-plan` shape; saving "
                    "would corrupt the policy. Edit the YAML directly or "
                    "run `vl pull` to refresh from the SaaS."
                )
                st.button(
                    "💾 Save to File",
                    type="primary",
                    use_container_width=True,
                    disabled=True,
                    help="Save disabled while a canonical policy is loaded.",
                )
            else:
                if st.button("💾 Save to File", type="primary", use_container_width=True):
                    save_policy_file(target_dir, filename, policy)

        with col_code:
            st.code(yaml.dump(policy, sort_keys=False), language="yaml")

    policy["controls"] = controls
    st.session_state[f"policy_{filename}"] = policy
