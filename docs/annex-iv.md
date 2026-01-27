# Generating Technical Documentation (Annex IV)

One of the most tedious parts of the EU AI Act is **Annex IV**: the requirement to maintain up-to-date technical documentation.

Venturalítica automates this by treating your code execution traces as the source of truth.

## The Annex IV Generator

You can generate a compliant draft of your Technical Documentation directly from the **Venturalítica Dashboard**.

### Step 1: Launch the Dashboard

Run the UI from your terminal in the root of your project:

```bash
venturalitica ui
```

### Step 2: Navigate to "Annex IV Generator"

In the left sidebar, look for the **GENERATE REPORTS** section.

1.  Click on **📄 technical_doc.md**.
2.  The system will analyze your local `.venturalitica/` folder.
3.  It will pull:
    *   **System Architecture** (from `bom.json`)
    *   **Risk Management Status** (from Article 9 Audit Results)
    *   **Data Governance** (from Article 10 Audit Results)
    *   **Cybersecurity** (from CVE scans)

### Step 3: Download the Draft

You will see a live preview of the generated markdown file.

*   Click **Download Draft** to save it as `Annex_IV_Draft.md`.
*   You can then convert this Markdown file to PDF using your preferred tool (e.g., Pandoc or VS Code).

!!! tip "Dynamic Updates"
    Each time you run `vl.enforce()`, the underlying evidence updates. Generating a new report will always reflect the latest state of your system.

---

## Via CLI (Alternative)

For CI/CD pipelines, you can also generate this documentation without opening the UI:

```bash
venturalitica doc --output docs/technical_file.md
```

This command performs the same logic but saves the file directly to your specified path.
