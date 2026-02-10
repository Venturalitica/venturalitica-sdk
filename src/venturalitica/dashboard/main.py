import streamlit as st
import os
from venturalitica.graph.nodes import NodeFactory

# Import Views
from venturalitica.dashboard.views.transparency import render_transparency_view
from venturalitica.dashboard.views.technical import render_technical_view
from venturalitica.dashboard.views.policy import render_policy_view
from venturalitica.dashboard.views.annex_generator import render_annex_view
from venturalitica.dashboard.views.integrations import render_integrations_view
from venturalitica.dashboard.components.metrics import load_cached_results

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
    
    with tab_feed:
        render_transparency_view(target_dir)

    with tab_tech:
        render_technical_view(target_dir)

    with tab_gov:
        render_policy_view()

    with tab_annex:
        render_annex_view(target_dir)

    with tab_int:
        render_integrations_view()

if __name__ == "__main__":
    render_dashboard()
