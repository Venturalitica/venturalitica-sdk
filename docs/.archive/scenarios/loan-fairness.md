# Loan Approval Fairness: A Complete Tutorial

## The Problem: Bias in Credit Scoring

### Real-World Context

In 2019, Apple Card (issued by Goldman Sachs) faced a major scandal when users discovered that the algorithm was offering women **significantly lower credit limits** than men, even when they had identical financial profiles. This wasn't intentional discrimination—it was **algorithmic bias** learned from historical data.

**The Cost:**
- Goldman Sachs investigated by New York regulators
- Reputational damage to Apple brand
- Potential violations of Equal Credit Opportunity Act (ECOA)

### Why This Happens

Credit scoring models are trained on historical loan data. If past lending decisions were biased (consciously or unconsciously), the model **learns and amplifies** that bias:

```
Historical Data (Biased) → ML Model → Biased Predictions
```

**Example Bias Patterns:**
1. **Gender Bias**: Women historically denied loans more often → Model learns "female = higher risk"
2. **Age Bias**: Young applicants denied more often → Model learns "age < 25 = reject"
3. **Proxy Discrimination**: Using "zip code" as a feature can be a proxy for race

---

## The Dataset: German Credit Data

We're using the **UCI German Credit Dataset** (1994), which contains:
- **1,000 loan applications**
- **20 features**: credit history, employment, age, gender, etc.
- **Target**: Loan approved (1) or rejected (0)

### The Hidden Bias

This dataset has **documented bias**:
- **Gender imbalance**: 69% male, 31% female applicants
- **Age discrimination**: Younger applicants rejected more often
- **Historical bias**: Reflects 1990s German banking practices

**Our Goal**: Build a fair credit scoring model that **doesn't perpetuate** these biases.

---

## The Regulatory Framework

### EU AI Act (High-Risk AI System)

Credit scoring is classified as a **High-Risk AI System** under EU AI Act Article 6:

> "AI systems intended to be used to evaluate the creditworthiness of natural persons or establish their credit score"

**Requirements (Articles 9-15):**
1. **Article 9**: Risk management system
2. **Article 10**: Data governance (quality, bias detection)
3. **Article 11**: Technical documentation (Annex IV)
4. **Article 12**: Record-keeping and traceability
5. **Article 13**: Transparency and information to users
6. **Article 14**: Human oversight
7. **Article 15**: Accuracy, robustness, cybersecurity

### Equal Credit Opportunity Act (ECOA) - US

**Prohibited Bases for Discrimination:**
- Race, color, religion, national origin
- Sex, marital status
- Age (with exceptions)

**The "80% Rule" (Disparate Impact):**
If the approval rate for a protected group is **< 80%** of the approval rate for the reference group, it's considered discriminatory.

```
Disparate Impact = (Minority Approval Rate) / (Majority Approval Rate)

If < 0.8 → Potential discrimination
```

### Risk Assessment Matrix

Before implementing controls, we perform a risk assessment to prioritize our governance efforts:

| Risk Scenario | Probability | Impact | Mitigation Strategy | regulatory Mapping |
| :--- | :--- | :--- | :--- | :--- |
| **Gender Bias** | High | Critical | Demographic Parity Audit | Art. 10 (Fairness) |
| **Age Discrimination** | Medium | High | Disparate Impact Check | ECOA / High-Risk |
| **Data Drift** | High | Medium | Continuous Monitoring | Art. 15 (Robustness) |
| **Hidden Context** | Medium | Critical | Explainability / Human Oversight | Art. 14 (Oversight) |
| **High Carbon Footprint** | Medium | Low | Green AI Tracking | Art. 11 (Tech Doc) |

---

## The Solution: Venturalítica SDK

### Step 1: Understand the Risks

We define **OSCAL policies** that map to regulatory requirements:

#### Risk 1: Class Imbalance (Data Quality)
**Policy**: `credit-data-imbalance`
**Requirement**: EU AI Act Article 10 (Data Governance)
**Check**: Minority class (rejected loans) must be ≥ 20% of dataset

**Why This Matters:**
If only 5% of your training data is "rejected loans," the model will be terrible at predicting rejections. It will just approve everyone.

```yaml
- control-id: credit-data-imbalance
  description: "Data Quality: Minority class (rejected loans) should represent at least 20% of the dataset to avoid biased training due to severe Class Imbalance."
  props:
    - name: metric_key
      value: class_imbalance
    - name: threshold
      value: "0.20"
    - name: operator
      value: ">="
```

#### Risk 2: Pre-training Gender Bias (Disparate Impact)
**Policy**: `credit-data-bias`
**Requirement**: ECOA (80% Rule)
**Check**: Disparate impact ratio for gender must be ≥ 0.8

**Why This Matters:**
If historical data shows women were approved at 60% the rate of men, your model will learn this bias.

```yaml
- control-id: credit-data-bias
  description: "Pre-training Fairness: Disparate impact ratio should follow the standard '80% Rule' (Four-Fifths Rule), ensuring favorable loan outcomes are representative across groups."
  props:
    - name: metric_key
      value: disparate_impact
    - name: threshold
      value: "0.80"
    - name: operator
      value: ">="
    - name: "input:dimension"
      value: gender
    - name: "input:target"
      value: target
```

#### Risk 3: Post-training Gender Fairness (Demographic Parity)
**Policy**: `credit-fair-1`
**Requirement**: EU AI Act Article 10 + ECOA
**Check**: Demographic parity difference for gender must be < 10%

**Why This Matters:**
Even if historical data was fair, your model might still make biased predictions. We check the **model's output**.

**Demographic Parity Difference:**
```
DPD = |P(approved | female) - P(approved | male)|

If > 0.10 → Model is biased
```

```yaml
- control-id: credit-fair-1
  description: "Fairness Audit: Demographic Parity Difference must be under 10%, ensuring gender-neutral model predictions regardless of historical bias."
  props:
    - name: metric_key
      value: demographic_parity_diff
    - name: threshold
      value: "0.10"
    - name: operator
      value: "<"
    - name: "input:dimension"
      value: gender
    - name: "input:target"
      value: target
    - name: "input:prediction"
      value: prediction
```

#### Risk 4: Age Discrimination
**Policy**: `credit-age-bias`
**Requirement**: ECOA (Age Discrimination)
**Check**: Demographic parity for age groups must be < 15%

**Why This Matters:**
Young people (< 25) are often denied loans more frequently. We check if the model perpetuates this.

```yaml
- control-id: credit-age-bias
  description: "Generational Bias Audit: Demographic parity for age groups must be under 15% to detect bias against younger or senior applicants."
  props:
    - name: metric_key
      value: demographic_parity_diff
    - name: threshold
      value: "0.15"
    - name: operator
      value: "<"
    - name: "input:dimension"
      value: age_group
    - name: "input:target"
      value: target
    - name: "input:prediction"
      value: prediction
```

#### Risk 5: Model Accuracy
**Policy**: `credit-acc-1`
**Requirement**: EU AI Act Article 15 (Accuracy)
**Check**: Recall for "good credit" classification must be ≥ 80%

**Why This Matters:**
A model that rejects all applicants is "fair" (0% bias) but useless. We need **both fairness AND accuracy**.

```yaml
- control-id: credit-acc-1
  description: "Minimum recall for 'good' credit classification"
  props:
    - name: metric_key
      value: recall
    - name: threshold
      value: "0.80"
    - name: operator
      value: ">="
```

---

## Step 2: Implement the Solution

### Training Script with Governance

```python
import pandas as pd
import venturalitica as vl
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Load data
df = pd.read_csv("german_credit.csv")
X = df.drop(columns=["target", "gender", "age"])
y = df["target"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# PRE-TRAINING AUDIT: Check data quality
df_train = pd.concat([X_train, y_train, df.loc[X_train.index, ["gender", "age"]]], axis=1)
vl.enforce(
    data=df_train,
    target="target",
    gender="gender",
    age="age",
    policy="risks.oscal.yaml"
)

# TRAINING: Track carbon emissions transparently
with vl.monitor(name="Loan Model Training"):
    model = RandomForestClassifier()
    model.fit(X_train, y_train)

# POST-TRAINING AUDIT: Check model fairness
df_test = pd.concat([X_test, y_test, df.loc[X_test.index, ["gender", "age"]]], axis=1)
df_test["prediction"] = model.predict(X_test)

vl.enforce(
    data=df_test,
    target="target",
    prediction="prediction",
    gender="gender",
    age="age",
    policy="risks.oscal.yaml"
)
```

---

## Step 3: Interpret the Results

### Example Output

```
[Venturalítica] 🛡️ Checking Training Data for Bias (Gender & Age)...

Evaluating Control 'credit-data-imbalance': Data Quality: Minority class (rejected loans) should represent at least 20%...
  ✓ PASS: class_imbalance = 0.43 >= 0.20

Evaluating Control 'credit-data-bias': Pre-training Fairness: Disparate impact ratio should follow the '80% Rule'...
  ✓ PASS: disparate_impact = 1.00 >= 0.80

[Venturalítica] 🟢 Starting monitor: Loan Model Training
... (training) ...
[Venturalítica] 🔴 Monitor stopped: Loan Model Training
  ⏱  Duration: 1.2s
  🌱 [Green AI] Carbon emissions: 0.000001 kgCO₂

[Venturalítica] 🛡️ Checking Model Compliance (Gender & Age)...

Evaluating Control 'credit-fair-1': Fairness Audit: Demographic Parity Difference must be under 10%...
  ✓ PASS: demographic_parity_diff = 0.00 < 0.10

Evaluating Control 'credit-age-bias': Generational Bias Audit: Demographic parity for age groups must be under 15%...
  ✓ PASS: demographic_parity_diff = 0.12 < 0.15

Evaluating Control 'credit-acc-1': Minimum recall for 'good' credit classification...
  ❌ FAIL: recall = 0.74 < 0.80
```

### What This Tells Us

1. ✅ **Data Quality is Good**: 43% of loans are rejected (well above 20% threshold)
2. ✅ **No Pre-training Gender Bias**: Historical data shows no disparate impact
3. ✅ **Model is Fair (Gender)**: 0% demographic parity difference
4. ✅ **Model is Fair (Age)**: 12% demographic parity difference (under 15% limit)
5. ❌ **Model Accuracy Needs Improvement**: Only 74% recall (need 80%)

**Action**: We need to improve model accuracy without sacrificing fairness.

---

## Step 4: Fix the Issues

### Option 1: Hyperparameter Tuning

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'n_estimators': [100, 200, 500],
    'max_depth': [10, 20, None],
    'min_samples_split': [2, 5, 10]
}

grid_search = GridSearchCV(RandomForestClassifier(), param_grid, cv=5, scoring='recall')
grid_search.fit(X_train, y_train)

model = grid_search.best_estimator_
```

### Option 2: Feature Engineering

```python
# Add interaction features
df['credit_amount_per_duration'] = df['credit_amount'] / df['duration']
df['age_employment_ratio'] = df['age'] / (df['employment_duration'] + 1)
```

### Option 3: Fairness-Aware Training

```python
from fairlearn.reductions import ExponentiatedGradient, DemographicParity

constraint = DemographicParity()
mitigator = ExponentiatedGradient(RandomForestClassifier(), constraint)
mitigator.fit(X_train, y_train, sensitive_features=df_train['gender'])
```

---

## Step 5: Document for Compliance

### EU AI Act Annex IV Requirements

The SDK helps you generate the required documentation:

```bash
venturalitica scan  # Generate ML-BOM
venturalitica ui    # Launch dashboard
```

**Dashboard Tab 3: Documentation** will auto-generate:

```markdown
# EU AI Act Annex IV Technical Documentation

## 2. System Elements
- scikit-learn (1.3.0): library
- RandomForestClassifier: machine-learning-model
- mlflow (2.9.0): library

## 3. Risk Management System
- Pre-training data quality checks: PASSED
- Post-training fairness audits: PASSED (5/6 controls)
- Identified risk: Model accuracy below threshold

## 4. Environmental Impact
- Carbon Emissions: 0.000001 kgCO₂
- Energy Consumed: 0.000003 kWh
- Training Duration: 1.2 seconds
```

---

## Key Takeaways

1. **Bias is Learned**: Models learn from historical data, including historical biases
2. **Pre-training Audits**: Check data quality BEFORE training
3. **Post-training Audits**: Check model fairness AFTER training
4. **Fairness ≠ Accuracy**: You need both
5. **Green AI**: Track environmental impact for EU AI Act Article 11
6. **Documentation**: Auto-generate compliance artifacts

---

## Next Steps

1. **Run the sample**: `cd scenarios/loan-mlflow-sklearn && uv run python train.py`
2. **Experiment**: Modify the model and see how metrics change
3. **Create custom policies**: Write your own OSCAL controls
4. **Integrate with MLOps**: Use `--framework mlflow` to log to MLflow

---

## Resources

- **[EU AI Act Full Text](https://artificialintelligenceact.eu/)**
- **[ECOA Guidelines](https://www.consumerfinance.gov/rules-policy/regulations/1002/)**
- **[Fairlearn Documentation](https://fairlearn.org/)**
- **[German Credit Dataset](https://archive.ics.uci.edu/ml/datasets/statlog+(german+credit+data))**
