# Level 4: The Architect (Annex IV Generation) 🔴

**Goal**: Automate the creation of 50+ page regulatory documents.

**Prerequisite**: [Level 3 (The Auditor)](https://venturalitica.github.io/venturalitica-sdk/academy/level3_auditor/index.md)

______________________________________________________________________

## 1. The Bottleneck: "Technical Documentation"

According to **Article 11** and **Annex IV** of the EU AI Act, High-Risk systems (like **Credit Scoring**) require comprehensive Technical Documentation. Writing this manually takes **weeks**.

## 2. The Solution: Generative Compliance

We use your **Policies (Level 1 & 2)** and **Evidence (Level 2/3)** to prompt an LLM to draft the document for you.

Venturalítica supports:

- **Cloud**: Mistral (via API).
- **Local**: Ollama (General purpose).
- **Sovereign (NEW)**: **ALIA** (Spanish Native GGUF via Llama.cpp) - *Experimental*.

### The Upgrade

We continue working on the "Loan Scoring" project.

### Run the High-Risk Audit

Ensure you have run the collection steps:

```
# Run the Article 10 (Data) & Article 15 (Model) Governance Audit
with vl.monitor("loan_annex_audit"):
    # 1. Verify Training Data (Art 10)
    vl.enforce(data=train_df, policy="data_governance.yaml", target="class")

    # 2. Verify Model Performance (Art 15)
    vl.enforce(
        data=val_df.assign(prediction=model.predict(val_df)), 
        policy="model_policy.yaml", 
        target="prediction"
    )
```

## 3. Generate the Document

1. Open the Dashboard: `uv run venturalitica ui`.
1. Go to the **"Annex IV Generator"** tab.
1. Select Provider: **Cloud (Mistral)**, **Local (Ollama)**, or **Sovereign (ALIA - Experimental)**.
1. Click **"Generate Annex IV"**.

### The Generation Process

Watch the logs. The System is acting as a **Team of Agents**:

1. **Scanner**: Reads your `trace.json` (The Evidence).
1. **Planner**: Decides which sections of Annex IV apply to your specific model type.
1. **Writer**: Drafts "Section 2.c: Architecture" using the `summary()` from your actual Python code.
1. **Critic**: Reviews the draft against the ISO 42001 standard.

**Result**: A markdown file (`Annex_IV.md`) that cites your specific accuracy scores (e.g., `Demographic Parity: 0.92`) as proof of safety.

## 4. Selecting your LLM

| Feature         | Cloud (Mistral API)       | Local (Ollama)    | Sovereign (ALIA - Experimental) |
| --------------- | ------------------------- | ----------------- | ------------------------------- |
| **Privacy**     | ☁️ Encrypted Transport    | 🔒 100% Offline   | 🛡️ Hardware Locked              |
| **Sovereignty** | 🇫🇷 Hosted in EU           | ✅ Generic        | 🇪🇸 **Spanish Native**           |
| **Speed**       | ⚡ Fast (Large Model)     | 🐢 Slower         | 🐢 **Slow (Experimental)**      |
| **Use Case**    | Final High-Quality Polish | Iterative Testing | **Research Only**               |

We currently offer **ALIA** as an experimental feature for organizations piloting Spanish-native sovereign AI.

Experimental Feature & Hardware Requirements

ALIA is a 40B parameter model. It is marked as **EXPERIMENTAL** and requires significant hardware resources:

- **RAM/VRAM**: ~41GB required (Q8 quantization).
- **GPU**: A high-end GPU (e.g., RTX 3090/4090 with 24GB+) is recommended for usable speeds.
- **Performance**: On consumer hardware or smaller GPUs (like RTX 2000), inference will effectively run on CPU and be very slow.

## 5. Export to PDF

By default, we generate `Annex_IV.md` (Markdown) for version control. To convert this to a regulatory-grade PDF:

```
uv pip install mdpdf
uv run mdpdf Annex_IV.md
```

```
pandoc Annex_IV.md -o Annex_IV.pdf --toc --pdf-engine=xelatex
```

## 6. Take Home Messages 🏠

1. **Documentation is a Function**: `f(Evidence) -> Document`. Never write what you can generate.
1. **LiveTrace**: If your accuracy drops tomorrow, regenerate the document. It will reflect the *current* state, preventing "Documentation Drift".
1. **The Full Loop**: You have gone from Code -> Policy (L1) -> Ops (L2) -> Evidence (L3) -> Legal Document (L4).

______________________________________________________________________

### 🎉 Congratulations!

You have completed the **Venturalítica Academy**. You are now ready to integrate this into your own CI/CD pipeline.

👉 **[Deep Dive: MLOps Integration](https://venturalitica.github.io/venturalitica-sdk/integrations/index.md)** 👉 **[Deep Dive: Training Loop](https://venturalitica.github.io/venturalitica-sdk/training/index.md)**
