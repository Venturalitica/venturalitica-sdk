# Multi-class and Causal Fairness Metrics Guide

This guide covers the new fairness metrics for multi-class classification and causal fairness analysis.

## Quick Start

### Multi-class Classification Fairness

```python
from venturalitica.metrics.multiclass import calc_multiclass_fairness_report
import pandas as pd

# Your data (3+ classes)
y_true = pd.Series([0, 1, 2, 0, 1, 2, ...])  # 3-class labels
y_pred = pd.Series([0, 1, 1, 0, 2, 2, ...])  # Predictions
protected_attr = pd.Series(['A', 'B', 'A', 'B', ...])  # Gender, race, etc.

# Get comprehensive report
report = calc_multiclass_fairness_report(y_true, y_pred, protected_attr)

print(f"Demographic Parity (Macro): {report['weighted_demographic_parity_macro']:.4f}")
print(f"Equal Opportunity (Macro):  {report['macro_equal_opportunity']:.4f}")
print(f"Predictive Parity (Macro):  {report['predictive_parity_macro']:.4f}")

# Fair if all metrics <= 0.1
```

### Causal Fairness Analysis

```python
from venturalitica.metrics.causal import calc_causal_fairness_diagnostic
import pandas as pd

# Your data
df = pd.DataFrame({
    'gender': ['M', 'F', 'M', ...],
    'education': [1, 4, 3, ...],
    'experience': [5, 10, 2, ...],
    'income': [0, 1, 0, ...],
})

# Analyze: How much is the protected attribute effect direct vs mediated?
diagnostic = calc_causal_fairness_diagnostic(
    df, 'gender', 'income',
    mediators=['education', 'experience']  # Legitimate explanations
)

print(diagnostic['causal_fairness_verdict'])
# Output: "✓ Causal fairness appears reasonable" or "⚠️ High direct effect..."
```

---

## Multi-class Metrics in Detail

### 1. Weighted Demographic Parity (Multi-class)

**What it measures:** Equal prediction rates across groups for each class.

**Formula:** For each class c:
```
DP_c = max(P(Ŷ=c|A=a)) - min(P(Ŷ=c|A=a)) across groups a
Result = max(DP_c) across all classes
```

**Strategies:**
- `'macro'`: Average disparity across all class pairs (recommended for balanced)
- `'weighted'`: Weight by class frequency (for imbalanced data)
- `'micro'`: Aggregate outcomes first
- `'one-vs-rest'`: Each class vs rest aggregation

**Threshold:** ≤ 0.1 (10% disparity)

**Example:**
```python
from venturalitica.metrics.multiclass import calc_weighted_demographic_parity_multiclass

disparity = calc_weighted_demographic_parity_multiclass(
    y_true, y_pred, protected_attr,
    strategy='weighted'  # Use weighted for imbalanced
)

if disparity <= 0.1:
    print("✓ Demographic parity achieved")
else:
    print(f"⚠️ High disparity: {disparity:.4f}")
```

---

### 2. Macro-averaged Equal Opportunity

**What it measures:** Equal True Positive Rates (recall) across groups for each class.

**Formula:** For each class c treated as one-vs-rest:
```
TPR_c(a) = TP_c(a) / P_c(a)  [recall for class c in group a]
EO_c = max(TPR_c) - min(TPR_c) across groups
Result = max(EO_c) across all classes
```

**When to use:** 
- Loan approvals (fairness in positive decisions)
- Hiring (equal callback rates by group)
- Medical diagnosis (equal sensitivity by demographic)

**Threshold:** ≤ 0.1 (equal TPR within 10%)

**Example:**
```python
from venturalitica.metrics.multiclass import calc_macro_equal_opportunity_multiclass

eo = calc_macro_equal_opportunity_multiclass(y_true, y_pred, protected_attr)

if eo <= 0.1:
    print("✓ Equal opportunity across groups")
else:
    print(f"⚠️ Unequal opportunity: {eo:.4f}")
```

---

### 3. Micro-averaged Equalized Odds

**What it measures:** Equal accuracy (both TPR and FPR) across groups.

**Formula:**
```
Micro-EO = |TPR_a - TPR_b| + |FPR_a - FPR_b|
```

**When to use:**
- Criminal justice (equal accuracy across demographics)
- Medical diagnosis (minimize both false positives and false negatives)
- Content moderation (equal error rates)

**Threshold:** ≤ 0.15 (combined TPR+FPR parity)

**Example:**
```python
from venturalitica.metrics.multiclass import calc_micro_equalized_odds_multiclass

eo = calc_micro_equalized_odds_multiclass(y_true, y_pred, protected_attr)

if eo <= 0.15:
    print("✓ Equalized odds achieved")
else:
    print(f"⚠️ Unequal odds: {eo:.4f}")
```

---

### 4. Predictive Parity (Multi-class)

**What it measures:** Equal precision (positive predictive value) across groups.

**Formula:** For each class c:
```
Precision_c(a) = TP_c / (TP_c + FP_c) [accuracy of positive predictions]
PP_c = max(Precision_c) - min(Precision_c) across groups
Result = max(PP_c) or weighted avg across classes
```

**When to use:**
- Hiring (equal reliability of positive recommendations)
- Loan approvals (equally reliable approval decisions)
- Content recommendation (equally reliable recommendations)

**Threshold:** ≤ 0.1 (equal precision within 10%)

**Example:**
```python
from venturalitica.metrics.multiclass import calc_predictive_parity_multiclass

pp = calc_predictive_parity_multiclass(
    y_true, y_pred, protected_attr,
    strategy='weighted'  # Weight by prediction frequency
)

if pp <= 0.1:
    print("✓ Predictive parity achieved")
else:
    print(f"⚠️ Precision disparity: {pp:.4f}")
```

---

## Causal Fairness Metrics

### 1. Path Decomposition (Direct vs Indirect Effects)

**What it measures:** How much of the protected attribute's effect is direct (discriminatory) vs indirect (through mediators).

**Decomposition:**
```
Total Effect = Direct Effect + Indirect Effect
- Direct Effect: Protected attr → Outcome (discriminatory)
- Indirect Effect: Protected attr → Mediators → Outcome (legitimate)
```

**Example with Hiring:**
```
Total salary gap = Direct discrimination + Mediated through experience/education
```

**Code:**
```python
from venturalitica.metrics.causal import calc_path_decomposition

effects = calc_path_decomposition(
    df, 'gender', 'salary',
    mediators=['education', 'years_experience', 'job_level']
)

for comparison, effect in effects.items():
    print(f"{comparison}:")
    print(f"  Total:       ${effect.total_effect:,.0f}")
    print(f"  Direct:      ${effect.direct_effect:,.0f} ({effect.proportion_mediated:.1%} mediated)")
    print(f"  Indirect:    ${effect.indirect_effect:,.0f}")
    
    if effect.direct_effect > 5000:  # $5k threshold
        print("  ⚠️ Significant direct discrimination detected")
```

**Interpretation:**
- **Low direct effect + high indirect effect** = ✓ Fair (differences explained by mediators)
- **High direct effect** = ⚠️ Potential discrimination
- **High proportion_mediated** = More differences explained legitimately

---

### 2. Counterfactual Fairness

**What it measures:** Would the decision change if the protected attribute was different?

**Concept:**
```
Counterfactually fair if: P(Ŷ=y|A=a, X) = P(Ŷ=y|A=a', X)
Where X is all causal ancestors of A
```

**Example:**
- Person A (female) is approved for loan
- If that same person was counterfactually male (same qualifications), would they be approved?
- If yes for most people: ✓ Counterfactually fair

**Code:**
```python
from venturalitica.metrics.causal import calc_counterfactual_fairness

unfairness = calc_counterfactual_fairness(df, 'gender', 'loan_approved')

print(f"Counterfactual unfairness: {unfairness:.4f}")

if unfairness <= 0.1:
    print("✓ Counterfactually fair (decisions robust to protected attribute)")
elif unfairness <= 0.2:
    print("⚠️ Moderate counterfactual disparities")
else:
    print("❌ Severe counterfactual unfairness")
```

**Thresholds:**
- ≤ 0.05: Excellent (counterfactual fairness achieved)
- 0.05-0.15: Good (minor counterfactual disparities)
- 0.15-0.30: Fair (noticeable disparities)
- > 0.30: Poor (decisions heavily influenced by protected attribute)

---

### 3. Fairness Through Awareness

**What it measures:** Can we make fair decisions using only "relevant" features without leaking protected information?

**Key insight:** Even if we don't explicitly use gender, if we use a feature that's highly correlated with gender, we're still discriminating.

**Metrics:**
- `information_leakage_score`: Average correlation between relevant features and protected attribute
- `legitimate_predictor_power`: How much relevant features predict the outcome

**Code:**
```python
from venturalitica.metrics.causal import calc_fairness_through_awareness

awareness = calc_fairness_through_awareness(
    df, 'gender', 'salary',
    relevant_features=['education', 'experience', 'test_score']
)

print(f"Information Leakage: {awareness['information_leakage_score']:.4f}")
for feat, power in awareness['legitimate_predictor_power'].items():
    print(f"  {feat} → salary correlation: {power:.4f}")

if awareness['information_leakage_score'] <= 0.2:
    print("✓ Features don't leak protected info")
else:
    print("⚠️ Features correlated with protected attribute")
    # Consider: Are the relevant features legitimate or proxies for gender?
```

**Thresholds:**
- ≤ 0.1: Excellent (minimal leakage)
- 0.1-0.25: Good (some correlation)
- 0.25-0.40: Fair (noticeable proxies)
- > 0.40: Poor (strong correlation with protected attribute)

---

### 4. Comprehensive Causal Fairness Diagnostic

**One-stop diagnostic combining all causal fairness checks:**

```python
from venturalitica.metrics.causal import calc_causal_fairness_diagnostic

diagnostic = calc_causal_fairness_diagnostic(
    df, 'protected_attr', 'outcome',
    mediators=['legitimate_feature_1', 'legitimate_feature_2']
)

# Inspection
print(f"Sample Size: {diagnostic['sample_size']}")
print(f"Verdict: {diagnostic['causal_fairness_verdict']}")

# Detailed analysis
for comparison, effect in diagnostic['path_decomposition'].items():
    print(f"\n{comparison}:")
    print(f"  Direct Effect: {effect.direct_effect:.4f}")
    print(f"  Mediation: {effect.proportion_mediated:.1%}")

print(f"\nCounterfactual Unfairness: {diagnostic['counterfactual_fairness']:.4f}")
print(f"Information Leakage: {diagnostic['fairness_through_awareness']['information_leakage_score']:.4f}")
```

---

## Complete Example: Hiring Fairness Audit

```python
import pandas as pd
from venturalitica.metrics import METRIC_REGISTRY

# Load hiring data
df = pd.read_csv('hiring_data.csv')

# 1. Check multi-class fairness across job levels
from venturalitica.metrics.multiclass import calc_multiclass_fairness_report

report = calc_multiclass_fairness_report(
    df['job_level'], df['predicted_level'], df['gender']
)

print("Multi-class Fairness Report:")
for metric, value in report.items():
    status = "✓" if value <= 0.1 else "⚠️"
    print(f"  {status} {metric}: {value:.4f}")

# 2. Understand root causes (causal analysis)
from venturalitica.metrics.causal import calc_causal_fairness_diagnostic

diagnostic = calc_causal_fairness_diagnostic(
    df, 'gender', 'hired',
    mediators=['education_years', 'years_experience', 'test_score']
)

print(f"\n{diagnostic['causal_fairness_verdict']}")

# 3. Examine path decomposition
for comp, effect in diagnostic['path_decomposition'].items():
    print(f"\n{comp}:")
    print(f"  Direct discrimination: {effect.direct_effect:.1%}")
    print(f"  Explained by mediators: {effect.proportion_mediated:.1%}")
```

---

## Integration with Existing Metrics

All new metrics are registered in `METRIC_REGISTRY`:

```python
from venturalitica.metrics import METRIC_REGISTRY, METRIC_METADATA

# List all available metrics
for metric_name, function in METRIC_REGISTRY.items():
    if 'multiclass' in metric_name or 'causal' in metric_name:
        meta = METRIC_METADATA.get(metric_name, {})
        print(f"{metric_name}: {meta.get('description', 'N/A')}")
```

---

## Troubleshooting

### "Minimum 30 samples required"
**Solution:** Need at least 30 data points for reliable statistical estimates.

### "Need at least 2 classes/groups"
**Solution:** 
- For multi-class: Ensure 3+ prediction classes
- For groups: Need both protected and non-protected groups (e.g., M/F, Young/Old)

### High metrics but valid predictions
**Interpretation:** Metrics might be high because:
1. Legitimate mediators differ between groups (not captured in `mediators` parameter)
2. Historical bias in the data training set
3. Need better feature engineering

**Action:** Add more mediators to path decomposition or consult domain expert.

### All metrics pass, but qualitative audit fails
**Insight:** Metrics capture statistical fairness, but miss contextual fairness.
- Engage stakeholders
- Review failed edge cases manually
- Consider additional fairness notions (individual fairness, etc.)

---

## References

### Multi-class Fairness
- Hardt, M., Price, E., & Srebro, N. (2016). "Equality of Opportunity in Supervised Learning." arXiv:1610.02413
- Buolamwini, B., & Gebru, T. (2018). "Gender Shades." Conference on Fairness, Accountability and Transparency.

### Causal Fairness
- Pearl, J. (2009). "Causality: Models, Reasoning, and Inference." Cambridge University Press.
- Kusner, M. J., Loftus, J., Russell, C., & Silva, R. (2017). "Counterfactual Fairness." arXiv:1705.08857
- Moritz, P., et al. (2015). "Fairness Through Awareness." Conference on Fairness, Accountability and Transparency.
- VanderWeele, T. J. (2013). "A three-way decomposition of effects in the presence of a three-way interaction."

---

## Quick Reference Table

| Metric | Classes | Use Case | Threshold | Reference |
|--------|---------|----------|-----------|-----------|
| Weighted DP | 3+ | Equal positive rates | ≤ 0.10 | Fairlearn |
| Macro EO | 3+ | Equal TPR (recall) | ≤ 0.10 | Hardt et al. 2016 |
| Micro Odds | 3+ | Equal accuracy | ≤ 0.15 | Hardt et al. 2016 |
| Predictive Parity | 3+ | Equal precision | ≤ 0.10 | Fairlearn |
| Path Decomposition | Binary | Direct vs mediated | Low direct | Pearl 2009 |
| Counterfactual | Binary | Robustness to attribute | ≤ 0.10 | Kusner et al. 2017 |
| Fairness Awareness | Binary | No leakage | ≤ 0.20 | Moritz et al. 2015 |

---

For questions or issues, please refer to the SDK documentation or contact the fairness team.
