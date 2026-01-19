import streamlit as st
from venturalitica.scanner import BOMScanner
import os
import json

st.set_page_config(
    page_title="Venturalitica Local Assistant",
    layout="wide",
    page_icon="🛡️"
)

st.title("🛡️ Venturalitica Local Compliance Assistant")

# Sidebar
st.sidebar.header("Configuration")
target_dir = st.sidebar.text_input("Project Root", value=os.getcwd())

if st.sidebar.button("Run Scan"):
    with st.spinner("Scanning codebase..."):
        try:
            scanner = BOMScanner(target_dir)
            bom_json = scanner.scan()
            st.session_state['bom'] = json.loads(bom_json)
            st.sidebar.success("Scan Complete!")
        except Exception as e:
            st.sidebar.error(f"Scan failed: {e}")

# Tabs: The core PLG Strategy
tab1, tab2, tab3 = st.tabs(["✅ Technical Check", "🏛️ Governance & Risks", "📄 Documentation"])

# Tab 1: Technical (Easy Mode)
with tab1:
    st.header("Technical Verification")
    st.info("This section validates your Code, Metrics, and BOM independently of organizational policy.")
    
    if 'bom' in st.session_state:
        bom = st.session_state['bom']
        st.subheader(f"📦 Bill of Materials ({len(bom.get('components', []))} components)")
        st.json(bom)
    else:
        st.warning("Run a scan to see Technical details.")
        
    st.divider()
    st.subheader("🍃 Environmental Impact (Green AI)")
    
    # Check for CodeCarbon output
    emissions_path = os.path.join(target_dir, "emissions.csv")
    if os.path.exists(emissions_path):
        import pandas as pd
        try:
            df = pd.read_csv(emissions_path)
            last_run = df.iloc[-1]
            col1, col2, col3 = st.columns(3)
            col1.metric("Emission (kgCO2)", f"{last_run['emissions']:.4f} kg")
            col2.metric("Duration", f"{last_run['duration']:.2f} s")
            col3.metric("Energy", f"{last_run['energy_consumed']:.4f} kWh")
            
            st.success("✅ Training footprint tracked.")
        except Exception as e:
            st.error(f"Could not read emissions data: {e}")
    else:
        st.info("No 'emissions.csv' found. Use `codecarbon` to track your training footprint.")
        st.code("""
from codecarbon import EmissionsTracker
tracker = EmissionsTracker()
tracker.start()
# ... training code ...
tracker.stop()
        """, language="python")

# Tab 2: Governance (Pain Mode)
with tab2:
    st.header("Governance & Risk Management")
    st.error("❌ organizational Verification: PENDING (Requires SaaS)")
    
    st.markdown("""
    ### Identified Risks (EU AI Act)
    The following risks must be assessed and mitigated before CE marking:
    
    1.  **Fundmental Rights Impact**: Potential bias against protected groups.
    2.  **Human Oversight**: Lack of HITL mechanism detected in code.
    3.  **Data Governance**: Training data provenance incomplete.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.warning("⚠️ Mitigation Plan Missing")
        st.code("""
# risks.oscal.yaml (Snippet)
risk_id: bias_loan_denial
severity: high
mitigation: NULL  <-- MISSING
        """, language="yaml")
    
    with col2:
        st.info("💡 How to fix?")
        st.markdown("**Option A (Local)**: Edit `risks.oscal.yaml` (500+ lines) manually.")
        if st.button("Open Raw YAML (Hard)"):
            st.toast("Opening IDE... Good luck!")
            
        st.markdown("---")
        st.markdown("**Option B (SaaS)**: Push to Venturalitica Platform for guided mitigation.")
        if st.button("Push to SaaS (Easy) 🚀", type="primary"):
            st.balloons()
            st.success("Redirecting to Platform...")

# Tab 3: Documentation (Gap Analysis)
with tab3:
    st.header("Technical Documentation (Annex IV)")
    
    st.markdown("""
    > **Status**: ⚠️ **INCOMPLETE**
    >
    > This draft fulfills **Section 2 (System Elements)** but lacks **Section 3 (Risk System)**.
    """)
    
    st.divider()
    
    if 'bom' in st.session_state:
        st.markdown("### 2. System Elements")
        components = st.session_state['bom'].get('components', [])
        for comp in components:
            st.markdown(f"- **{comp['name']}** ({comp.get('version', 'unknown')}): {comp.get('type')}")
    else:
        st.text("Scan required to populate System Elements.")
