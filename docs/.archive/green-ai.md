# Green AI Guide: Track Your Carbon Footprint

**Goal**: Measure and reduce the environmental impact of your ML training.

> 🌱 **Why This Matters**:
> - **EU AI Act Article 11**: Requires environmental impact documentation
> - **Stakeholder Transparency**: Show the carbon cost of your models
> - **Sustainability**: Optimize training for lower emissions

---

## What is Green AI?

**Green AI** is the practice of measuring and minimizing the carbon footprint of machine learning.

The Venturalitica SDK provides a **transparent tracking mechanism** called `Monitor` that collects Green AI metrics (emissions, energy) and performance metrics (duration) without cluttering your code.

---

## Step 1: Install CodeCarbon (30 seconds)

The SDK uses `codecarbon` under the hood:

```bash
pip install codecarbon
```

---

## Step 2: Use the Monitor (1 minute)

Add **one line** to your training script to start tracking:

```python
import venturalitica as vl
from sklearn.ensemble import RandomForestClassifier

# Wrap your training code in a monitor
with vl.monitor(name="Random Forest Training"):
    # Your existing training code
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
```

### What's happening?
The `vl.monitor` is a **Multimodal Observability** tool using a **Probe Architecture**:
1. 🟢 **CarbonProbe**: Starts the `codecarbon` tracker automatically.
2. 🟢 **HardwareProbe**: Captures Peak RAM and CPU usage.
3. 🟢 **IntegrityProbe**: Generates a **Security Fingerprint** of the environment (OS, Python version, CWD) to ensure audit trail integrity.
4. 🟢 **HandshakeProbe**: Nudges you if you haven't run a governance check (`vl.enforce`) yet.
5. 🔴 **Summarizes** all findings when the block finishes.

---

## Console Output

When the monitor finishes, you'll see a transparent summary:

```text
[Venturalitica] 🟢 Starting monitor: Random Forest Training

... (training occurs) ...

[Venturalitica] 🔴 Monitor stopped: Random Forest Training
  ⏱  Duration: 45.20s
  🛡 [Security] Fingerprint: 169140e3ffff | Integrity: ✅ Stable
  💻 [Hardware] Peak Memory: 293.94 MB | CPUs: 16
  🌱 [Green AI] Carbon emissions: 0.000012 kgCO₂
  🤝 [Handshake] Policy enforced verifyable audit trail present.
```

---

## Step 3: Visualize in the Dashboard

Launch the Venturalitica dashboard to see historical trends:

```bash
venturalitica ui
```

Navigate to **Tab 1: Technical Check** → **Green AI** section to see:
- CO₂ emissions (kgCO₂)
- Training duration
- Energy consumed (kWh)

---

## Step 4: Integrate with MLOps

`vl.monitor` automatically detects if you have an active MLflow, WandB, or ClearML run and logs the emissions data as a metric.

```python
import mlflow
import venturalitica as vl

with mlflow.start_run():
    with vl.monitor(name="Loan Model V1"):
        model.fit(X_train, y_train)
        
    # The monitor automatically logs 'carbon_emissions_kg' to MLflow
```

---

## EU AI Act Compliance

### Article 11: Technical Documentation

The EU AI Act requires documenting computational resources and energy consumption. 

**How Venturalitica helps:**
1. **Auto-Capture**: `vl.monitor` captures the data at the source.
2. **Auto-Inventory**: `venturalitica scan` detects training scripts and components.
3. **Annex IV Draft**: The dashboard (Tab 3: Documentation) automatically populates Section 4 (Environmental Impact) with the metrics collected by your monitors.

---

## Best Practices

1. **Monitor All Significant Runs**: Wrap any training or heavy data processing in a `vl.monitor`.
2. **Commit Emissions Assets**: Store the generated `emissions.csv` in your repository for reproducibility.
3. **Compare Versions**: Use the monitor to identify if newer model architectures are significantly more carbon-intensive for marginal accuracy gains.
