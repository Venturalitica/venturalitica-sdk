import streamlit as st
import os
from pathlib import Path
from venturalitica.dashboard.components.metrics import parse_bom_metrics
from venturalitica.badges import generate_compliance_badge

def render_technical_view(target_dir):
    st.header("Technical verification")
    
    c1, c2, c3 = st.columns(3)
    
    # 0. Load Data
    bom = st.session_state.get('bom')
    results = st.session_state.get('results')
    runtime_meta = st.session_state.get('runtime_meta')
    
    if bom:
        metrics, models, libs = parse_bom_metrics(bom)
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
            if os.path.exists("compliance_badge.svg"):
                st.image("compliance_badge.svg")
        else:
            st.info("Waiting for audit results...")
