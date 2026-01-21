# Core Concepts: The "Handshake" Architecture

**Goal**: Understand how the SDK decouples policies from training code.

> 🔒 **Bruce Schneier (Security)**: "The Handshake is a Policy Firewall. Trust but cryptographically verify."
>
> 📐 **Martin Fowler (Architecture)**: "Loose coupling between the Dev's repo and the C.O.'s policy allows both to evolve."

---

## The Problem: Tight Coupling

**Traditional Approach** (❌ Bad):

```python
# Training script (tightly coupled to policy)
if df['sex_col'].value_counts()['M'] / len(df) > 0.6:
    raise ValueError("Gender imbalance detected!")
```

**Problems:**
1. Policy logic is **hardcoded** in training script
2. Changing thresholds requires **code changes**
3. No **audit trail** of what was checked
4. **Not reusable** across projects

---

## The Solution: Role-Based Binding

**Venturalitica Approach** (✅ Good):

### Three-Tier Mapping

```
Functional Roles → Semantic Variables → Physical Columns
     (Metrics)         (Policy)           (DataFrame)
        ↓                 ↓                    ↓
   "dimension"        "gender"            "sex_col"
   "target"           "target"            "approved"
   "prediction"       "prediction"        <model output>
```

### How It Works

**1. Training Script** (defines physical columns):
```python
enforce(
    data=df,
    target='approved',      # Physical column
    prediction=predictions,
    gender='sex_col'        # Physical column
)
```

**2. Policy** (defines semantic variables):
```yaml
- control-id: fair-gender
  props:
    - name: "input:dimension"
      value: gender  # Semantic variable
```

**3. SDK** (maps roles to metrics):
```python
# Internally, the SDK does:
demographic_parity_diff(
    dimension=df['sex_col'],  # Role → Variable → Column
    target=df['approved'],
    prediction=predictions
)
```

---

## Why This Matters

### 1. **Policies Evolve Independently**

Change the threshold without touching code:

```yaml
# Before
- name: threshold
  value: "0.10"

# After (stricter)
- name: threshold
  value: "0.05"
```

**No code changes needed.**

### 2. **Reusable Across Projects**

Same policy, different datasets:

**Project A:**
```python
enforce(data=df_loans, gender='sex', policy='fairness.oscal.yaml')
```

**Project B:**
```python
enforce(data=df_hiring, gender='gender_col', policy='fairness.oscal.yaml')
```

**Same policy, different column names.**

### 3. **Clear Audit Trail**

```
[Binding] Virtual Role 'dimension' bound to Variable 'gender' (Column: 'sex_col')
```

An auditor can trace:
- Which **policy** was enforced
- Which **semantic variable** was used
- Which **physical column** was evaluated

---

## The "Handshake" Moment

> 📈 **Elena Verna (PLG)**: "Time-to-Handshake < 1 hour"

The **Handshake** is when a developer realizes:
1. ✅ The SDK is **frictionless** (5-minute quickstart)
2. ❌ Writing OSCAL policies is **painful** (500+ lines of YAML)
3. 💡 The SaaS is the **easy button**

**This is by design.**

### Free SDK (Pain-Driven Adoption)

```yaml
# You have to write this manually:
assessment-plan:
  uuid: complex-policy-id
  metadata:
    title: "Complex Multi-Attribute Policy"
    version: "1.0.0"
  reviewed-controls:
    control-selections:
      - include-controls:
        - control-id: control-1
          description: "Long description..."
          props:
            - name: metric_key
              value: demographic_parity_diff
            # ... 50 more lines ...
```

**Pain Point**: Manual YAML editing is error-prone and tedious.

### SaaS (Easy Button)

- Visual policy builder
- Pre-made templates (EU AI Act, ISO 42001)
- Team collaboration
- Version control

**Conversion**: Free SDK → Paid SaaS

---

## Educational Audit Logs

> 🎨 **Jakob Nielsen (UX)**: "The UI is the translator. Translate 'Bias > 0.1' into 'High Regulatory Risk'."

### Before (Cryptic):
```
demographic_parity_diff = 0.12 > 0.10 FAIL
```

### After (Educational):
```
Evaluating Control 'credit-fair-1': Fairness Audit: Demographic Parity 
Difference must be under 10%, ensuring gender-neutral model predictions 
regardless of historical bias.
  ❌ FAIL: demographic_parity_diff = 0.12 > 0.10
```

**Why This Matters:**
- Developers **learn** why metrics matter
- Compliance officers **understand** technical checks
- Auditors **verify** regulatory alignment

---

## Semantic Variables vs Physical Columns

### Semantic Variables (Policy Layer)

**Purpose**: Abstract, domain-agnostic names

**Examples**:
- `gender` (not `sex_col` or `gender_field`)
- `age_group` (not `age_cat` or `age_bin`)
- `income` (not `salary` or `annual_income`)

**Why**: Policies should be reusable across datasets

### Physical Columns (Data Layer)

**Purpose**: Actual column names in your DataFrame

**Examples**:
- `sex_col` (your specific naming convention)
- `age_cat` (your binning strategy)
- `annual_salary` (your data schema)

**Why**: Data schemas vary by project

### The Binding

```python
enforce(
    data=df,
    gender='sex_col',      # Bind semantic 'gender' to physical 'sex_col'
    age='age_cat',         # Bind semantic 'age' to physical 'age_cat'
    income='annual_salary' # Bind semantic 'income' to physical 'annual_salary'
)
```

---

## Functional Roles

Metrics expect specific **functional roles**:

| Role | Purpose | Example |
|------|---------|---------|
| `target` | Ground truth labels | `df['approved']` |
| `prediction` | Model predictions | `model.predict(X)` |
| `dimension` | Protected attribute for fairness | `df['gender']` |

**Why Roles?**
- Metrics are **generic** (work with any dataset)
- Policies are **semantic** (domain-specific)
- Training scripts are **physical** (actual column names)

**Roles bridge the gap.**

---

## Pre-training vs Post-training

### Pre-training (Data Quality)

**No predictions yet**, so only check data:

```python
enforce(
    data=df_train,
    target='approved',
    gender='gender',
    policy='data-quality.oscal.yaml'  # Only uses 'target' and 'dimension'
)
```

**Metrics**:
- Class Imbalance
- Disparate Impact (in historical data)

### Post-training (Model Fairness)

**Predictions available**, so check model:

```python
enforce(
    data=df_test,
    target='approved',
    prediction=predictions,  # ← Now available
    gender='gender',
    policy='fairness.oscal.yaml'  # Uses 'target', 'prediction', 'dimension'
)
```

**Metrics**:
- Demographic Parity Difference
- Equal Opportunity Difference
- Accuracy, Precision, Recall

---

## Multi-Attribute Governance

Monitor **multiple** protected attributes:

```python
enforce(
    data=df,
    target='approved',
    prediction=predictions,
    gender='sex_col',    # First dimension
    age='age_group',     # Second dimension
    race='ethnicity'     # Third dimension
)
```

**Policy** (checks all dimensions):
```yaml
- control-id: fair-gender
  props:
    - name: "input:dimension"
      value: gender

- control-id: fair-age
  props:
    - name: "input:dimension"
      value: age

- control-id: fair-race
  props:
    - name: "input:dimension"
      value: race
```

---

## Robustness: Missing Columns

The SDK **gracefully handles** missing data:

```python
# Pre-training: no 'prediction' column
enforce(
    data=df_train,
    target='approved',
    gender='gender',
    policy='full-policy.oscal.yaml'  # Has both data + model checks
)
```

**Result**:
- ✅ Data quality checks **run**
- ⏭️ Model fairness checks **skipped** (no prediction)
- ℹ️ Log: "Skipping control 'fair-1': missing 'prediction'"

**No errors. No crashes.**

---

## Architecture Diagram

```
┌─────────────────┐
│ Training Script │  (Physical Layer)
│   df['sex_col'] │
└────────┬────────┘
         │ enforce(gender='sex_col')
         ↓
┌─────────────────┐
│   OSCAL Policy  │  (Semantic Layer)
│ input:dimension │
│   value: gender │
└────────┬────────┘
         │ SDK resolves binding
         ↓
┌─────────────────┐
│ Metric Function │  (Functional Layer)
│ calc_dem_parity │
│  (dimension=...) │
└─────────────────┘
```

---

## Next Steps

- **[Quickstart](quickstart.md)** - See binding in action
- **[OSCAL Authoring](oscal-authoring.md)** - Write your own policies
- **[Advanced Features](advanced.md)** - Programmatic binding

---

## 💡 Committee Insights

### 📐 Martin Fowler (Architecture)
> "This is textbook Separation of Concerns. The policy layer is completely decoupled from the execution layer."

### 🔒 Bruce Schneier (Security)
> "The binding creates a cryptographic-like audit trail. You can verify exactly what was checked, when, and how."

### 🎨 Jakob Nielsen (UX)
> "The educational logs are the 'translation layer' between dev and legal. Brilliant."
