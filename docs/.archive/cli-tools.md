# CLI Tools

The Venturalítica SDK provides powerful command-line tools for project analysis, compliance scanning, and interactive governance management.

## 1. BOM Scanner: `venturalitica scan`

Generate a **CycloneDX ML-BOM** (Machine Learning Bill of Materials) for your project.

### What is an ML-BOM?

An ML-BOM is a standardized inventory of all components in your ML system:
- **Dependencies**: Python packages and versions
- **ML Models**: Detected model classes (scikit-learn, PyTorch, TensorFlow)
- **Frameworks**: MLOps tools (MLflow, WandB, ClearML)
- **Datasets**: Referenced data files

This is critical for:
- **Supply Chain Security**: Track vulnerable dependencies
- **Reproducibility**: Document exact versions used
- **Compliance**: EU AI Act Article 11 (Technical Documentation)
- **Auditing**: Provide evidence of system composition

### Usage

```bash
# Scan current directory
venturalitica scan

# Scan specific project
venturalitica scan --target ./my-ml-project
```

### Detection Method

Uses Python AST (Abstract Syntax Tree) parsing to find model instantiations in `.py` files without executing the code. It automatically detects:
- **scikit-learn**: Most common classifiers and regressors
- **Deep Learning**: PyTorch and TensorFlow/Keras models
- **Boosting**: XGBoost, LightGBM, CatBoost

---

## 2. Compliance Dashboard: `venturalitica ui`

Launch a local Streamlit dashboard for interactive compliance management.

### Usage

```bash
venturalitica ui
```

Opens a web interface at `http://localhost:8501`

### Dashboard Features

#### Tab 1: ✅ Technical Check
Validate technical aspects independently of organizational policy.
- **BOM Viewer**: Explore your system's inventory.
- **Green AI Tracking**: View carbon emissions, energy consumption, and training duration.

#### Tab 2: 🏛️ Governance & Risks
Highlight governance gaps and map technical metrics to regulatory requirements.
- **Risk Identification**: List compliance risks (Bias, Oversight, Data Governance).
- **Mitigation Gap Analysis**: Identify missing mitigation plans in your OSCAL policies.

#### Tab 3: 📄 Documentation
Generate EU AI Act Annex IV technical documentation drafts automatically.
- **System Elements**: Auto-populated list of libraries and models.
- **Risk Management System**: Overview of pre-training and post-training audits.

## CLI Best Practices

1. **Run `scan` before `ui`**: Generate the `bom.json` first so the dashboard has data to display.
2. **Integrate CodeCarbon**: Add emissions tracking to your training scripts to see Green AI metrics in the UI.
3. **CI/CD Integration**: Run `venturalitica scan` in your pipelines to detect dependency changes early.
