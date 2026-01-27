# The Compliance Gap (Roadmap)

Venturalítica **v0.4** provides the foundation for **Glass Box AI**, but high-risk systems (EU AI Act) require continuous improvement. This document identifies the current technical gaps and the features required to turn "Technical Evidence" into "Legal Certainty."

---

## ✅ Recently Closed Gaps (v0.4)

The "Deep Strategic Audit" and the **Academy** release have closed the following critical gaps:

### 1. Technical Documentation (Article 11)
*   **Previous Gap**: Manual writing of technical files.
*   **Solution**: **Annex IV Generator** (Mistral & **ALIA** Sovereign AI) now automates the drafting of regulatory documents.

### 2. Transparency & Trust (Article 13)
*   **Previous Gap**: No public-facing proof of compliance.
*   **Solution**: `vl.generate_compliance_badge()` creates a verifiable SVG linked to the evidence hash.

### 3. Resource Efficiency (Article 15)
*   **Previous Gap**: No tracking of energy or hardware usage.
*   **Solution**: `vl.monitor()` now automatically logs CO2 emissions and GPU/RAM consumption.

---

## 🛠 Missing Features & Open Gaps

### 1. Evidence Hardening (Article 12)
*   **Current State**: SHA-256 hashing of evidence files (The "Digital Seal").
*   **The Gap**: No native **Digital Signing** (Non-repudiation).
*   **Requirement**: Implementation of GPG/X.509 signing for `trace.json` files to ensure they cannot be forged even by the system owner.

### 2. Deep Data Governance (Article 10)
*   **Current State**: Basic class balance and missing value checks.
*   **The Gap**: Lack of **Data Lineage** and **Annotation Provenance**.
*   **Requirement**: Tools to log the source of labels, inter-annotator agreement metrics, and "poisoning" detection for training sets.

### 3. Human Oversight Interactive Checks (Article 14)
*   **Current State**: Static check for interactive elements (AST analysis).
*   **The Gap**: No runtime verification of "Human-in-the-loop" (HITL) actions.
*   **Requirement**: A `vl.oversight()` wrapper to record *when* a human actually approves/rejects a high-risk prediction in production.

### 4. Adversarial Robustness (Article 15)
*   **Current State**: Efficiency & Accuracy tracking (`vl.monitor`).
*   **The Gap**: No native **Attack Scanners** for security.
*   **Requirement**: Integration with robustness libraries (e.g., ART, CleverHans) to automate adversarial testing as part of the `enforce()` pipeline.

### 5. Automated Bias Mitigation
*   **Current State**: Detection only.
*   **The Gap**: Friction in fixing detected bias.
*   **Requirement**: Integration with Fairlearn/AIF360 for "suggested mitigations" directly in the Dashboard.

---

## 🚀 Propose a Feature

We are building the future of Responsible AI. If you have a specific requirement to fulfill a compliance mandate, we want to hear from you.

1.  **Open a [GitHub Issue](https://github.com/venturalitica/venturalitica-sdk/issues/new)**.
2.  Tag it as `feature-request` + `compliance-gap`.
3.  Describe the **Legal Article** (e.g., Art 13) or **Technical Pain** you are addressing.

[View Roadmap Discussions](https://github.com/venturalitica/venturalitica-sdk/discussions)
