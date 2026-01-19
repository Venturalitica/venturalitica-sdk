import pytest
import pandas as pd
import numpy as np
from venturalitica.metrics import (
    calc_accuracy, calc_precision, calc_recall, calc_f1,
    calc_demographic_parity, calc_equal_opportunity,
    calc_disparate_impact, calc_class_imbalance,
    METRIC_REGISTRY
)

@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'target': [1, 0, 1, 1, 0, 0, 1, 0],
        'prediction': [1, 0, 0, 1, 1, 0, 1, 0],
        'sensitive': ['A', 'A', 'A', 'A', 'B', 'B', 'B', 'B']
    })

def test_standard_metrics(sample_data):
    kwargs = {'target': 'target', 'prediction': 'prediction'}
    assert calc_accuracy(sample_data, **kwargs) == 0.75
    assert calc_precision(sample_data, **kwargs) == 0.75 # TP=3 (idx 0,3,6), FP=1 (idx 4)
    assert calc_recall(sample_data, **kwargs) == 0.75    # TP=3, FN=1 (idx 2)
    assert calc_f1(sample_data, **kwargs) == 0.75

def test_demographic_parity(sample_data):
    kwargs = {'target': 'target', 'prediction': 'prediction', 'sensitive': 'sensitive'}
    # Group A: [1, 0, 0, 1] -> mean = 0.5
    # Group B: [1, 0, 1, 0] -> mean = 0.5
    # Diff = 0.0
    assert calc_demographic_parity(sample_data, **kwargs) == 0.0

def test_equal_opportunity(sample_data):
    kwargs = {'target': 'target', 'prediction': 'prediction', 'sensitive': 'sensitive'}
    # Group A positive: idx 0, 2, 3 -> preds [1, 0, 1] -> mean = 0.666...
    # Group B positive: idx 6 -> preds [1] -> mean = 1.0
    # Diff = 0.333...
    res = calc_equal_opportunity(sample_data, **kwargs)
    assert pytest.approx(res) == 0.3333333333333333

def test_disparate_impact(sample_data):
    kwargs = {'target': 'target', 'sensitive': 'sensitive'}
    # Group A target: [1, 0, 1, 1] -> mean = 0.75
    # Group B target: [0, 0, 1, 0] -> mean = 0.25
    # Ratio = 0.25 / 0.75 = 0.333...
    res = calc_disparate_impact(sample_data, **kwargs)
    assert pytest.approx(res) == 0.3333333333333333

def test_class_imbalance(sample_data):
    kwargs = {'target': 'target'}
    # 4 ones, 4 zeros -> ratio 1.0
    assert calc_class_imbalance(sample_data, **kwargs) == 1.0

def test_registry():
    assert "accuracy_score" in METRIC_REGISTRY
    assert "disparate_impact" in METRIC_REGISTRY

def test_missing_cols(sample_data):
    with pytest.raises(ValueError, match="Missing required columns"):
        calc_accuracy(sample_data, target='target') # missing prediction
