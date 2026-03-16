try:
    import streamlit as st
except ImportError:
    raise ImportError(
        "streamlit is required for the dashboard. "
        "Install with: pip install venturalitica[dashboard]"
    )


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
            all_imports.update(data.get("imports", []))

    st.markdown("### 🇪🇺 Regulatory Compliance Map")
    st.markdown("""
    *This mapping connects technical evidence to EU AI Act obligations **IF** the system is classified as High-Risk (Annex III).*
    """)

    # 9. Article 9: Risk Management System
    with st.expander("⚖️ Article 9: Risk Management System", expanded=True):
        audit_results = runtime_meta.get("audit_results", [])
        bias_concerns = [
            r for r in audit_results if "disparate_impact" in r or "bias" in r
        ]

        if bias_concerns:
            st.info(
                f"**Fundamental Rights Risk (Fairness):** Detected {len(bias_concerns)} fairness checks."
            )
            for check in bias_concerns:
                if "FAIL" in check:
                    st.error(f"❌ **Risk Materialized**: {check}")
                else:
                    st.success(f"✅ **Mitigation Verified**: {check}")
        else:
            st.caption(
                "No fairness/bias evaluations found in runtime traces. Risk identification pending."
            )

    # 10. Article 10: Data Assurance
    with st.expander("📄 Article 10: Data Assurance & Quality"):
        risk_libraries = [
            i
            for i in all_imports
            if any(k in i.lower() for k in ["sklearn", "mlflow", "statsmodels"])
        ]
        data_libraries = [
            i for i in all_imports if any(k in i.lower() for k in ["pandas", "numpy"])
        ]

        if risk_libraries:
            st.info(
                "**Obligation Context:** Training, validation, and testing datasets must be relevant, representative, and free of errors."
            )
            st.markdown("#### 🔍 Technical Evidence Detected:")
            st.markdown(f"- **Modeling Frameworks**: `{', '.join(risk_libraries[:3])}`")
            if data_libraries:
                st.markdown(f"- **Data Processing**: `{', '.join(data_libraries[:3])}`")
            st.success(
                "✅ **Action**: This evidence supports the 'Data Assurance' chapter of your Technical File."
            )
        else:
            st.caption("No ML modeling libraries detected.")

    # 11. Article 11: Technical Documentation
    with st.expander("📁 Article 11: Technical Documentation"):
        st.info(
            "The provider must draw up technical documentation demonstrating conformity."
        )
        has_bom = st.session_state.get("bom") is not None
        has_annex = st.session_state.get("annex_sections") != {}

        c1, c2 = st.columns(2)
        with c1:
            if has_bom:
                st.success("✅ **Evidence**: SBOM available.")
            else:
                st.warning("⚠️ **Gap**: SBOM not scanned.")
        with c2:
            if has_annex:
                st.success("✅ **Evidence**: Annex IV Draft exists.")
            else:
                st.warning("⚠️ **Gap**: Annex IV not generated.")

    # 12. Article 12: Record-Keeping
    with st.expander("📝 Article 12: Record-Keeping"):
        st.info("Automatic logging of events ('logs') over the lifetime of the system.")
        if st.session_state.get("evidence_hash"):
            st.success(
                f"✅ **Evidence**: Cryptographic Hash (`{st.session_state['evidence_hash'][:8]}...`) anchored."
            )
        if runtime_meta:
            st.success("✅ **Evidence**: Execution traces (runtime_meta) captured.")
        else:
            st.warning("⚠️ **Gap**: No runtime records detected.")

    # 13. Article 13: Transparency & Provision of Information
    with st.expander("👁️ Article 13: Transparency"):
        st.info(
            "Systems must be accompanied by instructions for use to enable users to interpret output."
        )
        if "raw_source" in str(code_context):
            st.success(
                "✅ **Evidence**: Source code visibility enabled (Technical Transparency)."
            )
        else:
            st.warning("⚠️ **Gap**: Evidence opacity.")

    # 14. Article 14: Human Oversight
    with st.expander("👤 Article 14: Human Oversight"):
        st.info("Designed to be effectively overseen by natural persons.")
        has_human = any("stream" in i for i in all_imports) or any(
            "gradio" in i for i in all_imports
        )
        if has_human:
            st.success("✅ **Evidence**: Interactive oversight interface detected.")
        else:
            st.warning(
                "⚠️ **Gap**: No human-in-the-loop nodes detected in control flow."
            )

    # 15. Article 15: Accuracy, Robustness & Cybersecurity
    with st.expander("🛡️ Article 15: Accuracy & Cybersecurity"):
        issues = bom_security.get("issues", [])

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**15(1) Accuracy & Robustness**")
            if any("mlflow" in i for i in all_imports):
                st.success(
                    "✅ **Evidence**: Automated Metric Tracking detected (`mlflow`)."
                )
            else:
                st.warning("⚠️ **Gap**: No automated experiment tracking detected.")

        with c2:
            st.markdown("**15(3) Cybersecurity (Resilience)**")
            if issues:
                st.error(
                    f"❌ **Gap**: {len(issues)} supply chain vulnerabilities detected."
                )
                st.caption(
                    "Impacts 'Resilience' claim against third-party exploitation."
                )
            else:
                st.success(
                    "✅ **Evidence**: Zero known vulnerabilities. Integrity Seal valid."
                )

    # HUDERIA: Council of Europe Framework Convention on AI & Human Rights
    with st.expander("🏛️ HUDERIA: Fundamental Rights Impact Assessment (Council of Europe)"):
        st.info(
            """
            **HUDERIA** (Human Rights, Democracy and Rule of Law Impact Assessment) is a
            non-binding Council of Europe methodology for evaluating AI impact on fundamental rights.
            It complements GDPR and the EU AI Act with a human rights lens.

            This assessment follows HUDERIA's 4-element methodology:
            1. **COBRA** (Context-Based Risk Analysis),
            2. **SEP** (Stakeholder Engagement Process),
            3. **RIA** (Rights Impact Assessment),
            4. **Mitigation Planning**.
            """
        )

        audit_results = runtime_meta.get("audit_results", [])
        huderia_controls = [r for r in audit_results if "huderia-cobra" in r.lower()]

        col1, col2, col3, col4 = st.columns(4)

        # COBRA Assessment
        with col1:
            st.markdown("#### COBRA ✓/✗")
            if huderia_controls:
                cobra_passes = [r for r in huderia_controls if "PASS" in r]
                cobra_fails = [r for r in huderia_controls if "FAIL" in r]
                if cobra_fails:
                    st.error(f"❌ {len(cobra_fails)} risk factors detected")
                    for fail in cobra_fails[:3]:
                        st.caption(f"- {fail[:60]}...")
                else:
                    st.success(f"✅ All {len(cobra_passes)} risk factors acceptable")
            else:
                st.caption("No COBRA assessment run yet")

        # SEP Assessment
        with col2:
            st.markdown("#### SEP ✓/✗")
            sep_found = any("stakeholder" in r.lower() for r in audit_results)
            if sep_found:
                st.success("✅ Stakeholder engagement documented")
            else:
                st.warning("⚠️ Stakeholder engagement not assessed")

        # RIA Assessment
        with col3:
            st.markdown("#### RIA ✓/✗")
            privacy_metrics = [r for r in audit_results if any(
                k in r.lower() for k in ["k_anonymity", "l_diversity", "t_closeness", "data_minimization"]
            )]
            bias_metrics = [r for r in audit_results if any(
                k in r.lower() for k in ["disparate_impact", "demographic_parity", "causal_fairness"]
            )]
            if privacy_metrics or bias_metrics:
                st.success(
                    f"✅ Rights Impact metrics: {len(privacy_metrics)} privacy + {len(bias_metrics)} bias"
                )
            else:
                st.warning("⚠️ No detailed rights impact metrics run")

        # Mitigation Plan
        with col4:
            st.markdown("#### Mitigation ✓")
            st.success("→ See [HUDERIA Methodology Guide](https://www.coe.int/)")
            st.caption("Define mitigation strategy per COBRA findings")

        st.divider()

        # Detailed Findings
        if huderia_controls:
            st.markdown("#### Detailed COBRA Findings")
            for control in huderia_controls[:5]:
                if "FAIL" in control:
                    st.error(control)
                else:
                    st.success(control)
            if len(huderia_controls) > 5:
                st.caption(f"... and {len(huderia_controls) - 5} more controls")

    st.divider()
    st.caption(
        "ℹ️ *This evidence is automatically injected into the Annex IV.2 Generator.*"
    )
