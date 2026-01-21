# OSCAL Policy Authoring

This guide explains how to write and customize governance policies using the NIST OSCAL (Open Security Controls Assessment Language) standard.

## Policy Structure

Venturalitica uses a simplified OSCAL `assessment-plan` format to define its governance policies. Here is the basic structure:

```yaml
assessment-plan:
  uuid: unique-policy-identifier
  metadata:
    title: "Human-Readable Policy Name"
    version: "1.0.0"
  
  reviewed-controls:
    control-selections:
      - include-controls:
        - control-id: unique-control-id
          description: "Educational description explaining WHY this control matters"
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

## Available Metrics

### Performance Metrics
- `accuracy` - Overall classification accuracy
- `precision` - Positive predictive value
- `recall` - True positive rate
- `f1` - Harmonic mean of precision and recall

### Fairness Metrics
- `demographic_parity_diff` - Difference in positive prediction rates across groups
- `equal_opportunity_diff` - Difference in true positive rates across groups
- `disparate_impact` - Ratio of positive prediction rates (80% Rule)

### Data Quality Metrics
- `class_imbalance` - Proportion of minority class

## Operators

- `<` - Less than
- `<=` - Less than or equal
- `>` - Greater than
- `>=` - Greater than or equal
- `==` - Equal to
- `!=` - Not equal to

## Pre-training vs Post-training Controls

### Pre-training (data-only audits)
Use these to validate your training data *before* spending compute:

```yaml
- control-id: data-quality-check
  description: "Class Imbalance check before training"
  props:
    - name: metric_key
      value: class_imbalance
    - name: threshold
      value: "0.20"
    - name: operator
      value: ">="
    - name: "input:target"
      value: target
```

### Post-training (model fairness audits)
Use these to validate the model's actual predictions:

```yaml
- control-id: fairness-check
  description: "Demographic Parity after training"
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

## Educational Descriptions

Make your policies self-documenting. The `description` field is shown in the audit logs to help developers understand the governance requirements:

```yaml
- control-id: credit-data-bias
  description: "Pre-training Fairness: Disparate impact ratio should follow the standard '80% Rule' (Four-Fifths Rule), ensuring favorable loan outcomes are representative across groups."
```
