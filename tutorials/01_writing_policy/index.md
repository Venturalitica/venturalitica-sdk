# 🛠️ Writing Code-First Policy (The Engineer)

This guide focuses on the **Engineer Persona**: the one who translates legal requirements into technical rules (OSCAL). In **Level 1**, you learned to "Block" bad deployments. Now we will write the actual policy file that governs the project.

______________________________________________________________________

## The Policy File (`data_policy.yaml`)

For **Phase 1 (Data Audit)**, we only care about **Article 10 (Data Governance)**. Your Data Scientist (The Builder) cannot start training until this file is ready.

### 1. The Structure

Create a file named `data_policy.yaml` in your project root.

```
assessment-plan:
  uuid: credit-scoring-v1
  metadata:
    title: "Article 10: Consumer Credit Directive (CCD)"
    description: "Acceptance criteria for training data quality and bias."
  reviewed-controls:
    control-selections:
      - include-controls:
        # RULES GO HERE
```

______________________________________________________________________

## 2. Defining the Rules (Controls)

A "Control" is a unit of logic. In the EU AI Act, you must prove you checked for specific risks.

### Rule A: Representation (Statistical Support)

- **Legal Requirement**: "Training, validation and testing data sets shall be relevant, representative, free of errors and complete." (Art 10.3)
- **Translation**: Ensure no demographic group is erased (Min 20% representation).

```
        - control-id: check-imbalance
          description: "Ensure minority groups are statistically significant."
          props:
            - name: metric_key
              value: min_class_ratio
            - name: threshold
              value: "0.20"  # Fail if minority class < 20%
            - name: operator
              value: ">"
```

### Rule B: Bias (Disparate Impact)

- **Legal Requirement**: "Examination of possible biases." (Art 10.2.f)
- **Translation**: Acceptance rates must not deviate by more than 20% between groups (Four-Fifths Rule).

```
        - control-id: check-gender-bias
          description: "Disparate Impact Ratio must be within 0.8 - 1.25"
          props:
            - name: metric_key
              value: disparate_impact_ratio
            - name: threshold
              value: "0.80"
            - name: operator
              value: ">"
```

______________________________________________________________________

## 3. Verify the Policy

Before handing it off to the Data Scientist, verify it works.

```
import venturalitica as vl
from venturalitica.quickstart import load_sample

# 1. Load the 'Approved' Dataset (Mock)
data = load_sample('loan')

# 2. Dry Run the Policy
try:
    vl.enforce(
        data=data,
        target="class",
        gender="Attribute9",  # "Personal status and sex" in German Credit Data
        policy="data_policy.yaml"
    )
    print("✅ Policy is valid syntax and passes baseline data.")
except Exception as e:
    print(f"❌ Policy Error: {e}")
```

______________________________________________________________________

## Part 2: The Model Policy (`model_policy.yaml`)

Once the data is approved, you need to define the rules for the **final product** (the trained model). This corresponds to **Article 15 (Accuracy, Robustness, and Cybersecurity)**.

Create a second file: `model_policy.yaml`.

### Rule C: Performance (Accuracy)

- **Legal Requirement**: "High-risk AI systems shall be designed ... to achieve an appropriate level of accuracy." (Art 15.1)
- **Translation**: The model must be better than random guessing (e.g., > 70% accuracy).

```
        - control-id: accuracy-check
          description: "Model must achieve at least 70% accuracy."
          props:
            - name: metric_key
              value: accuracy_score
            - name: threshold
              value: "0.70"
            - name: operator
              value: ">"
```

### Rule D: Post-Training Fairness (Outcome)

- **Legal Requirement**: "Results shall not be biased..."
- **Translation**: Even if data was balanced, the model might still learn to discriminate. Check the predictions again.

```
        - control-id: gender-fairness-model
          description: "Ensure model predictions do not disparately impact women."
          props:
            - name: metric_key
              value: disparate_impact_ratio
            - name: "input:dimension"
              value: "gender"         # Explicitly link to the gender column
            - name: threshold
              value: "0.80"
            - name: operator
              value: ">"
```

______________________________________________________________________

## What's Next?

You have now created the **specification**. 👉 Hand these files (`data_policy.yaml` and `model_policy.yaml`) to your Data Scientist. They will use them in **Level 2** to audit their training pipeline.
