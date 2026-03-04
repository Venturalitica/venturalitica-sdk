import os  # Forced reload triggered by agent
import sys
import types

# Ensure importing dashboard modules doesn't fail when Streamlit
# is unavailable (test environments). If streamlit can't be imported,
# inject a lightweight stub module into sys.modules so other modules
# can import `streamlit as st` safely. Tests can still patch
# `venturalitica.dashboard.main.st` with a richer mock.
try:
    import streamlit as st
except Exception:
    _mod = types.ModuleType("streamlit")
    # minimal session_state and no-op helpers — render functions will
    # usually be patched in tests with a richer mock prior to use.
    _mod.session_state = {}

    def _noop(*a, **k):
        return None

    for _name in [
        "set_page_config",
        "markdown",
        "header",
        "columns",
        "sidebar",
        "divider",
        "info",
        "subheader",
        "tabs",
        "image",
        "selectbox",
        "caption",
        "expander",
        "container",
        "write",
        "text",
        "text_area",
        "text_input",
        "radio",
        "multiselect",
        "button",
        "spinner",
        "success",
        "error",
        "warning",
        "json",
        "dataframe",
    ]:
        setattr(_mod, _name, _noop)
    sys.modules["streamlit"] = _mod
    st = _mod

# Import Views (done after ensuring `streamlit` exists)
from venturalitica.dashboard.components.metrics import (
    list_available_sessions,
    load_cached_results,
    load_session_metadata,
)

# Import Styles
from venturalitica.dashboard.styles import apply_saas_theme
from venturalitica.dashboard.views.annex_generator import render_annex_view
from venturalitica.dashboard.views.model_card_editor import render_model_card_editor
from venturalitica.dashboard.views.policy import render_policy_view
from venturalitica.dashboard.views.policy_editor import render_policy_editor
from venturalitica.dashboard.views.technical import render_technical_view
from venturalitica.dashboard.views.transparency import render_transparency_view

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Venturalítica | AI Assurance", layout="wide", page_icon="🔍")

# --- APPLY THEME ---
apply_saas_theme()


def _resolve_logo():
    """Resolve logo path — prefer lupa.svg (brand icon), fall back to others."""
    # Walk up from this file to the SDK package root, then to the monorepo root
    sdk_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    monorepo_root = os.path.dirname(os.path.dirname(sdk_root))
    base_path = os.path.join(monorepo_root, "landing", "public")

    candidates = [
        (os.path.join(base_path, "lupa.svg"), 55),
        (os.path.join(base_path, "venturalitica.svg"), 160),
        (os.path.join(base_path, "vl.svg"), 50),
    ]
    for path, width in candidates:
        if os.path.exists(path):
            return path, width
    return None, 50


def render_dashboard():
    # --- HEADER ---
    logo_path, logo_width = _resolve_logo()

    col_logo, col_title = st.columns([0.05, 0.95])
    with col_logo:
        if logo_path:
            st.image(logo_path, width=logo_width)
        else:
            st.write("# 🔍")
    with col_title:
        st.markdown(
            """
            <h1 style='padding-top: 0rem; margin-bottom: 0px; font-family: Roboto Condensed, sans-serif; color: #0b3260;'>
                Venturalítica AI Assurance
            </h1>
            <p style='color: #4e6584; font-size: 1.05rem; margin-top: -5px; font-family: Roboto, sans-serif;'>
                Compliance-as-Code &middot; Collect, verify, and organise technical evidence for EU AI Act documentation.
            </p>
        """,
            unsafe_allow_html=True,
        )

    # --- PROJECT CONTEXT ---
    target_dir = os.getcwd()
    st.sidebar.markdown("### 📁 Project Context")
    st.sidebar.text(f"Root: {os.path.basename(target_dir)}")
    st.sidebar.divider()

    # --- PHASE STATUS (file-existence checks) ---
    has_model_card = os.path.exists(os.path.join(target_dir, "system_description.yaml"))
    has_policy = os.path.exists(os.path.join(target_dir, "model_policy.oscal.yaml"))
    has_evidence = os.path.exists(os.path.join(target_dir, "results.json")) or any(
        f.startswith("trace_") for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))
    )
    has_doc = os.path.exists(os.path.join(target_dir, "venturalitica_technical_doc.json"))

    p1_status = "✅" if has_model_card else "⚠️"
    p2_status = "✅" if has_policy else "⚠️"
    p3_status = "✅" if has_evidence else "⚠️"
    p4_status = "✅" if has_doc else "⚠️"

    # --- PHASE NAVIGATION ---
    PHASE_HOME = "Home"
    PHASE_IDENTITY = "Identity"
    PHASE_POLICY = "Policy"
    PHASE_VERIFY = "Verify"
    PHASE_REPORT = "Report"

    phase_keys = [PHASE_HOME, PHASE_IDENTITY, PHASE_POLICY, PHASE_VERIFY, PHASE_REPORT]

    # Gating: a phase is unlocked only when its prerequisite is met
    phase_unlocked = {
        PHASE_HOME: True,
        PHASE_IDENTITY: True,  # always available
        PHASE_POLICY: has_model_card,
        PHASE_VERIFY: has_policy,
        PHASE_REPORT: has_evidence,
    }

    def format_phase(key):
        locked = not phase_unlocked.get(key, True)
        lock_icon = "🔒 " if locked else ""
        if key == PHASE_HOME:
            return "🏠 Home"
        if key == PHASE_IDENTITY:
            return f"{lock_icon}1. System Identity {p1_status}"
        if key == PHASE_POLICY:
            return f"{lock_icon}2. Risk Policy & Guards {p2_status}"
        if key == PHASE_VERIFY:
            return f"{lock_icon}3. Verify & Evaluate {p3_status}"
        if key == PHASE_REPORT:
            return f"{lock_icon}4. Technical Report {p4_status}"
        return key

    # Handle session-state navigation (e.g. from Home buttons)
    if "mission_target" in st.session_state:
        target = st.session_state.pop("mission_target")
        if target in phase_keys and phase_unlocked.get(target, False):
            st.session_state["sidebar_selection"] = target

    phase = st.sidebar.radio(
        "📍 Assurance Phase",
        options=phase_keys,
        format_func=format_phase,
        key="sidebar_selection",
        help="Collect evidence across 4 phases: Identity → Policy → Verification → Reporting.",
    )

    # Enforce gating: redirect locked phases back to Home
    if not phase_unlocked.get(phase, True):
        st.warning("Complete the previous phase before proceeding.")
        phase = PHASE_HOME

    selected_label = format_phase(phase)

    # =========================================================================
    # HOME
    # =========================================================================
    if phase == PHASE_HOME:
        st.subheader("🔍 AI Assurance — Evidence Collection")
        st.markdown(
            "Welcome to the **Venturalítica AI Assurance Workspace**. "
            "Follow these 4 steps to collect and organise the technical evidence "
            "referenced by EU AI Act Annex IV. "
            "This tool **assists with evidence gathering** and does not constitute "
            "legal advice or guarantee regulatory compliance."
        )

        m_col1, m_col2 = st.columns(2)

        # Step 1 — always available
        with m_col1:
            with st.container(border=True):
                st.markdown(f"#### 1. Define System {p1_status}")
                st.caption("Annex IV.1 — System Identity & Hardware")
                st.info("Describe your AI system: identity, intended purpose, and computational assets.")
                if has_model_card:
                    st.success("✅ Evidence captured")
                    if st.button("Edit System", key="m1_edit", use_container_width=True):
                        st.session_state.mission_target = PHASE_IDENTITY
                        st.rerun()
                else:
                    if st.button("Start Step 1", key="m1_start", use_container_width=True):
                        st.session_state.mission_target = PHASE_IDENTITY
                        st.rerun()

        # Step 2 — requires Step 1
        with m_col2:
            with st.container(border=True):
                st.markdown(f"#### 2. Define Policies {p2_status}")
                st.caption("Articles 9–10 — Risk & Data Governance (OSCAL)")
                st.info("Set model (fairness / performance) and data (privacy / quality) policy rules.")
                if not has_model_card:
                    st.warning("⏳ Complete Step 1 first.")
                elif has_policy:
                    st.success("✅ Evidence captured")
                    if st.button("Edit Policies", key="m2_edit", use_container_width=True):
                        st.session_state.mission_target = PHASE_POLICY
                        st.rerun()
                else:
                    if st.button("Start Step 2", key="m2_start", use_container_width=True):
                        st.session_state.mission_target = PHASE_POLICY
                        st.rerun()

        m_col3, m_col4 = st.columns(2)

        # Step 3 — requires Step 2
        with m_col3:
            with st.container(border=True):
                st.markdown(f"#### 3. Review Evidence {p3_status}")
                st.caption("Articles 11–15 — Technical Integrity & Transparency")
                st.info("Inspect telemetry, execution traces, and metric validation results.")
                if not has_policy:
                    st.warning("⏳ Complete Step 2 first.")
                else:
                    if has_evidence:
                        st.success("✅ Evidence captured")
                    if st.button("View Evidence", key="m3_start", use_container_width=True):
                        st.session_state.mission_target = PHASE_VERIFY
                        st.rerun()

        # Step 4 — requires Step 3
        with m_col4:
            with st.container(border=True):
                st.markdown(f"#### 4. Generate Report {p4_status}")
                st.caption("Article 11 & Annex IV — Technical Documentation")
                st.info("Draft a technical documentation file based on the evidence collected above.")
                if not has_evidence:
                    st.warning("⏳ Complete Step 3 first.")
                else:
                    if has_doc:
                        st.success("✅ Report drafted")
                    if st.button("Start Step 4", key="m4_start", use_container_width=True):
                        st.session_state.mission_target = PHASE_REPORT
                        st.rerun()

    # =========================================================================
    # PHASE 1: SYSTEM IDENTITY
    # =========================================================================
    elif phase == PHASE_IDENTITY:
        st.caption(f"📍 **Assurance Journey** > {selected_label}")
        st.subheader("🏗️ Phase 1: System Identity")
        st.info("Describe your AI system for **Annex IV.1** — identity, purpose, and assets.")
        render_model_card_editor(target_dir)

    # =========================================================================
    # PHASE 2: RISK POLICY
    # =========================================================================
    elif phase == PHASE_POLICY:
        st.caption(f"📍 **Assurance Journey** > {selected_label}")
        st.subheader("🛡️ Phase 2: Risk Policy")
        st.info("Define the **Compliance-as-Code** policy (OSCAL) that your system must adhere to.")
        render_policy_editor(target_dir)

    # =========================================================================
    # PHASE 3 & 4: SESSION CONTEXT REQUIRED
    # =========================================================================
    else:
        # Session Selector
        st.sidebar.markdown("### 🕒 Session Context")
        available_sessions = ["Global / History"] + list_available_sessions()
        selected_session = st.sidebar.selectbox(
            "Select Evidence Run",
            available_sessions,
            index=0,
            help="Select a specific training or evaluation run to analyse.",
        )

        # Load Results for Session
        results_raw = load_cached_results(selected_session)
        if isinstance(results_raw, dict):
            st.session_state["results"] = results_raw.get(
                "post_metrics",
                results_raw.get("audit_results", results_raw.get("metrics", [])),
            )
            if "training_metadata" in results_raw and not st.session_state.get("runtime_meta"):
                st.session_state["runtime_meta"] = results_raw["training_metadata"]
        else:
            st.session_state["results"] = results_raw if isinstance(results_raw, list) else []

        if selected_session != "Global / History":
            run_meta = load_session_metadata(selected_session)
            if run_meta.get("traces"):
                main_trace = run_meta["traces"][0]
                st.session_state["code_context"] = main_trace.get("code_context", {})
                st.session_state["runtime_meta"] = main_trace
            if run_meta.get("bom"):
                st.session_state["bom"] = run_meta["bom"]

        # --- PHASE 3: VERIFY ---
        if phase == PHASE_VERIFY:
            st.caption(f"📍 **Assurance Journey** > {selected_label} > {selected_session}")
            st.subheader(f"🔍 Phase 3: Verification ({selected_session})")

            tab_feed, tab_tech, tab_gov = st.tabs(
                [
                    "👁️ Transparency Feed",
                    "✅ Technical Integrity",
                    "🏛️ Policy Enforcement",
                ]
            )

            with tab_feed:
                render_transparency_view(target_dir)
            with tab_tech:
                render_technical_view(target_dir)
            with tab_gov:
                render_policy_view()

        # --- PHASE 4: REPORT ---
        elif phase == PHASE_REPORT:
            st.caption(f"📍 **Assurance Journey** > {selected_label} > {selected_session}")
            st.subheader(f"📄 Phase 4: Technical Documentation ({selected_session})")
            st.info(
                "Generate technical documentation (Annex IV) based on your "
                "Identity (Phase 1), Policy (Phase 2) and Evidence (Phase 3)."
            )

            render_annex_view(target_dir)


if __name__ == "__main__":
    render_dashboard()
