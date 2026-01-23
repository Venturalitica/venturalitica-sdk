import streamlit as st
from venturalitica.scanner import BOMScanner
from venturalitica.badges import generate_compliance_badge
from pathlib import Path
import os
import json
import time
import asyncio
from venturalitica.graph.workflow import create_compliance_graph
from langchain_core.messages import HumanMessage

# --- UI CONFIGURATION ---
st.set_page_config(
    page_title="Venturalitica | Local Compliance",
    layout="wide",
    page_icon="🛡️"
)

# --- STYLING ---
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Slab:wght@400;700&display=swap" rel="stylesheet">
<style>
    /* Global Body Font: Roboto */
    html, body, [class*="st-"], .stMarkdown, p, span, div, li, a {
        font-family: 'Roboto', sans-serif !important;
        color: #1f2937 !important;
    }
    
    /* Headers: Roboto Slab */
    h1, h2, h3, h4, h5, h6, .stTitle, [data-testid="stHeader"] h1, [data-testid="stMarkdownContainer"] h1, 
    [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {
        font-family: 'Roboto Slab', serif !important;
        font-weight: 700 !important;
        color: #111827 !important;
    }

    .main {
        background-color: #fefefe;
    }
    
    /* Metrics: Roboto Slab for values */
    [data-testid="stMetricValue"] {
        font-family: 'Roboto Slab', serif !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'Roboto', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.8rem;
        color: #6b7280; /* slate-500 */
    }

    /* Premium Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        font-family: 'Roboto', sans-serif !important;
        font-weight: 500 !important;
    }

    /* Custom Color Wrappers */
    .compliance-pass {
        color: #0369a1 !important; /* sky-700 */
        font-weight: 600;
    }
    .compliance-fail {
        color: #b91c1c !important; /* red-700 */
        font-weight: 600;
    }
    
    /* Box Styling */
    .annex-box {
        background-color: #f9fafb;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
    }
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
    graph = create_compliance_graph(model_name=st.session_state.get('model_name', 'mistral'))
    
    initial_state = {
        "project_root": target_dir,
        "bom": {},
        "runtime_meta": {},
        "sections": {},
        "final_markdown": ""
    }
    
    container.info("🚀 Launching Compliance-RAG...")
    
    # Stream the graph execution
    async for event in graph.astream(initial_state):
        for node, data in event.items():
            if node == "scanner":
                container.success("✅ Application scanned.")
                with container.expander("BOM Details"):
                    st.json(data.get("bom", {}))
            elif node == "planner":
                container.info("🗺️ Planning documentation structure...")
            elif node.startswith("writer_"):
                section = node.split("_")[1]
                container.markdown(f"✍️ **Drafted Section {section}**")
            elif node == "compiler":
                container.success("📄 Document compiled successfully!")
                return data.get("final_markdown")
                
    return None

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
        st.title("Venturalitica Local Compliance")
        st.markdown("*Empowering developers to build compliant AI by design.*")

    # Local Project Context
    target_dir = os.getcwd()
    st.sidebar.markdown("### 📁 Project Context")
    st.sidebar.text(f"Root: {os.path.basename(target_dir)}")
    
    if st.sidebar.button("🔄 Refresh Local Scan", use_container_width=True):
        with st.spinner("Analyzing artifacts..."):
            try:
                scanner = BOMScanner(target_dir)
                bom_json = scanner.scan()
                st.session_state['bom'] = json.loads(bom_json)
                st.sidebar.success("Scan Complete!")
            except Exception as e:
                st.sidebar.error(f"Scan failed: {e}")

    # Load results from disk if available
    results = load_cached_results()
    if results and 'results' not in st.session_state:
        st.session_state['results'] = results

    # TABS
    tab_tech, tab_gov, tab_annex = st.tabs([
        "✅ Technical Integrity", 
        "🏛️ Policy Enforcement", 
        "📄 Annex IV.2 Generator"
    ])

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
                with st.expander(f"{mark} {r.get('control_id')} | {r.get('description')[:60]}..."):
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
        if 'annex_draft' not in st.session_state:
            st.session_state['annex_draft'] = {
                "intended_purpose": "",
                "hardware": "",
                "description": "",
                "risk_system": ""
            }

        # MODEL SELECTION
        st.session_state['model_name'] = st.selectbox("Select Local LLM", ["mistral", "llama3", "phi3"], index=0)

        # SMART SCAN BUTTON (Real AI)
        if st.button("✨ Smart Draft with Compliance-RAG", type="primary", use_container_width=True):
            status_container = st.container()
            with st.spinner("Orchestrating AI Agents..."):
                # Run async graph in sync streamlit
                final_md = asyncio.run(run_compliance_graph(target_dir, status_container))
                if final_md:
                    st.session_state['annex_full_md'] = final_md
                    st.success("Draft generated by Mistral (Local)!")

        st.divider()
        
        # EDITOR
        st.markdown("### 📝 Annex IV.2 Editor")
        
        full_text = st.session_state.get('annex_full_md', "")
        edited_text = st.text_area("Full Document", value=full_text, height=600)
        st.session_state['annex_full_md'] = edited_text

        # EXPORT
        st.divider()
        if st.button("💾 Export to Markdown (Annex_IV.md)"):
            with open("Annex_IV.md", "w") as f:
                f.write(st.session_state.get('annex_full_md', ""))
            st.success("Document exported to `Annex_IV.md` in project root.")
            st.toast("Documentation Ready!")

if __name__ == "__main__":
    render_dashboard()
