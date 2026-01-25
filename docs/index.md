# Venturalitica

**Frictionless Governance for AI.**

Venturalitica is a lightweight Python SDK designed to enforce policies, audit fairness, and track environmental impact in your ML workflows with zero friction.

---

## ⚡️ Quickstart in 60 Seconds

Detect bias in your datasets or models with one line of code.

```python
import venturalitica as vl

# Auto-download UCI data, load policy, and run bias audit
results = vl.quickstart('loan')
```

---

## 🛡 Key Features

| Feature | Description |
| :--- | :--- |
| **Bias Detection** | Quantitative fairness audits (Disparate Impact, Class Balance). |
| **Integrity Checks** | Immutable audit trails and model fingerprints. |
| **Green AI** | Native carbon emission and energy consumption tracking. |
| **Policy as Code** | Define governance rules in standard OSCAL/YAML formats. |
| **Framework Agnostic** | Works with Scikit-learn, PyTorch, TensorFlow, and more. |

---

## 📚 Explore Tutorials

Start with our interactive Jupyter notebooks:

- **[⚡️ Zero-Setup Audit](tutorials/local-audit.md)** - Run a full compliance scan on any project folder in 2 minutes.
- **[🛠️ Training Workflow](training.md)** - Learn how to audit data before training and verify models post-training.
- **[📊 Regulatory Mapping](compliance-dashboard.md)** - Deep dive into how Venturalitica maps technical evidence to the EU AI Act.

---

## ⚙️ Installation

```bash
pip install venturalitica
```

---

[Quickstart Guide](quickstart.md) | [Local Audit Tutorial](tutorials/local-audit.md) | [Regulatory Map](compliance-dashboard.md) | [API Reference](api.md)

© 2026 Venturalitica | Built for Responsible AI
