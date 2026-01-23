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

- **[00: Quickstart](https://github.com/Venturalitica/venturalitica-sdk/blob/main/notebooks/00-quickstart.ipynb)** - Fast one-liner audit on the German Credit dataset.
- **[01: Training Workflow](https://github.com/Venturalitica/venturalitica-sdk/blob/main/notebooks/01-training-tutorial.ipynb)** - Learn how to audit data before training and verify models post-training.

---

## ⚙️ Installation

```bash
pip install venturalitica
```

---

[Quickstart Guide](quickstart.md) | [API Reference](api.md) | [GitHub](https://github.com/Venturalitica/venturalitica-sdk)

© 2026 Venturalitica | Built for Responsible AI
