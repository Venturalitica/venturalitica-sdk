---
title: "Tutorial"
date: 2026-01-18T00:00:00+01:00
draft: false
weight: 2
---

# Tutorial: From Zero to Compliance 🚀

This guide takes you from a raw python script to a compliant AI project.

## Step 1: Install the SDK

We want to track our Carbon Footprint too, so let's install the `green` extra.

```bash
pip install "venturalitica-sdk[green]"
```

## Step 2: Implement Carbon Tracking

Wrap your training loop (or main function) with `codecarbon` (detected automatically by our UI).

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker()
tracker.start()

# Your ML Training here
model.fit(X, y)

tracker.stop() # Generates emissions.csv
```

## Step 3: Scan the Project

Scan your directory to inventory everything.

```bash
venturalitica scan .
```

You will see `[INFO] Generated bom.json with 24 components`.

## Step 4: Verify in Dashboard

Launch the UI:

```bash
venturalitica ui
```

Go to **Technical Check**. You should see:
1.  **BOM**: Your libraries and model (e.g., `RandomForestClassifier`).
2.  **Environment**: 🍃 **0.024 kgCO2**.

## Step 5: The "Gap"

Go to **Governance**. You will see **RED** flags.
*   "Missing Human Oversight"
*   "Missing Bias Assessment"

This is normal! To fix these Organization-level risks, you would typically push this Draft to the **Venturalitica SaaS** (Coming Later).
