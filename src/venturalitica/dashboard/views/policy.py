import streamlit as st

def render_policy_view():
    st.header("Governance & Policy Scan")
    
    results = st.session_state.get('results')
    
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
