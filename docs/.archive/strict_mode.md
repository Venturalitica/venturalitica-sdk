# Strict Mode Compliance

## 🛡️ Preventing Silent Failures (Article 14)

The EU AI Act (Article 14) mandates effective human oversight and technical measures to prevent risks. In a programmatic compliance workflow, the biggest risk is a "silent failure"—where a compliance check is skipped due to a misconfiguration (e.g., a missing column or undefined metric) but the pipeline continues to deploy the model.

Venturalítica enforces **Strict Mode** to prevent this.

## How it Works

When Strict Mode is enabled:
1.  **Missing Metrics**: If a control references a metric key that is not registered, the validation raises a `ValueError` instead of skipping.
2.  **Unbound Variables**: If a policy requires a variable (e.g., `zip_code`) that cannot be found in your DataFrame or context mapping, the validation raises a `ValueError`.
3.  **Calculation Errors**: Any runtime error during metric calculation (e.g., division by zero) becomes a hard failure.

### Auto-Detection (CI/CD)

The SDK automatically detects if it is running in a Continuous Integration environment.

*   **If `CI=true`**: Strict Mode is **ENABLED** by default.
*   **If `VENTURALITICA_STRICT=true`**: Strict Mode is **ENABLED**.

This means you can develop locally with "loose" checks (getting warnings for missing config), but your CI pipeline (GitHub Actions, GitLab CI, Jenkins) will **break the build** if compliance is not fully rigorous.

## Manual Configuration

You can force strict mode in your code:

```python
import venturalitica as vl

# Force strict checking even locally
vl.enforce(
    data=df,
    target="y",
    policy="my_policy.yaml",
    strict=True  # <--- Raises errors on any missing config
)
```

## Best Practices

1.  **Always use `CI=true` in production pipelines.**
2.  **Monitor your logs.** In loose mode (local), watch for `[Skip]` warnings.
3.  **Define all metrics.** Ensure every metric key in your OSCAL policy has a corresponding function in the `METRIC_REGISTRY`.
