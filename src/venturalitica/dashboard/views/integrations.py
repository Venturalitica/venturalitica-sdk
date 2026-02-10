import streamlit as st
import os

def render_integrations_view():
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
