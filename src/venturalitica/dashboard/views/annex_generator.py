import streamlit as st
import os
import asyncio
from venturalitica.graph.workflow import create_compliance_graph

async def run_compliance_graph(target_dir, container, selected_languages, provider="auto", api_key=None):
    """
    Orchestrates the LangGraph workflow and streams updates to the UI.
    """
    graph = create_compliance_graph(model_name=st.session_state.get('model_name', 'mistral'), provider=provider, api_key=api_key)
    
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

def render_annex_view(target_dir):
    st.header("Technical Documentation Generator")
    st.markdown("Generate compliant documentation for the **EU AI Act Annex IV**.")
    
    # State management for Annex
    if 'annex_sections' not in st.session_state:
        st.session_state['annex_sections'] = {}

    # MODEL SELECTION
    col_prov, col_key = st.columns([1, 2])
    
    with col_prov:
        provider = st.radio("Inference Provider", ["Local (Ollama)", "Cloud (Mistral AI)", "Local (ALIA 40B - Experimental)"], index=0, horizontal=True)
        provider_map = {
            "Local (Ollama)": "local",
            "Cloud (Mistral AI)": "cloud",
            "Local (ALIA 40B - Experimental)": "transformers"
        }
        provider_code = provider_map[provider]
    
    entered_key = None
    with col_key:
        if provider_code == "cloud":
            env_key = os.getenv("MISTRAL_API_KEY")
            help_text = f"Detected in .env: {'✅ Yes' if env_key else '❌ No'}"
            entered_key = st.text_input("Mistral API Key", value=env_key if env_key else "", type="password", help=help_text)
            if not entered_key:
                st.warning("⚠️ API Key required for Cloud mode.")
            st.info("🚀 Using **Magistral** (Mistral Large) for high-precision auditing.")
        elif provider_code == "transformers":
            st.success("🤖 **Native Spanish Engine**: Optimized for EU AI Act compliance in Spanish.")
            st.info("💡 **EXPERIMENTAL**: Running **ALIA 40B (Q8)** locally. Model size is ~41GB. Expect slow generation on consumer hardware (CPU offloading).")

    if provider_code == "local":
            st.session_state['model_name'] = st.selectbox("Select Ollama Model", ["mistral", "llama3", "phi3"], index=0)
    elif provider_code == "transformers":
            st.session_state['model_name'] = "langtech-innovation/ALIA-40b-instruct-2512_nvfp4"
    else:
            st.session_state['model_name'] = "magistral-medium-latest"

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
            # Check for required keys
            can_run = True
            if provider_code == "cloud" and not entered_key:
                st.error("Cannot run Cloud Agent without API Key.")
                can_run = False
            elif provider_code == "huggingface" and not entered_key:
                st.error("Cannot run Hugging Face Agent without API Token.")
                can_run = False
            
            if can_run:
                ret_val = asyncio.run(run_compliance_graph(target_dir, status_container, selected_langs, provider_code, entered_key))
                if ret_val:
                    # Handle legacy return or new tuple
                    if isinstance(ret_val, tuple):
                        final_md, sections = ret_val
                        st.session_state['annex_full_md'] = final_md
                        st.session_state['annex_sections'] = sections
                    else:
                        st.session_state['annex_full_md'] = ret_val
                    
                    st.success(f"Draft generated by {provider.split(' ')[0]}!")

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
                val = sections[key]
                
                # Handle both legacy string format and new dict format
                if isinstance(val, dict):
                    content = val.get("content", "")
                    thinking = val.get("thinking", None)
                else:
                    content = val
                    thinking = None
                
                if thinking:
                    with st.expander(f"💭 Reasoning for {key}", expanded=False):
                        st.info(thinking)
                        
                new_content = st.text_area(f"[{key}]", value=content, height=250, key=f"editor_{key}")
                
                if isinstance(val, dict):
                    val["content"] = new_content
                    sections[key] = val
                else:
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
