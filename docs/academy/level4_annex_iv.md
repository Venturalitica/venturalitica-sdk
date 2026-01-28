# Level 4: The Architect (Annex IV Generation) 🔴

**Goal**: Automate the creation of 50+ page regulatory documents.

**Prerequisite**: [Level 3 (The Auditor)](level3_auditor.md)

---

## 1. The Bottleneck: "Technical Documentation"

According to **Article 11** and **Annex IV** of the EU AI Act, High-Risk systems (like **Credit Scoring**) require comprehensive Technical Documentation.
Writing this manually takes **weeks**.

## 2. The Solution: Generative Compliance

We use your **Policies (Level 1 & 2)** and **Evidence (Level 2/3)** to prompt an LLM to draft the document for you. 

Venturalítica supports:

- **Cloud**: Mistral (via API).
- **Local**: Ollama (General purpose).
- **Sovereign (NEW)**: **ALIA** (Spanish Native GGUF via Llama.cpp) - *Experimental*.

### The Upgrade

We continue working on the "Loan Scoring" project.

> 💡 **Full Code**: You can find the automation script for Annex IV generation here: [generate_annex_iv.py](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/generate_annex_iv.py)

### Run the High-Risk Audit

Ensure you have run the collection steps:

```python
# 1. Load Data
df = vl.load_sample("loan")
train_df = df.sample(frac=0.8)
val_df = df.drop(train_df.index)

# 2. Run the Article 10 (Data) & Article 15 (Model) Governance Audit
with vl.monitor("loan_annex_audit"):
    # 2.1 Verify Training Data (Art 10)
    # Download data_policy.oscal.yaml: https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/policies/loan/data_policy.oscal.yaml
    vl.enforce(data=train_df, policy="data_policy.oscal.yaml", target="class")
    
    # 2.2 Verify Model Performance (Art 15)
    # Download model_policy.oscal.yaml: https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/policies/loan/model_policy.oscal.yaml
    vl.enforce(
        data=val_df.assign(prediction=val_df['class']), # Simulated model
        policy="model_policy.oscal.yaml", 
        target="class",
        prediction="prediction"
    )
```

## 3. Generate the Document

1.  Open the Dashboard: `uv run venturalitica ui`.
2.  Go to the **"Annex IV Generator"** tab.
3.  Select Provider: **Cloud (Mistral)**, **Local (Ollama)**, or **Sovereign (ALIA - Experimental)**.
4.  Click **"Generate Annex IV"**.

    ![Annex IV Generator](../assets/academy/annex_iv_generator.png)

### The Generation Process
Watch the logs. The System is acting as a **Team of Agents**:

1.  **Scanner**: Reads your `trace.json` (The Evidence).
2.  **Planner**: Decides which sections of Annex IV apply to your specific model type.
3.  **Writer**: Drafts "Section 2.c: Architecture" using the `summary()` from your actual Python code.
4.  **Critic**: Reviews the draft against the ISO 42001 standard.

**Result**: A markdown file (`Annex_IV.md`) that cites your specific accuracy scores (e.g., `Demographic Parity: 0.92`) as proof of safety.

## 4. Selecting your LLM

| Feature | Cloud (Mistral API) | Local (Ollama) | Sovereign (ALIA - Experimental) |
| :--- | :--- | :--- | :--- |
| **Privacy** | ☁️ Encrypted Transport | 🔒 100% Offline | 🛡️ Hardware Locked |
| **Sovereignty** | 🇫🇷 Hosted in EU | ✅ Generic | 🇪🇸 **Spanish Native** |
| **Speed** | ⚡ Fast (Large Model) | 🐢 Slower | 🐢 **Slow (Experimental)** |
| **Use Case** | Final High-Quality Polish | Iterative Testing | **Research Only** |

We currently offer **ALIA** as an experimental feature for organizations piloting Spanish-native sovereign AI.

!!! warning "Experimental Feature & Hardware Requirements"
    ALIA is a 40B parameter model. It is marked as **EXPERIMENTAL** and requires significant hardware resources:
    
    *   **RAM/VRAM**: ~41GB required (Q8 quantization).
    *   **GPU**: A high-end GPU (e.g., RTX 3090/4090 with 24GB+) is recommended for usable speeds.
    *   **Performance**: On consumer hardware or smaller GPUs (like RTX 2000), inference will effectively run on CPU and be very slow.

## 5. Export to PDF

By default, we generate `Annex_IV.md` (Markdown) for version control. To convert this to a regulatory-grade PDF:

=== "Python (mdpdf)"
    ```bash
    uv pip install mdpdf
    uv run mdpdf Annex_IV.md
    ```

=== "Pandoc (Advanced)"
    ```bash
    pandoc Annex_IV.md -o Annex_IV.pdf --toc --pdf-engine=xelatex
    ```

## 6. Take Home Messages 🏠

1.  **Documentation is a Function**: `f(Evidence) -> Document`. Never write what you can generate.
2.  **LiveTrace**: If your accuracy drops tomorrow, regenerate the document. It will reflect the *current* state, preventing "Documentation Drift".
3.  **The Full Loop**: You have gone from Code -> Policy (L1) -> Ops (L2) -> Evidence (L3) -> Legal Document (L4).

---

### 🎉 Congratulations!
You have completed the **Venturalítica Academy**.
You are now ready to integrate this into your own CI/CD pipeline.

👉 **[Deep Dive: MLOps Integration](../integrations.md)**
👉 **[Deep Dive: Training Loop](../training.md)**
