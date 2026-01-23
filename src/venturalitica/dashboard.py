import streamlit as st
from venturalitica.scanner import BOMScanner
from venturalitica.badges import generate_compliance_badge
from pathlib import Path
import os
import json
import time

# --- UI CONFIGURATION ---
st.set_page_config(
    page_title="Venturalitica | Local Compliance",
    layout="wide",
    page_icon="🛡️"
)

# --- STYLING ---
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .compliance-pass {
        color: #28a745;
        font-weight: bold;
    }
    .compliance-fail {
        color: #dc3545;
        font-weight: bold;
    }
    .annex-box {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
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

def generate_annex_iv_draft(bom, results):
    """
    Simulated LLM scan of the project to generate Annex IV.2 sections.
    """
    time.sleep(1.5) # Simulate thinking
    
    # 1. System Elements (from BOM)
    components = bom.get('components', [])
    model_names = [c['name'] for c in components if c['type'] == 'machine-learning-model']
    
    # 2. Results Summary
    passed_count = sum(1 for r in results if r.get('passed')) if results else 0
    total_count = len(results) if results else 0
    
    draft = {
        "title": "Technical Documentation: Annex IV.2 (Draft)",
        "intended_purpose": "General credit risk assessment for consumer loans.",
        "hardware": "Cloud-based deployment on virtualized CPU instances.",
        "input_data": "Structured financial data including age, occupation, and credit history.",
        "description": f"The AI System is based on {', '.join(model_names) if model_names else 'standard ML architectures'}. "
                       f"It incorporates {len(components)} technical modules. "
                       f"Local validation shows {passed_count}/{total_count} compliance controls passed.",
        "risk_system": "The system includes automated bias detection and drift monitoring via Venturalitica SDK."
    }
    return draft

# --- MAIN RENDER ---
def render_dashboard():
    # Header with Logo/Title
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        st.write("# 🛡️")
    with col2:
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
        if 'bom' in st.session_state:
            comp_count = len(st.session_state['bom'].get('components', []))
            c1.metric("Modules Found", comp_count)
        else:
            c1.metric("Modules Found", "0")
            
        if results:
            passed = sum(1 for r in results if r.get('passed'))
            total = len(results)
            c2.metric("Controls Eval", f"{passed}/{total}")
            
            # GENERATE BADGE
            status = 'passing' if passed == total else 'failing'
            badge_path = Path("compliance_badge.svg")
            generate_compliance_badge(status, policy_name="Local Audit", output_path=badge_path)
            
            with c3:
                st.write("**Compliance Badge**")
                st.image("compliance_badge.svg")
                with open("compliance_badge.svg", "rb") as f:
                    st.download_button("Download Badge", f, "compliance_badge.svg", "image/svg+xml")
        else:
            c2.metric("Controls Eval", "N/A")
            c3.metric("EU AI Act Status", "Waiting")

        st.divider()
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("📦 Module Inventory (BOM)")
            if 'bom' in st.session_state:
                st.json(st.session_state['bom'], expanded=False)
            else:
                st.info("Run scan in sidebar to populate BOM.")

        with col_right:
            st.subheader("🍃 Sustainability")
            emissions_path = os.path.join(target_dir, "emissions.csv")
            if os.path.exists(emissions_path):
                import pandas as pd
                df = pd.read_csv(emissions_path)
                last_run = df.iloc[-1]
                st.success(f"Tracked: {last_run['emissions']:.4f} kgCO2")
                st.caption(f"Last record: {last_run['timestamp'] if 'timestamp' in last_run else 'Recently'}")
            else:
                st.warning("No emissions data found (CodeCarbon not used).")

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

        # SMART SCAN BUTTON (The "Aha!" Moment)
        if st.button("✨ Smart Draft with LLM Scan", type="primary", use_container_width=True):
            if 'bom' not in st.session_state:
                st.error("Please run a local scan first to provide context.")
            else:
                with st.spinner("LLM scanning project artifacts..."):
                    draft = generate_annex_iv_draft(st.session_state['bom'], results)
                    st.session_state['annex_draft'] = draft
                    st.success("Draft generated based on code analysis and audit results!")

        st.divider()
        
        # EDITOR
        st.markdown("### 📝 Annex IV.2 Editor")
        
        draft = st.session_state['annex_draft']
        
        colA, colB = st.columns(2)
        with colA:
            st.write("**1. General Description**")
            purpose = st.text_area("Intended Purpose", value=draft.get("intended_purpose", ""), height=100)
            hardware = st.text_area("Hardware & Resources", value=draft.get("hardware", ""), height=100)
            
        with colB:
            st.write("**2. System Details**")
            description = st.text_area("Technical Architecture", value=draft.get("description", ""), height=100)
            risk = st.text_area("Risk Management System", value=draft.get("risk_system", ""), height=100)

        # UPDATE LOCAL STATE
        st.session_state['annex_draft']["intended_purpose"] = purpose
        st.session_state['annex_draft']["hardware"] = hardware
        st.session_state['annex_draft']["description"] = description
        st.session_state['annex_draft']["risk_system"] = risk

        # EXPORT
        st.divider()
        if st.button("💾 Export to Markdown (Annex_IV.md)"):
            content = f"""# EU AI Act: Annex IV Technical Documentation
Generated by Venturalitica Assistant

## 1. General description
**Intended Purpose:**
{purpose}

**Hardware:**
{hardware}

## 2. Technical implementation
{description}

## 3. Risk management system
{risk}
"""
            with open("Annex_IV.md", "w") as f:
                f.write(content)
            st.success("Document exported to `Annex_IV.md` in project root.")
            st.toast("Documentation Ready!")

if __name__ == "__main__":
    render_dashboard()
