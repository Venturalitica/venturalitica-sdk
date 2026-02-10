import streamlit as st
from venturalitica.dashboard.components.compliance_map import render_compliance_mapping

def render_transparency_view(target_dir):
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
