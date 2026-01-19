---
title: "User Manual"
date: 2026-01-18T00:00:00+01:00
draft: false
weight: 1
---

# User Manual: Venturalitica SDK

## 1. Installation

```bash
# Core SDK
pip install venturalitica-sdk

# With standard metrics (sklearn/numpy)
pip install "venturalitica-sdk[metrics]"

# With Green AI (Carbon Tracking) 🍃
pip install "venturalitica-sdk[green]"
```

## 2. CLI Reference

### `scan`
Generates a Software Bill of Materials (BOM) including Python libraries and ML Models.

```bash
venturalitica scan --target ./project-dir
```
*   **Output**: `bom.json` (CycloneDX format).
*   **Behavior**: Scans `pyproject.toml`, `requirements.txt`, and parses AST for `sklearn`/`torch` models.

### `ui`
Launches the Local Compliance Assistant dashboard.

```bash
venturalitica ui
```
*   **Address**: `http://localhost:8501`
*   **Features**: Technical Checks, Governance "Red Flags", Draft Documentation.

## 3. Configuration (`risks.oscal.yaml`)

The SDK enforces policies defined in OSCAL.

```yaml
policy:
  - id: "human-oversight"
    risk_level: "high"
    mitigation: "manual-review"
```

Use the Dashboard to visualize which risks are unmitigated.
