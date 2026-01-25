# Advanced Features

This guide covers advanced usage patterns, custom configurations, and programmatic access to the Venturalítica SDK.

## Programmatic Report Generation

You can generate markdown reports programmatically from enforcement results for custom dashboards or email notifications.

```python
from venturalitica import enforce
from venturalitica.integrations import generate_report

results = enforce(
    data=df,
    target="approved",
    prediction=predictions,
    gender="gender",
    policy="risks.oscal.yaml"
)

# Generate markdown report
report_md = generate_report(results)
with open("compliance_report.md", "w") as f:
    f.write(report_md)
```

## Custom Storage Backends

By default, the SDK looks for policies in the local filesystem. You can customize the storage location using the `LocalFileSystemStorage` class.

```python
from venturalitica.storage import LocalFileSystemStorage
from venturalitica.core import GovernanceValidator

# Use custom policy storage location
storage = LocalFileSystemStorage(base_path="/custom/policies")
validator = GovernanceValidator("risks.oscal.yaml", storage=storage)
```

## Robust Evaluation: Handling Missing Columns

The SDK is designed to handle missing columns gracefully, which is particularly useful for performing audits at different stages of the ML lifecycle.

### Pre-training (Data Audit Only)
If you haven't trained a model yet, you won't have a `prediction` column. The SDK will automatically skip any controls that require it.

```python
# Pre-training: no predictions yet
enforce(
    data=df_train,
    target="approved",
    gender="gender",
    policy="risks.oscal.yaml"  # Will skip controls requiring 'prediction'
)
```

### Post-training (Full Audit)
Once you have predictions, the SDK evaluates all controls in the policy.

```python
# Post-training: full audit
enforce(
    data=df_test,
    target="approved",
    prediction=predictions,
    gender="gender",
    policy="risks.oscal.yaml"  # All controls evaluated
)
```

## Accessing Raw Compliance Results

If you need to perform additional logic based on the compliance status of specific controls, you can access the raw result objects.

```python
from venturalitica.core import ComplianceResult

results: List[ComplianceResult] = enforce(
    data=df,
    target="approved",
    prediction=predictions,
    gender="gender",
    policy="risks.oscal.yaml"
)

for result in results:
    print(f"Control: {result.control_id}")
    print(f"Passed: {result.passed}")
    print(f"Metric: {result.metric_key} = {result.actual_value:.4f}")
    print(f"Threshold: {result.operator} {result.threshold}")
```

## Multi-Policy Enforcement

You can enforce multiple OSCAL policies in a single call by passing a list of policy files. This is useful for combining baseline organizational policies with project-specific risk assessments.

```python
enforce(
    data=df,
    policy=[
        "policies/global-baseline.oscal.yaml",
        "policies/project-risks.oscal.yaml"
    ]
)
```
