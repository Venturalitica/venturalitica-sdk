import streamlit as st
from venturalitica.scanner import BOMScanner
from venturalitica.badges import generate_compliance_badge
from pathlib import Path
import os
import json
import time
import time
import time
import asyncio
from venturalitica.graph.workflow import create_compliance_graph
from venturalitica.graph.nodes import NodeFactory
from langchain_core.messages import HumanMessage

# --- UI CONFIGURATION ---
st.set_page_config(
    page_title="Venturalítica | Local Compliance",
    layout="wide",
    page_icon="🛡️"
)

# --- STYLING ---
st.markdown("""
<style>
    /* Minimal Customization - Safe Reset */
    
    /* Custom Color Wrappers for Audit Results */
    .compliance-pass { color: #0369a1; font-weight: 600; }
    .compliance-fail { color: #b91c1c; font-weight: 600; }
    
    /* Subtle Background Adjustment */
    .main { background-color: #fefefe; }
    
</style>
""", unsafe_allow_html=True)

# --- LOGIC HELPERS ---
def load_cached_results():
    results_path = ".venturalitica/results.json"
    if os.path.exists(results_path):
        with open(results_path, "r") as f:
            return json.load(f)
    return None

async def run_compliance_graph(target_dir, container):
    """
    Orchestrates the LangGraph workflow and streams updates to the UI.
    """
async def run_compliance_graph(target_dir, container, selected_languages):
    """
    Orchestrates the LangGraph workflow and streams updates to the UI.
    """
    graph = create_compliance_graph(model_name=st.session_state.get('model_name', 'mistral'))
    
    initial_state = {
        "project_root": target_dir,
        "bom": {},
        "runtime_meta": {},
        "sections": {},
        "final_markdown": "",
        "languages": selected_languages,
        # Pass pre-calculated transparency data if available to avoid re-scanning
        "evidence_hash": st.session_state.get('evidence_hash', ""),
        "bom_security": st.session_state.get('bom_security', {})
    }
    
    with container.status("🚀 Orchestrating Compliance Agents...", expanded=True) as status:
        # Stream the graph execution
        async for event in graph.astream(initial_state):
            for node, data in event.items():
                if node == "scanner":
                    status.update(label="🔍 Application scanned.", state="running")
                    with st.expander("BOM Details"):
                        st.json(data.get("bom", {}))
                elif node == "planner":
                    status.update(label="🗺️ Planning documentation structure...", state="running")
                elif node.startswith("writer_"):
                    section = node.split("_")[1]
                    st.write(f"✍️ **Drafted Section {section}**")
                elif node == "compiler":
                    status.update(label="📄 Document compiled successfully!", state="complete")
                    # MODIFIED: Return tuple of (full_markdown, sections_dict)
                    return data.get("final_markdown"), data.get("sections", {})
                elif node == "translator":
                    translations = data.get("translations", {})
                    st.write(f"🌍 Translations completed: {list(translations.keys())}")
                    if "translations" not in st.session_state:
                         st.session_state["translations"] = {}
                    st.session_state["translations"].update(translations)
                
    return None, {}

def _parse_bom(bom):
    """Parses BOM into actionable metrics and lists."""
    if not bom:
        return {}, [], []
    
    components = bom.get('components', [])
    ml_models = [c for c in components if c.get('type') == 'machine-learning-model']
    libs = [c for c in components if c.get('type') == 'library']
    
    licenses = set()
    for c in components:
        for lic in c.get('licenses', []):
            if isinstance(lic, dict) and 'license' in lic:
                licenses.add(lic['license'].get('id', 'Unknown'))
            elif isinstance(lic, str):
                licenses.add(lic)
                
    metrics = {
        "total": len(components),
        "models": len(ml_models),
        "licenses": len(licenses)
    }
    return metrics, ml_models, libs

    metrics = {
        "total": len(components),
        "models": len(ml_models),
        "licenses": len(licenses)
    }
    return metrics, ml_models, libs

def render_compliance_mapping(code_context, bom_security, runtime_meta):
    """
    Maps technical signals to EU AI Act Obligations (Art 9-15).
    Professional 'Evidence ↔ Obligation' Traceability Matrix.
    """
    if not code_context or not isinstance(code_context, dict):
        st.info("No Evidence Map available yet. Refresh local scan.")
        return

    # Aggregate metadata
    all_imports = set()
    for _, data in code_context.items():
        if isinstance(data, dict):
            all_imports.update(data.get('imports', []))
    
    st.markdown("### 🇪🇺 Regulatory Compliance Map")
    st.markdown("""
    *This mapping connects technical evidence to EU AI Act obligations **IF** the system is classified as High-Risk (Annex III).*
    """)
    
    # 9. Article 9: Risk Management System
    with st.expander("⚖️ Article 9: Risk Management System", expanded=True):
        audit_results = runtime_meta.get("audit_results", [])
        bias_concerns = [r for r in audit_results if "disparate_impact" in r or "bias" in r]
        
        if bias_concerns:
             st.info(f"**Fundamental Rights Risk (Fairness):** Detected {len(bias_concerns)} fairness checks.")
             for check in bias_concerns:
                 if "FAIL" in check:
                     st.error(f"❌ **Risk Materialized**: {check}")
                 else:
                     st.success(f"✅ **Mitigation Verified**: {check}")
        else:
             st.caption("No fairness/bias evaluations found in runtime traces. Risk identification pending.")

    # 10. Article 10: Data Governance
    with st.expander("📄 Article 10: Data Governance & Quality"):
        risk_libraries = [i for i in all_imports if any(k in i.lower() for k in ['sklearn', 'mlflow', 'statsmodels'])]
        data_libraries = [i for i in all_imports if any(k in i.lower() for k in ['pandas', 'numpy'])]
        
        if risk_libraries:
            st.info("**Obligation Context:** Training, validation, and testing datasets must be relevant, representative, and free of errors.")
            st.markdown("#### 🔍 Technical Evidence Detected:")
            st.markdown(f"- **Modeling Frameworks**: `{', '.join(risk_libraries[:3])}`")
            if data_libraries:
                 st.markdown(f"- **Data Processing**: `{', '.join(data_libraries[:3])}`")
            st.success("✅ **Action**: This evidence supports the 'Data Governance' chapter of your Technical File.")
        else:
            st.caption("No ML modeling libraries detected.")

    # 11. Article 11: Technical Documentation
    with st.expander("📁 Article 11: Technical Documentation"):
        st.info("The provider must draw up technical documentation demonstrating conformity.")
        has_bom = st.session_state.get('bom') is not None
        has_annex = st.session_state.get('annex_sections') != {}
        
        c1, c2 = st.columns(2)
        with c1:
            if has_bom: st.success("✅ **Evidence**: SBOM available.")
            else: st.warning("⚠️ **Gap**: SBOM not scanned.")
        with c2:
            if has_annex: st.success("✅ **Evidence**: Annex IV Draft exists.")
            else: st.warning("⚠️ **Gap**: Annex IV not generated.")

    # 12. Article 12: Record-Keeping
    with st.expander("📝 Article 12: Record-Keeping"):
        st.info("Automatic logging of events ('logs') over the lifetime of the system.")
        if st.session_state.get('evidence_hash'):
            st.success(f"✅ **Evidence**: Cryptographic Hash (`{st.session_state['evidence_hash'][:8]}...`) anchored.")
        if runtime_meta:
            st.success("✅ **Evidence**: Execution traces (runtime_meta) captured.")
        else:
            st.warning("⚠️ **Gap**: No runtime records detected.")

    # 13. Article 13: Transparency & Provision of Information
    with st.expander("👁️ Article 13: Transparency"):
        st.info("Systems must be accompanied by instructions for use to enable users to interpret output.")
        if "raw_source" in str(code_context):
            st.success("✅ **Evidence**: Source code visibility enabled (Technical Transparency).")
        else:
            st.warning("⚠️ **Gap**: Evidence opacity.")

    # 14. Article 14: Human Oversight
    with st.expander("👤 Article 14: Human Oversight"):
        st.info("Designed to be effectively overseen by natural persons.")
        has_human = any("stream" in i for i in all_imports) or any("gradio" in i for i in all_imports)
        if has_human:
            st.success("✅ **Evidence**: Interactive oversight interface detected.")
        else:
            st.warning("⚠️ **Gap**: No human-in-the-loop nodes detected in control flow.")

    # 15. Article 15: Accuracy, Robustness & Cybersecurity
    with st.expander("🛡️ Article 15: Accuracy & Cybersecurity"):
        issues = bom_security.get("issues", [])
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**15(1) Accuracy & Robustness**")
            if any("mlflow" in i for i in all_imports):
                 st.success("✅ **Evidence**: Automated Metric Tracking detected (`mlflow`).")
            else:
                 st.warning("⚠️ **Gap**: No automated experiment tracking detected.")
        
        with c2:
            st.markdown("**15(3) Cybersecurity (Resilience)**")
            if issues:
                st.error(f"❌ **Gap**: {len(issues)} supply chain vulnerabilities detected.")
                st.caption(f"Impacts 'Resilience' claim against third-party exploitation.")
            else:
                st.success("✅ **Evidence**: Zero known vulnerabilities. Integrity Seal valid.")

    st.divider()
    st.caption("ℹ️ *This evidence is automatically injected into the Annex IV.2 Generator.*")

# --- MAIN RENDER ---
def render_dashboard():
    # Header with Logo/Title
    logo_path = "/home/morganrcu/proyectos/venturalitica-integration/landing/public/vl.svg"
    
    col_logo, col_title = st.columns([0.1, 0.9])
    with col_logo:
        if os.path.exists(logo_path):
            st.image(logo_path, width=64)
        else:
            st.write("# 🛡️")
    with col_title:
        st.title("Venturalítica Local Compliance")
        st.markdown("*Empowering developers to build compliant AI by design.*")

    # Local Project Context
    target_dir = os.getcwd()
    st.sidebar.markdown("### 📁 Project Context")
    st.sidebar.text(f"Root: {os.path.basename(target_dir)}")
    
    if st.sidebar.button("🔄 Refresh Local Scan", use_container_width=True):
        with st.spinner("Deep Scanning artifacts (BOM, AST, Security)..."):
            try:
                # Use Full Scanner Node
                nodes = NodeFactory(model_name=st.session_state.get('model_name', 'mistral'))
                dummy_state = {"project_root": target_dir}
                scan_result = nodes.scan_project(dummy_state)
                
                st.session_state['bom'] = scan_result.get('bom')
                st.session_state['evidence_hash'] = scan_result.get('evidence_hash')
                st.session_state['bom_security'] = scan_result.get('bom_security')
                st.session_state['code_context'] = scan_result.get('code_context')
                st.session_state['runtime_meta'] = scan_result.get('runtime_meta')
                
                st.sidebar.success("Deep Scan Complete!")
            except Exception as e:
                st.sidebar.error(f"Scan failed: {e}")

    # Load results from disk if available
    results = load_cached_results()
    if results and 'results' not in st.session_state:
        st.session_state['results'] = results

    # TABS
    tab_feed, tab_tech, tab_gov, tab_annex, tab_int = st.tabs([
        "👁️ Transparency Feed",
        "✅ Technical Integrity", 
        "🏛️ Policy Enforcement", 
        "📄 Annex IV.2 Generator",
        "🔗 Integrations"
    ])
    
    # TAB 0: TRANSPARENCY FEED (New)
    with tab_feed:
        st.header("Transparency Feed")
        st.markdown("**Glass Box Integrity**: Verify the exact evidence used by the AI Agent.")
        
        # 1. Integrity Seal
        hash_val = st.session_state.get('evidence_hash', 'Not Scanned')
        if hash_val != 'Not Scanned':
            st.success(f"🔐 **Evidence Hash (SHA-256):** `{hash_val}`")
            st.caption("This hash anchors the documentation to this specific version of your codebase.")
        else:
            st.warning("⚠️ Evidence not yet hashed. Run 'Refresh Local Scan' in sidebar.")

        col_feed_1, col_feed_2 = st.columns(2)
        with col_feed_1:
            st.subheader("🛡️ Supply Chain Security")
            sec = st.session_state.get('bom_security', {})
            if sec:
                if sec.get('vulnerable'):
                    st.error(f"❌ Vulnerabilities Detected: {len(sec.get('issues', []))}")
                    for issue in sec.get('issues', []):
                        severity = issue.get('severity', 'UNKNOWN')
                        color = {"CRITICAL": "red", "HIGH": "orange", "MEDIUM": "blue", "LOW": "green"}.get(severity, "grey")
                        
                        with st.expander(f"🚨 {issue['package']} {issue['version']} [{severity}]"):
                            st.write(f"**Description:** {issue['summary']}")
                            st.markdown(f"[View Advisory]({issue['link']})")
                            st.caption(f"Score: {issue.get('score', 'N/A')}")
                else:
                    st.success("✅ No known vulnerabilities found in BOM (OSV.dev)")
            else:
                 st.info("Run scan to check security.")

        with col_feed_2:
             st.subheader("📝 Compliance Evidence")
             ctx = st.session_state.get('code_context', {})
             sec = st.session_state.get('bom_security', {})
             
             if ctx:
                 # NEW: Professional Compliance Mapping
                 render_compliance_mapping(ctx, sec, st.session_state.get('runtime_meta', {}))
                 
                 with st.expander("🔍 View Raw Evidence (Technical)"):
                     selected_file = st.selectbox("Select specific file", list(ctx.keys()))
                     if selected_file:
                         st.code(ctx[selected_file].get('raw_source', "No source available") if isinstance(ctx[selected_file], dict) else "Data mismatch", language="python")
             else:
                 st.info("Run scan to see captured code context.")

    # TAB 1: Technical Integrity
    with tab_tech:
        st.header("Technical verification")
        
        c1, c2, c3 = st.columns(3)
        
        # 0. Load Data
        bom = st.session_state.get('bom')
        results = st.session_state.get('results')
        runtime_meta = st.session_state.get('runtime_meta')
        
        if bom:
            metrics, models, libs = _parse_bom(bom)
            c1.metric("Dependencies", metrics['total'])
            c2.metric("ML Models (Static)", metrics['models'])
            
            # UNIQUE LICENSES from components
            unique_lics = metrics.get('licenses', 0)
            c3.metric("Licenses", unique_lics)
        else:
            c1.metric("Dependencies", "0")
            c2.metric("ML Models", "0")
            c3.metric("Licenses", "0")
            
        st.divider()
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("🤖 AI Architecture")
            if runtime_meta:
                 model_info = runtime_meta.get("model", {})
                 with st.container(border=True):
                     st.markdown(f"**Primary Model:** `{model_info.get('class', 'Unknown')}`")
                     st.markdown(f"**Framework:** `{model_info.get('module', 'Unknown')}`")
                     if 'params' in runtime_meta:
                         with st.expander("Hyperparameters", expanded=False):
                             st.json(runtime_meta['params'])
            elif 'bom' in st.session_state:
                st.info("No runtime metadata found. Using static scan results.")
                if models:
                    for m in models:
                        st.write(f"- {m['name']} (Detected in {m.get('description', 'source')})")
            else:
                st.info("Run scan to see architecture.")

            st.subheader("📦 Module Inventory")
            if 'bom' in st.session_state:
                sub_tabs = st.tabs(["Supply Chain", "Raw BOM"])
                with sub_tabs[0]:
                    if libs:
                        lib_df = [{"Library": l['name'], "Version": l.get('version', 'N/A')} for l in libs]
                        st.dataframe(lib_df, use_container_width=True, hide_index=True)
                with sub_tabs[1]:
                    st.json(st.session_state['bom'], expanded=False)

        with col_right:
            st.subheader("🍃 Sustainability Tracker")
            emissions_path = os.path.join(target_dir, "emissions.csv")
            if os.path.exists(emissions_path):
                import pandas as pd
                try:
                    df = pd.read_csv(emissions_path)
                    last_run = df.iloc[-1]
                    st.metric("Total CO2 Emissions", f"{last_run['emissions'] * 1000:.4f} gCO2")
                    st.markdown(f"**Compute:** {last_run['cpu_model'] if 'cpu_model' in last_run else 'Cloud Instance'}")
                    st.markdown(f"**Duration:** {last_run['duration'] if 'duration' in last_run else 'N/A'}s")
                    
                    # Small area chart for emissions over time
                    if len(df) > 1:
                        st.area_chart(df['emissions'])
                except Exception as e:
                    st.error(f"Error reading emissions: {e}")
            else:
                st.warning("No emissions data found. Run pipeline with `codecarbon` enabled.")

            st.subheader("🎖️ Compliance Status")
            if results:
                passed = sum(1 for r in results if r.get('passed'))
                total = len(results)
                status = 'passing' if passed == total else 'failing'
                badge_path = Path("compliance_badge.svg")
                generate_compliance_badge(status, policy_name="Local Audit", output_path=badge_path)
                st.image("compliance_badge.svg")
            else:
                st.info("Waiting for audit results...")

    # TAB 2: Policy Enforcement
    with tab_gov:
        st.header("Governance & Policy Scan")
        
        if results:
            st.markdown("### Latest Audit Results")
            for r in results:
                status_class = "compliance-pass" if r.get('passed') else "compliance-fail"
                mark = "✅" if r.get('passed') else "❌"
                # Clean up expander title to avoid overlap
                label = f"{mark} {r.get('control_id')} | {r.get('description')[:50]}..."
                with st.expander(label):
                    st.write(f"**Metric:** {r.get('metric_key')}")
                    st.write(f"**Value:** {r.get('actual_value'):.4f} (Threshold: {r.get('operator')}{r.get('threshold')})")
                    if not r.get('passed'):
                        st.error(f"Red flag: {r.get('severity')} risk detected.")
        else:
            st.info("No audit results found. Run `enforce()` in your training script.")
            
        st.divider()
        st.markdown("#### 💡 Governance Recommendation")
        st.info("Based on your local scan, you are missing a 'Human-in-the-Loop' mechanism for critical decisions.")

    # TAB 3: Annex IV.2 Generator (NEW FEATURE)
    with tab_annex:
        st.header("Technical Documentation Generator")
        st.markdown("Generate compliant documentation for the **EU AI Act Annex IV**.")
        
        # State management for Annex
        if 'annex_sections' not in st.session_state:
            st.session_state['annex_sections'] = {}

        # MODEL SELECTION
        st.session_state['model_name'] = st.selectbox("Select Local LLM", ["mistral", "llama3", "phi3"], index=0)

        # LANGUAGE SELECTION (Choice)
        available_langs = [
            "English", "Spanish", "French", "German", "Italian", "Catalan", 
            "Basque", "Galician", "Bulgarian", "Croatian", "Czech", "Danish", 
            "Dutch", "Estonian", "Finnish", "Greek", "Hungarian", "Irish", 
            "Latvian", "Lithuanian", "Maltese", "Polish", "Portuguese", 
            "Romanian", "Slovak", "Slovenian", "Swedish"
        ]
        selected_langs = st.multiselect("Select Languages (Multi-lingual Batch)", available_langs, default=["English"])

        # SMART SCAN BUTTON (Real AI)
        if st.button("✨ Smart Draft with Compliance-RAG", type="primary", use_container_width=True):
            status_container = st.container()
            with st.spinner("Orchestrating AI Agents..."):
                # Run async graph in sync streamlit
                # MODIFIED: Expecting tuple (markdown, sections)
                ret_val = asyncio.run(run_compliance_graph(target_dir, status_container, selected_langs))
                if ret_val:
                    # Handle legacy return or new tuple
                    if isinstance(ret_val, tuple):
                        final_md, sections = ret_val
                        st.session_state['annex_full_md'] = final_md
                        st.session_state['annex_sections'] = sections
                    else:
                        st.session_state['annex_full_md'] = ret_val
                    
                    st.success("Draft generated by Mistral (Local)!")

        st.divider()
        
        # EDITOR (Side-by-Side)
        st.markdown("### 📝 Annex IV.2 Editor & Preview")
        
        sections = st.session_state.get('annex_sections', {})
        if sections:
            # Layout: Editor on Left, Preview on Right
            ed_col, pre_col = st.columns(2)
            
            with ed_col:
                st.markdown("#### 🛠️ Edit")
                sorted_keys = sorted(sections.keys())
                compiled_md = ""
                for key in sorted_keys:
                    content = sections[key]
                    new_content = st.text_area(f"[{key}]", value=content, height=250, key=f"editor_{key}")
                    sections[key] = new_content
                    compiled_md += f"\n\n## {key}\n{new_content}"
                st.session_state['annex_full_md'] = compiled_md
                st.session_state['annex_sections'] = sections
            
            with pre_col:
                st.markdown("#### 👁️ Preview")
                st.markdown(st.session_state.get('annex_full_md', ""))
            
        else:
            # Fallback for empty state or legacy string
            full_text = st.session_state.get('annex_full_md', "")
            e_col, r_col = st.columns(2)
            with e_col:
                edited_text = st.text_area("Full Document Editor", value=full_text, height=600)
                st.session_state['annex_full_md'] = edited_text
            with r_col:
                st.markdown(st.session_state.get('annex_full_md', ""))

        # EXPORT
        st.divider()
        c_ex1, c_ex2 = st.columns(2)
        with c_ex1:
             if st.button("💾 Export Master (English)"):
                with open("Annex_IV_en.md", "w") as f:
                    f.write(st.session_state.get('annex_full_md', ""))
                st.success("Saved to `Annex_IV_en.md`")
        
        with c_ex2:
             translations = st.session_state.get("translations", {})
             if translations:
                 if st.button(f"💾 Export All Translations ({len(translations)})"):
                     for lang, content in translations.items():
                         fname = f"Annex_IV_{lang}.md"
                         with open(fname, "w") as f:
                             f.write(content)
                     st.success(f"Exported {len(translations)} files.")
    
    # TAB 4: Integrations (The Governance Lens)
    # TAB 4: Integrations (The Governance Lens)
    with tab_int:
        st.header("Integrations Status")
        st.markdown("Monitor your **Governance Ecosystem** connectivity.")
        
        # Load captured integrations from runtime meta
        meta_integrations = st.session_state.get('runtime_meta', {}).get('integrations', {})
        
        c1, c2 = st.columns(2)
        
        # MLflow Status
        with c1:
            st.subheader("MLflow")
            mlflow_meta = meta_integrations.get('mlflow', {})
            
            # 1. Runtime Evidence (Best)
            if mlflow_meta.get('active'):
                st.success(f"🟢 **Synced (Runtime)**: Run `{mlflow_meta['run_id'][:8]}...`")
                st.markdown(f"**URI**: `{mlflow_meta['tracking_uri']}`")
                
                # Smart Link Construction
                base_uri = mlflow_meta['tracking_uri'].rstrip('/')
                exp_id = mlflow_meta.get('experiment_id', '0')
                run_id = mlflow_meta.get('run_id')
                
                if "localhost" in base_uri or "127.0.0.1" in base_uri:
                     # MLflow UI Standard Path
                     deep_link = f"{base_uri}/#/experiments/{exp_id}/runs/{run_id}"
                     st.link_button("View Run Detail", deep_link) 
                else: 
                     st.info("Remote Tracking Server detected.")
            
            # 2. Fallback: Env Check
            else:
                mlflow_env = os.environ.get("MLFLOW_TRACKING_URI")
                if mlflow_env:
                     st.warning(f"🟡 **Configured**: `{mlflow_env}` set but no active run captured.")
                elif os.path.exists("mlruns"):
                     st.warning("🟡 **Local**: Found `mlruns` directory.")
                else:
                     st.error("🔴 **Disconnected**: No configuration found.")

        # WandB Status
        with c2:
            st.subheader("Weights & Biases (Cloud)")
            wandb_meta = meta_integrations.get('wandb', {})
            
            # 1. Runtime Evidence (Best)
            if wandb_meta.get('active'):
                st.success(f"🟢 **Synced (Runtime)**: `{wandb_meta.get('entity')}/{wandb_meta.get('project')}`")
                if wandb_meta.get('run_url'):
                    st.link_button("View Run Dashboard ↗", wandb_meta['run_url'])
                else:
                    st.info("Run detected (URL missing).")
            
            # 2. Fallback: Env Check
            else:
                wandb_key = os.environ.get("WANDB_API_KEY")
                if wandb_key:
                    st.warning("🟡 **Configured**: `WANDB_API_KEY` present.")
                else:
                    st.error("🔴 **Disconnected**: `WANDB_API_KEY` missing.")

        st.divider()
        st.markdown("### 🏹 Deep Links")
        st.caption("Links are generated dynamically from the latest `vl.wrap()` execution.")

if __name__ == "__main__":
    render_dashboard()
