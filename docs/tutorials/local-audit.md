# Tutorial: Your First Local Audit

This tutorial demonstrates the "Zero-Setup" power of Venturalitica. You will audit a project folder without writing a single line of Python training code.

**Goal**: Generate a compliance report for an existing project directory.

---

## Prerequisites

1.  Install the SDK:
    ```bash
    pip install venturalitica
    ```
2.  Have a project folder ready (e.g., `my-ml-project/`) containing some `.py` files and a `requirements.txt`.

---

## Step 1: Scan the Project

The scanner acts like an automated auditor. It reads your file structure to inventory your "Software Bill of Materials" (SBOM).

```bash
cd my-ml-project
venturalitica scan
```

**Output**:
```text
Scanning target: .
✓ BOM generated: ./bom.json
Found 42 components.
```

**What just happened?**
*   Venturalitica parsed your dependencies (`numpy`, `pandas`, `scikit-learn`).
*   It detected your ML models (e.g., `RandomForestClassifier`) by analyzing your source code (AST).
*   It saved everything into a standard `bom.json` file.

---

## Step 2: Launch the Dashboard

Now that you have evidence (the SBOM), let's inspect it.

```bash
venturalitica ui
```

This opens the **Compliance Dashboard** in your browser (`http://localhost:8501`).

**What to look for**:
1.  Navigate to **Article 11 (Documentation)**.
2.  You should see your **Software Bill of Materials** marked as **PRESENT**.
3.  Check **Article 15 (Security)**: Are there any known vulnerabilities in your dependencies?

---

## Step 3: Generate the Technical File

Finally, let's create the official document required by the EU AI Act (Annex IV).

```bash
venturalitica doc --output technical_file_draft.md
```

**Output**:
```text
📄 Generating Technical Documentation: technical_file_draft.md
✓ Documentation draft created: technical_file_draft.md
```

Open `technical_file_draft.md`. You will see a structured template pre-filled with the data from your scan:
*   **System Description**: Placeholders for you to fill.
*   **Technical Implementation**: A list of the ML models and libraries detected in Step 1.
*   **Risk Management**: Status of any fairness audits (if you had run `enforce` scripts).

---

## Summary

In less than 2 minutes, you have:
1.  **Inventoried** your supply chain.
2.  **Visualized** your compliance status.
3.  **Drafted** your legal documentation.

This is the **Local First** philosophy: immediate value, zero cloud dependency.
