import pandas as pd
from venturalitica.privacy import calc_k_anonymity, calc_l_diversity


def test_k_anonymity_simple():
    df = pd.DataFrame({'age': [25, 25, 30, 30, 35], 'zip': ['10001', '10001', '10002', '10002', '10003']})
    k = calc_k_anonymity(df, quasi_identifiers=['age', 'zip'])
    assert k == 2.0


def test_k_anonymity_csv_string():
    df = pd.DataFrame({'age': [25, 25], 'zip': ['10001', '10001']})
    k = calc_k_anonymity(df, quasi_identifiers='age,zip')
    assert k == 2.0


def test_l_diversity_simple():
    df = pd.DataFrame({'age': [25,25,25,30], 'diag': ['A','A','B','A']})
    l = calc_l_diversity(df, quasi_identifiers=['age'], sensitive_attribute='diag')
    assert l == 2.0
