# Venturalítica SDK v1.1 - Enhanced Fairness & Privacy Framework

## 📋 Overview

Version 1.1 introduces **alternative fairness metrics**, **privacy-preserving measures**, and **semantic interpretation** of governance results. This is the result of comprehensive auditing and refinement of the fairness evaluation framework.

**Key Achievement:** Eliminated silent metric failures (0.000/1.000 perfect values) and replaced them with strict validation and meaningful error messages.

---

## 🎯 What's New

### 1. **Equalized Odds** - Beyond Demographic Parity
- **Metric:** `equalized_odds_ratio`
- **Why it matters:** Demographic Parity only checks if approval rates are equal. Equalized Odds ensures BOTH true positive rate (TPR) and false positive rate (FPR) are equal across groups.
- **Use case:** Lending, hiring, healthcare - anywhere errors have different costs for different groups.
- **Formula:** |TPR_A - TPR_B| + |FPR_A - FPR_B|
- **Reference:** [Hardt et al. 2016](https://arxiv.org/abs/1610.02413)

### 2. **Predictive Parity** - Precision Across Groups
- **Metric:** `predictive_parity`
- **Why it matters:** When we make a positive prediction, it should be equally likely to be correct regardless of the applicant's protected attribute.
- **Use case:** Critical for hiring - if we predict "qualified", the probability of job success should be equal for men and women.
- **Formula:** |Precision_A - Precision_B|
- **Real-world impact:** Prevents scenario where one group gets hired on weak credentials while another gets rejected despite strong credentials.

### 3. **Privacy Metrics** - GDPR & Data Protection
New module: `venturalitica.metrics.privacy`

#### k-Anonymity
- **What:** Minimum group size in dataset when quasi-identifiers are known
- **Why:** Can't re-identify individuals if they're in groups of size k
- **GDPR:** Recommends k≥5
- **Formula:** Minimum |group| where group defined by quasi-identifiers

#### l-Diversity
- **What:** Minimum distinct values of sensitive attribute per quasi-identifier group
- **Why:** Even if you know age+gender, you can't infer diagnosis if multiple values exist
- **Formula:** Minimum distinct values in sensitive_attribute per QI group

#### t-Closeness
- **What:** Maximum distribution difference between groups
- **Why:** Prevents inference attacks on continuous attributes (lab values, income)
- **Formula:** Maximum Earth Mover Distance between distributions
- **Reference:** [Li et al. 2007](https://en.wikipedia.org/wiki/T-closeness)

#### Data Minimization (GDPR Art. 5)
- **What:** Proportion of non-sensitive columns
- **Why:** GDPR requires collecting only necessary data
- **Formula:** (total_columns - sensitive_columns) / total_columns
- **Target:** ≥ 0.70

---

## 📁 New Files & Structure

### Policies (Enhanced with Alternative Metrics)

```
policies/
├── loan/
│   ├── governance-baseline.oscal.yaml      (unchanged - traditional DP)
│   └── governance-enhanced.oscal.yaml      ✨ NEW - includes Equalized Odds, privacy
├── hiring/
│   ├── hiring-bias.oscal.yaml              (unchanged - traditional)
│   └── hiring-bias-enhanced.oscal.yaml     ✨ NEW - Predictive Parity focus
├── health/
│   ├── clinical-risk.oscal.yaml            (unchanged - traditional)
│   └── clinical-risk-enhanced.oscal.yaml   ✨ NEW - Privacy metrics priority
```

### Examples (New Demonstration Scenarios)

```
scenarios/
├── loan-mlflow-sklearn/
│   ├── 01_governance_audit.py              (unchanged - basic flow)
│   └── 02_alternative_metrics_demo.py      ✨ NEW - deep dive into metrics
├── hiring-wandb-torch/
│   ├── (existing files)
│   └── 02_advanced_fairness_analysis.py    ✨ NEW - Precision Paradox explanation
```

### Tests (Comprehensive Unit & Integration Tests)

```
tests/
├── test_metrics.py                         (existing - basic fairness)
├── test_enhanced_metrics.py                ✨ NEW - equalized odds, privacy
├── test_badges.py                          ✨ NEW - compliance badge generation
├── test_output_interpretation.py           ✨ NEW - semantic interpretation
└── (other tests unchanged)
```

### SDK Core (Fixed & Enhanced)

```
src/venturalitica/
├── __init__.py                             [MODIFIED] - VenturalíticaJSONEncoder
├── core.py                                 (unchanged)
├── metrics/
│   ├── __init__.py                         [MODIFIED] - METRIC_REGISTRY (16 metrics)
│   ├── fairness.py                         [MODIFIED] - strict validation, new metrics
│   ├── privacy.py                          ✨ NEW - 4 privacy metrics
│   ├── performance.py                      (existing)
│   └── data.py                             (existing)
├── output.py                               [MODIFIED] - semantic interpretation
├── badges.py                               ✨ NEW - SVG badge generation
└── (other modules unchanged)
```

---

## 🚀 Quick Start: Using New Metrics

### Basic Usage

```python
import venturalitica as vl
from venturalitica.metrics import METRIC_REGISTRY

# See all available metrics (16 total)
print(METRIC_REGISTRY.keys())

# Use new metric in policy
policy = {
    "metric_key": "equalized_odds_ratio",
    "threshold": 0.20,
    "operator": "<"
}

# Or run governance audit
vl.enforce(data=df, policy="policies/loan/governance-enhanced.oscal.yaml")
```

### Alternative Fairness Metrics

```python
from venturalitica.metrics.fairness import (
    calc_equalized_odds_ratio,
    calc_predictive_parity
)

# Equalized Odds (TPR + FPR parity)
odds_ratio = calc_equalized_odds_ratio(
    df,
    target='target',
    prediction='prediction', 
    dimension='gender'
)

# Predictive Parity (Precision parity)
pred_parity = calc_predictive_parity(
    df,
    target='target',
    prediction='prediction',
    dimension='gender'
)
```

### Privacy Metrics

```python
from venturalitica.metrics.privacy import (
    calc_k_anonymity,
    calc_l_diversity,
    calc_t_closeness,
    calc_data_minimization_score
)

# k-Anonymity check
k = calc_k_anonymity(df, quasi_identifiers=['age', 'gender', 'zipcode'])
assert k >= 5, "GDPR recommends k≥5"

# l-Diversity check
l = calc_l_diversity(
    df,
    quasi_identifiers=['age', 'gender'],
    sensitive_attribute='diagnosis'
)

# t-Closeness check
t = calc_t_closeness(
    df,
    quasi_identifiers=['age', 'gender'],
    sensitive_attribute='lab_result'
)

# Data minimization audit
score = calc_data_minimization_score(
    df,
    sensitive_columns=['age', 'income', 'health_status']
)
assert score >= 0.70, "Collecting too much sensitive data"
```

### Semantic Interpretation

```python
from venturalitica.output import _get_metric_interpretation

# Get human-readable interpretation
result = _get_metric_interpretation(
    metric_key='demographic_parity_diff',
    actual_value=0.08,
    threshold=0.10,
    operator='<'
)

# Returns:
# {
#   'risk_level': '🟢 LOW',
#   'interpretation': 'Perfect: 0.0800 ≤ 0.1000'
# }
```

### Badge Generation

```python
from venturalitica import generate_compliance_badge

# Generate compliance badge for README
badge = generate_compliance_badge(
    status='passing',
    policy_name='loan',
    date='2026-01-22'
)

# Markdown: ![Compliance](badge.svg)
```

---

## 🧪 Running Tests

### All New Tests
```bash
cd packages/venturalitica-sdk

# Enhanced metrics (Equalized Odds, Predictive Parity, Privacy)
pytest tests/test_enhanced_metrics.py -v

# Badge generation
pytest tests/test_badges.py -v

# Output interpretation and semantic meaning
pytest tests/test_output_interpretation.py -v

# Run all tests
pytest tests/ -v
```

### Running Example Scenarios
```bash
# Loan scenario with alternative metrics
cd scenarios/loan-mlflow-sklearn
python 02_alternative_metrics_demo.py

# Hiring scenario with Precision Paradox explanation
cd scenarios/hiring-wandb-torch
python 02_advanced_fairness_analysis.py
```

---

## 📚 Understanding Metric Relationships

### Fairness Metric Hierarchy (Strictness)

```
Demographic Parity (least strict)
    ↓ (same approval rates)
Equal Opportunity (medium)
    ↓ (same TPR - true positive rate)
Equalized Odds (most strict)
    ↓ (same TPR AND FPR)
Predictive Parity (orthogonal)
    ↓ (same precision)
```

**In practice:**
- DP can pass while others fail (approval rates equal but different errors)
- EqOpp can pass while EqOdds fails (equal TPR but unequal FPR)
- Predictive Parity often fails when model calibration differs by group

### Privacy Metric Relationship

```
Data Minimization (what to collect)
    ↓
k-Anonymity (re-identification risk)
    ↓
l-Diversity (attribute disclosure risk)
    ↓
t-Closeness (inference attack risk)
```

---

## 🔍 Breaking Changes from v1.0

| Change | Impact | Migration |
|--------|--------|-----------|
| `vl.quickstart()` removed | HIGH | Use `vl.enforce()` directly |
| Metrics now raise errors on missing columns | HIGH | Check column mappings in policy |
| Metrics 0.000 values now errors | HIGH | Debug context binding |
| JSON encoder changed | LOW | Automatic, no changes needed |

**Why:** Silent 0.000 values masked real fairness problems. Strict validation forces proper data setup.

---

## 📊 Metrics at a Glance

| Metric | Type | Formula | Ideal | Use Case |
|--------|------|---------|-------|----------|
| Demographic Parity | Fairness | \|P(Ŷ=1\|A=a) - P(Ŷ=1\|A=b)\| | 0.0 | Equal approval rates |
| Equal Opportunity | Fairness | \|TPR_a - TPR_b\| | 0.0 | Equal true positive rates |
| Equalized Odds | Fairness | \|TPR_a - TPR_b\| + \|FPR_a - FPR_b\| | 0.0 | Both TPR & FPR equal |
| Predictive Parity | Fairness | \|Precision_a - Precision_b\| | 0.0 | Equal prediction reliability |
| k-Anonymity | Privacy | min(\|group\|) | ≥5 | Re-identification protection |
| l-Diversity | Privacy | min(distinct values/group) | ≥2 | Attribute disclosure protection |
| t-Closeness | Privacy | max(distribution distance) | <0.15 | Inference attack protection |
| Data Minimization | Privacy | (non-sensitive cols) / (total cols) | ≥0.70 | GDPR compliance |

---

## 🎓 Learning Resources

### Papers
- **Equalized Odds:** [Hardt et al. 2016](https://arxiv.org/abs/1610.02413)
- **Predictive Parity:** [Corbett-Davies et al. 2017](https://arxiv.org/abs/1708.09055)
- **k-Anonymity:** [Sweeney 2002](https://dataprivacylab.org/)
- **Privacy Metrics:** [Li et al. 2007](https://en.wikipedia.org/wiki/T-closeness)

### Libraries
- [Fairlearn](https://fairlearn.org/) - Microsoft fairness library
- [AI Fairness 360](https://aif360.readthedocs.io/) - IBM fairness metrics
- [Diffprivlib](https://diffprivlib.readthedocs.io/) - Differential privacy

### Frameworks
- [GDPR Article 5](https://gdpr-info.eu/art-5-gdpr/) - Data minimization principle
- [OSCAL](https://pages.nist.gov/OSCAL/) - Open Security Controls Assessment Language

---

## ❓ FAQ

### Q: Which metric should I use?
**A:** 
- **Loan/Hiring:** Start with Equalized Odds (both TPR & FPR) + Predictive Parity (reliability)
- **Healthcare:** Start with Equalized Odds + Privacy metrics (k-anonymity ≥5)
- **Research:** All metrics together for comprehensive analysis

### Q: My metric is returning 0.000
**A:** 
It's not anymore! If you had 0.000 metrics before, they're now raising errors. Check:
1. Is column name correct? (Column exists in DataFrame)
2. Are values consistent? (M vs 1, no NaN values)
3. Is it truly binary target? (0/1 or True/False)

### Q: Can metrics conflict?
**A:** Yes! Different metrics optimize different concepts:
- **Demographic Parity** vs **Equalized Odds:** DP focuses on selection rate, EqOdds on errors
- **Fairness** vs **Accuracy:** Fairness constraints may reduce overall accuracy
- Choose metrics aligned with your ethical values, not just optimization goals

### Q: How do I handle multi-class classification?
**A:** Current metrics are binary. For multi-class:
1. Run one-vs-rest for each class
2. Aggregate using weighted average
3. Consider micro/macro averages
(Multi-class support planned for v1.2)

### Q: What's the difference between threshold and operator?
**A:** 
- **Threshold:** The target value (e.g., 0.10 for Demographic Parity)
- **Operator:** Comparison direction (e.g., "<" means metric should be below threshold)

```yaml
metric_key: demographic_parity_diff
threshold: 0.10
operator: "<"  # Goal: metric < 0.10
```

---

## 📝 Version History

### v1.1 (Current)
- ✨ Equalized Odds metric
- ✨ Predictive Parity metric
- ✨ Privacy metrics (k-anonymity, l-diversity, t-closeness, data minimization)
- ✨ Semantic interpretation layer (🟢🟡🔴 indicators)
- ✨ Badge generation for GitHub
- 🐛 Fixed silent 0.000 metric returns
- 🐛 Fixed JSON serialization errors
- ❌ Removed vl.quickstart() API

### v1.0 (Previous)
- Demographic Parity
- Equal Opportunity
- Performance metrics (accuracy, precision, recall, F1)
- Data quality metrics

---

## 🤝 Contributing

To add a new metric:

1. **Create function in appropriate module:**
   ```python
   # In metrics/fairness.py or metrics/privacy.py
   def calc_my_metric(df, **kwargs) -> float:
       # Strict validation
       if missing_column:
           raise ValueError(f"Missing column. Did you mean? Check policy mapping.")
       # Calculate
       return value
   ```

2. **Register in `metrics/__init__.py`:**
   ```python
   METRIC_REGISTRY['my_metric'] = calc_my_metric
   
   METRIC_METADATA['my_metric'] = {
       'name': 'My Metric',
       'description': '...',
       'category': 'fairness',  # or 'privacy', 'performance'
       'ideal_value': 0.0,
       'reference': 'https://...'
   }
   ```

3. **Add tests in `tests/test_enhanced_metrics.py`:**
   ```python
   def test_my_metric_perfect_case():
       result = calc_my_metric(perfect_data)
       assert result == 0.0
   ```

4. **Update documentation and examples**

---

## 📞 Support

- **Issues:** GitHub Issues on [venturalitica-integration](repo)
- **Discussions:** GitHub Discussions
- **Email:** support@venturalitica.dev

---

**Status:** Production Ready ✓  
**Last Updated:** 2026-01-22  
**Maintainers:** Venturalítica Governance Team
