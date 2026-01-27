# Generating Technical Documentation (Annex IV)

One of the most tedious parts of the EU AI Act is **Annex IV**: the requirement to maintain up-to-date technical documentation.

Venturalítica automates this by treating your code execution traces as the source of truth.

## The Annex IV Generator

You can generate a compliant draft of your Technical Documentation directly from the **Venturalítica Dashboard**.

### Step 1: Launch the Dashboard

Run the UI from your terminal in the root of your project:

```
venturalitica ui
```

### Step 2: Navigate to "Annex IV Generator"

1. Go to the **"Annex IV Generator"** tab in the top navigation.
1. Select your **Inference Provider**:
   - **Local (Ollama)**: Standard offline mode.
   - **Cloud (Mistral)**: High-quality, EU-hosted generation.
   - **Local (ALIA - Experimental)**: Spanish Sovereign model (Requires significant hardware).
1. Click **"Generate Annex IV"**.

The system will analyze your local `.venturalitica/` folder and pull: * **System Architecture** (from `bom.json`) * **Risk Management Status** (from Article 9 Audit Results) * **Data Governance** (from Article 10 Audit Results) * **Cybersecurity** (from CVE scans)

### Step 3: Download the Draft

You will see a live preview of the generated markdown file.

- Click **Download Draft** to save it as `Annex_IV_Draft.md`.
- You can then convert this Markdown file to PDF using your preferred tool (e.g., Pandoc or VS Code).

Dynamic Updates

Each time you run `vl.enforce()`, the underlying evidence updates. Generating a new report will always reflect the latest state of your system.

______________________________________________________________________

## Via CLI (Alternative)

For CI/CD pipelines, you can also generate this documentation without opening the UI:

```
venturalitica doc --output docs/technical_file.md
```

This command performs the same logic but saves the file directly to your specified path.
