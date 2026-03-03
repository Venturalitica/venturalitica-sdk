import json
import os
from pathlib import Path

try:
    import streamlit as st
except ImportError:
    raise ImportError(
        "streamlit is required for the dashboard. "
        "Install with: pip install venturalitica[dashboard]"
    )
import yaml

from venturalitica.inference import infer_risk_classification, infer_system_description, infer_technical_documentation
from venturalitica.models import SystemDescription, TechnicalDocumentation


def load_system_description(target_dir):
    """Loads the system description YAML if it exists."""
    path = Path(target_dir) / "system_description.yaml"
    if path.exists():
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
            return SystemDescription(
                name=data.get("name", ""),
                version=data.get("version", ""),
                provider_name=data.get("provider_name", ""),
                intended_purpose=data.get("intended_purpose", ""),
                interaction_description=data.get("interaction_description", ""),
                software_dependencies=data.get("software_dependencies", ""),
                market_placement_form=data.get("market_placement_form", ""),
                hardware_description=data.get("hardware_description", ""),
                external_features=data.get("external_features", ""),
                ui_description=data.get("ui_description", ""),
                instructions_for_use=data.get("instructions_for_use", ""),
            )
    return SystemDescription()


def save_system_description(target_dir, model: SystemDescription):
    """Saves the system description to YAML."""
    path = Path(target_dir) / "system_description.yaml"
    with open(path, "w") as f:
        yaml.dump(model.to_dict(), f, sort_keys=False)
    st.toast("✅ System Description Saved!")


def render_model_card_editor(target_dir):
    st.title("🛡️ System Identity — Annex IV.1")
    st.markdown("""
    According to **Article 11** of the EU AI Act, high-risk systems must maintain technical documentation. 
    This form captures the **Annex IV.1: General Description** evidence for your AI system.
    """)

    # Sidebar: Compliance Context
    with st.sidebar:
        st.header("⚖️ Regulatory Context")
        st.markdown("""
        **Annex IV Requirements:**
        1. **General Description** (This form)
        2. **Technical Architecture**
        3. **Risk Management** (via Policies)
        4. **Data Governance**
        5. **Monitoring & Post-market**
        """)

        st.divider()
        st.subheader("Assurance Readiness")
        # Simple completion check
        sd_state = st.session_state.get("system_description", load_system_description(target_dir))
        fields = [sd_state.name, sd_state.intended_purpose, sd_state.instructions_for_use]
        filled = sum(1 for f in fields if f and len(f) > 5)
        progress = filled / len(fields)
        st.progress(progress)
        st.caption(f"{int(progress * 100)}% of critical regulatory fields documented.")

    # Tabs for different Annex IV sections
    with st.expander("🪄 **AI-Assisted Documentation (Smart Inference)**", expanded=False):
        st.markdown("Automate documentation by scanning your code for architecture and intent.")
        c_inf1, c_inf2 = st.columns([1, 1])
        with c_inf1:
            inf_provider = st.selectbox("Inference Engine", ["Mistral AI (Cloud)", "Local (Ollama)"])
        with c_inf2:
            if "Mistral" in inf_provider:
                api_key = st.text_input("MISTRAL_API_KEY", type="password", value=os.getenv("MISTRAL_API_KEY", ""))
            else:
                st.info("Ensure Ollama is running locally.")
                api_key = None

        if st.button("✨ Scan Repository & Infer Specs", use_container_width=True, type="primary"):
            with st.spinner("Analyzing codebase..."):
                try:
                    p_code = "cloud" if "Mistral" in inf_provider else "local"
                    inferred_sd = infer_system_description(target_dir, provider=p_code, api_key=api_key)
                    st.session_state["system_description"] = inferred_sd
                    st.success("Specifications inferred! Review below.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Inference failed: {e}")

    # Tabs for different Annex IV sections
    tab1, tab2, tab3, tab4 = st.tabs(
        ["(a) Identity & Purpose", "(b-e) Interaction & Hardware", "(g-h) UI & Instructions", "Annex IV.2 Tech Doc"]
    )

    if "system_description" not in st.session_state:
        st.session_state["system_description"] = load_system_description(target_dir)

    sd = st.session_state["system_description"]

    with tab1:
        st.subheader("Annex IV.1(a): System Identity")
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            sd.name = c1.text_input("Commercial Name", value=sd.name)
            sd.provider_name = c2.text_input("Provider / Developer", value=sd.provider_name)
            sd.version = c3.text_input("Version", value=sd.version)

            st.markdown("#### Intended Purpose (Art. 3.12)")
            st.info("⚠️ This is the most critical field. It defines the 'high-risk' status.")
            sd.intended_purpose = st.text_area(
                "Description of the Intended Purpose",
                value=sd.intended_purpose,
                help="Describe the specific function, context of use, and target users.",
                height=150,
            )
            sd.potential_misuses = st.text_area(
                "Potential Misuses (Art. 15)", value=sd.potential_misuses, help="Foreseeable misuse risks."
            )

            st.divider()
            st.markdown("#### ⚖️ Regulatory Context (Annex I & III)")
            if st.button("🚦 Check Risk Level", type="secondary"):
                with st.spinner("Consulting EU AI Act Knowledge Base..."):
                    # Save state first to ensure we infer on latest text
                    risk_assessment = infer_risk_classification(sd)
                    st.session_state["risk_assessment"] = risk_assessment

            if "risk_assessment" in st.session_state:
                ra = st.session_state["risk_assessment"]
                if ra.risk_level == "PROHIBITED":
                    st.error(f"🚫 **PROHIBITED** (Annex I)\n\n{ra.reasoning}")
                elif ra.risk_level == "HIGH_RISK":
                    st.warning(f"⚠️ **HIGH-RISK** (Annex III)\n\n{ra.reasoning}")
                elif ra.risk_level == "TRANSPARENCY_ONLY":
                    st.info(f"👀 **TRANSPARENCY RISK** (Art 50)\n\n{ra.reasoning}")
                else:
                    st.success(f"✅ **MINIMAL RISK**\n\n{ra.reasoning}")

                if ra.applicable_articles:
                    st.caption(f"Relevant Articles: {', '.join(ra.applicable_articles)}")

    with tab2:
        st.subheader("Annex IV.1(b): Hardware & Assets")
        st.info("Define the physical and environmental requirements for your system.")

        with st.container(border=True):
            # REMOVED: BOM/Software Dependencies (Moved to Mission 4)

            st.markdown("#### Hardware Specifications")
            sd.hardware_description = st.text_area(
                "Compute Resources (CPU/GPU/RAM)",
                value=sd.hardware_description,
                help="Describe the hardware required to run the system efficiently.",
                height=100,
            )

            col_l, col_r = st.columns(2)
            with col_l:
                sd.interaction_description = st.text_area(
                    "Environment Interaction",
                    value=sd.interaction_description,
                    help="How the AI system interfaces with its environment.",
                )
            with col_r:
                sd.external_features = st.text_area(
                    "Physical External Features",
                    value=sd.external_features,
                    help="Markings, packaging features, or physical embedded constraints.",
                )

    with tab3:
        st.subheader("Annex IV.1(g-h): UI & Instructions")
        with st.container(border=True):
            sd.market_placement_form = st.text_input(
                "Form of Market Placement",
                value=sd.market_placement_form,
                placeholder="e.g. SaaS, Embedded, Standalone",
            )
            sd.ui_description = st.text_area("User Interface Description", value=sd.ui_description)

            st.markdown("#### Instructions for Use (Art. 13)")
            st.warning("Art. 13 requires instructions to be clear and enable users to interpret the system's output.")
            sd.instructions_for_use = st.text_area("Mandatory Instructions", value=sd.instructions_for_use, height=120)

    with tab4:
        st.subheader("Annex IV.2: Technical Documentation")

        # Load Tech Doc
        td_path = os.path.join(target_dir, "venturalitica_technical_doc.json")
        td = TechnicalDocumentation()
        if os.path.exists(td_path):
            with open(td_path, "r") as f:
                data = json.load(f)
                td = TechnicalDocumentation(**data)

        if st.button("✨ Smart Draft Technical Details", type="secondary"):
            with st.spinner("Analyzing code structure & data provenance..."):
                td = infer_technical_documentation(target_dir)
                st.success("Draft generated!")
                st.json(td.to_dict(), expanded=False)

        st.markdown("#### (c) Architecture Diagram")
        if td.architecture_diagram:
            st.markdown(f"```mermaid\n{td.architecture_diagram}\n```")
        td.architecture_diagram = st.text_area("Mermaid Code", value=td.architecture_diagram, height=150)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### (a) Development Methods")
            dev_methods_txt = "\n".join(td.development_methods)
            new_dev_methods = st.text_area("Methods (One per line)", value=dev_methods_txt, height=100)
            td.development_methods = [x.strip() for x in new_dev_methods.split("\n") if x.strip()]

            st.markdown("#### (d) Data Provenance")
            # Simple JSON editor for now
            td.data_provenance = st.data_editor(td.data_provenance, num_rows="dynamic")

        with c2:
            st.markdown("#### (b) Logic Description")
            td.logic_description = st.text_area("Logic Summary", value=td.logic_description, height=100)

            st.markdown("#### (e) Human Oversight")
            oversight_txt = "\n".join(td.human_oversight_measures)
            new_oversight = st.text_area("Oversight Measures", value=oversight_txt, height=100)
            td.human_oversight_measures = [x.strip() for x in new_oversight.split("\n") if x.strip()]

    st.divider()
    if st.button("💾 Save Annex IV Metadata", type="primary"):
        save_system_description(target_dir, sd)
        # Save Tech Doc
        td_path = os.path.join(target_dir, "venturalitica_technical_doc.json")
        try:
            # Ensure td is available in local scope, if not defined in tab4 block (e.g. if tab not visited)
            if "td" not in locals():
                td = TechnicalDocumentation()
                if os.path.exists(td_path):
                    with open(td_path, "r") as f:
                        data = json.load(f)
                        td = TechnicalDocumentation(**data)

            with open(td_path, "w") as f:
                json.dump(td.to_dict(), f, indent=2)
        except Exception as e:
            st.error(f"Error saving Technical Doc: {e}")

        st.balloons()
