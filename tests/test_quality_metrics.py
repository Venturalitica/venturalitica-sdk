import pandas as pd
from venturalitica.quality import calc_class_imbalance, calc_data_completeness


def test_calc_class_imbalance_balanced():
    df = pd.DataFrame({'y': [1, 0, 1, 0]})
    val = calc_class_imbalance(df, target='y')
    assert 0.99 <= val <= 1.0  # Should be ~1.0 for perfectly balanced


def test_calc_class_imbalance_imbalanced():
    df = pd.DataFrame({'y': [1, 1, 1, 0]})
    val = calc_class_imbalance(df, target='y')
    assert 0.0 < val < 1.0


def test_calc_class_imbalance_single_class():
    df = pd.DataFrame({'y': [1, 1, 1, 1]})
    val = calc_class_imbalance(df, target='y')
    assert val == 0.0


def test_calc_data_completeness_all_present():
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    assert calc_data_completeness(df) == 1.0


def test_calc_data_completeness_with_missing():
    df = pd.DataFrame({'a': [1, None], 'b': [None, 4]})
    # completeness per col: [0.5, 0.5] -> mean 0.5
    assert calc_data_completeness(df) == 0.5
