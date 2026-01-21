# Venturalitica SDK Documentation

Welcome to the Venturalitica SDK documentation. This directory contains comprehensive guides for using the SDK to integrate AI governance into your ML workflows.

## 📚 Documentation Index

### [Tutorial](tutorial.md)
**Start here!** A comprehensive, step-by-step guide covering all SDK features:
- Installation and setup
- Core concepts (Role-based Binding, Educational Audits)
- Policy enforcement (basic to advanced)
- OSCAL policy authoring
- MLOps integrations (MLflow, WandB, ClearML)
- CLI tools (`scan`, `ui`)
- Advanced features and customization

### Quick Links

- **[SDK Repository](https://github.com/venturalitica/venturalitica-sdk)** - Source code and issues
- **[Samples Repository](https://github.com/venturalitica/venturalitica-sdk-samples)** - Real-world examples with datasets
- **[OSCAL Standard](https://pages.nist.gov/OSCAL/)** - Policy definition standard

## 🚀 Quick Start

```bash
# Install the SDK
pip install venturalitica-sdk

# Run a sample
git clone https://github.com/venturalitica/venturalitica-sdk-samples.git
cd venturalitica-sdk-samples/scenarios/loan-mlflow-sklearn
uv run python train.py
```

## 📖 Learning Path

1. **Beginners**: Start with the [Tutorial](tutorial.md) sections 1-3
2. **Intermediate**: Explore [Role-Based Binding](tutorial.md#role-based-binding) and [OSCAL Authoring](tutorial.md#oscal-policy-authoring)
3. **Advanced**: Dive into [MLOps Integrations](tutorial.md#mlops-integrations) and [Advanced Features](tutorial.md#advanced-features)

## 🎯 Use Cases

### Credit Scoring Fairness
Ensure loan approval models comply with fair lending regulations.
- **Sample**: `loan-mlflow-sklearn`
- **Policies**: Demographic Parity, Disparate Impact (80% Rule)
- **Regulations**: ECOA, Fair Credit Reporting Act

### Hiring Bias Detection
Detect and mitigate bias in recruitment models.
- **Sample**: `hiring-wandb-torch`
- **Policies**: Gender/Age fairness, Equal Opportunity
- **Regulations**: EEOC guidelines, EU AI Act

### Clinical Risk Assessment
Validate medical diagnosis models for fairness and accuracy.
- **Sample**: `health-clearml-sklearn`
- **Policies**: Sensitivity/Specificity, Clinical accuracy
- **Regulations**: HIPAA, MDR (Medical Device Regulation)

## 🛠️ SDK Features Overview

### Core Capabilities
- ✅ **OSCAL-native policy definitions** - Industry-standard compliance
- ✅ **Role-based semantic binding** - Decouple policies from code
- ✅ **Educational audit logs** - Explain *why* metrics matter
- ✅ **Pre/post-training audits** - Data quality + model fairness
- ✅ **Multi-attribute governance** - Monitor multiple protected attributes

### Integrations
- ✅ **MLflow** - Automatic metric/tag/artifact logging
- ✅ **Weights & Biases** - Compliance tracking in experiments
- ✅ **ClearML** - Healthcare/regulated industry MLOps
- ✅ **Streamlit Dashboard** - Local compliance UI

### CLI Tools
- ✅ **`venturalitica scan`** - Generate ML-BOM (CycloneDX)
- ✅ **`venturalitica ui`** - Launch compliance dashboard

## 📊 Supported Metrics

### Performance
- Accuracy, Precision, Recall, F1-Score

### Fairness
- Demographic Parity Difference
- Equal Opportunity Difference
- Disparate Impact (80% Rule)

### Data Quality
- Class Imbalance

## 🤝 Contributing

We welcome contributions! Areas of interest:
- New fairness metrics
- Additional MLOps integrations
- Policy templates for specific regulations
- Documentation improvements

## 📄 License

Apache 2.0 - See [LICENSE](../LICENSE) for details.
