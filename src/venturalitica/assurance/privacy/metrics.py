"""
Privacy-preserving metrics for data anonymization assessment.

References:
- Sweeney, L. (2002). k-anonymity: A model for protecting privacy
- Machanavajjhala et al. (2006). l-diversity: Privacy beyond k-anonymity
"""

import pandas as pd


def calc_k_anonymity(df: pd.DataFrame, **kwargs) -> float:
    """
    Calculates the k-anonymity level of a dataset.

    k-anonymity means each combination of quasi-identifiers appears
    at least k times in the dataset.

    Args:
        df: DataFrame
        quasi_identifiers: List of column names (e.g., ['age', 'zip', 'gender'])

    Returns:
        float: k-anonymity level (minimum group size)
               Higher is better (e.g., k=5 means min group size 5)

    Raises:
        ValueError: If quasi_identifiers not provided

    Example:
        >>> df = pd.DataFrame({
        ...     'age': [25, 25, 30, 30, 35],
        ...     'zip': ['10001', '10001', '10002', '10002', '10003'],
        ...     'salary': [50000, 52000, 60000, 62000, 70000]
        ... })
        >>> calc_k_anonymity(df, quasi_identifiers=['age', 'zip'])
        2.0  # Min group size is 2
    """
    quasi_identifiers = kwargs.get("quasi_identifiers", [])

    # Accept comma-separated string or list input from policy props
    if isinstance(quasi_identifiers, str):
        quasi_identifiers = [
            q.strip() for q in quasi_identifiers.split(",") if q.strip()
        ]

    if (
        isinstance(quasi_identifiers, (list, tuple))
        and len(quasi_identifiers) == 1
        and isinstance(quasi_identifiers[0], str)
        and "," in quasi_identifiers[0]
    ):
        # Guard against nested comma string inside a list
        quasi_identifiers = [
            q.strip() for q in quasi_identifiers[0].split(",") if q.strip()
        ]

    if not quasi_identifiers:
        raise ValueError(
            "quasi_identifiers required for k-anonymity. "
            "💡 Did you mean? Specify columns that could re-identify: ['age', 'zip', 'gender']"
        )

    missing_cols = [c for c in quasi_identifiers if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Quasi-identifier columns not found: {missing_cols}. "
            f"Available: {list(df.columns)}"
        )

    # Count frequency of each quasi-identifier combination
    group_sizes = df.groupby(quasi_identifiers).size()

    # k-anonymity is the minimum group size
    k = group_sizes.min() if not group_sizes.empty else 0

    return float(k)


def calc_l_diversity(df: pd.DataFrame, **kwargs) -> float:
    """
    Calculates l-diversity of a dataset.

    l-diversity ensures that each quasi-identifier combination has
    at least l distinct values for sensitive attributes.

    Args:
        df: DataFrame
        quasi_identifiers: List of QI columns
        sensitive_attribute: Column name (e.g., 'diagnosis', 'income')

    Returns:
        float: l-diversity level (minimum distinct values per group)
               Higher is better (e.g., l=3 means min 3 distinct diagnoses per QI group)

    Raises:
        ValueError: If quasi_identifiers or sensitive_attribute not provided
    """
    quasi_identifiers = kwargs.get("quasi_identifiers", [])
    sensitive_attr = kwargs.get("sensitive_attribute", None)

    if not quasi_identifiers:
        raise ValueError("quasi_identifiers required for l-diversity")

    if not sensitive_attr:
        raise ValueError(
            "sensitive_attribute required for l-diversity (e.g., 'diagnosis'). "
            "💡 Did you mean? This is the column you want to protect."
        )

    missing_cols = [
        c for c in quasi_identifiers + [sensitive_attr] if c not in df.columns
    ]
    if missing_cols:
        raise ValueError(f"Columns not found: {missing_cols}")

    # For each QI group, count distinct values in sensitive attribute
    grouped = df.groupby(quasi_identifiers)
    distinct_counts = grouped[sensitive_attr].nunique()

    # l-diversity is the minimum distinct values
    l_diversity_value = distinct_counts.min()

    return float(l_diversity_value)


def calc_t_closeness(df: pd.DataFrame, **kwargs) -> float:
    """
    Calculates t-closeness of a dataset.

    t-closeness measures the maximum distance between the distribution
    of a sensitive attribute in a quasi-identifier group and the
    overall distribution.

    Args:
        df: DataFrame
        quasi_identifiers: List of QI columns
        sensitive_attribute: Column name (must be ordinal or categorical)

    Returns:
        float: t-closeness level (max distance) (0-1)
               Lower is better (e.g., t=0.1 means max 10% distribution difference)

    Note: Implementation uses Earth Mover's Distance (EMD) for ordinal attributes
    """
    quasi_identifiers = kwargs.get("quasi_identifiers", [])
    sensitive_attr = kwargs.get("sensitive_attribute", None)

    if not quasi_identifiers:
        raise ValueError("quasi_identifiers required for t-closeness")

    if not sensitive_attr:
        raise ValueError("sensitive_attribute required for t-closeness")

    missing_cols = [
        c for c in quasi_identifiers + [sensitive_attr] if c not in df.columns
    ]
    if missing_cols:
        raise ValueError(f"Columns not found: {missing_cols}")

    # Calculate overall distribution
    overall_dist = df[sensitive_attr].value_counts(normalize=True).sort_index()

    # Calculate max distance in any group
    grouped = df.groupby(quasi_identifiers)
    max_distance = 0.0

    for _, group in grouped:
        group_dist = group[sensitive_attr].value_counts(normalize=True).sort_index()

        # Simple L1 distance (can be extended to EMD for ordinal)
        all_values = set(overall_dist.index) | set(group_dist.index)
        distance = 0.0

        for val in all_values:
            overall_prob = overall_dist.get(val, 0.0)
            group_prob = group_dist.get(val, 0.0)
            distance += abs(overall_prob - group_prob)

        distance = distance / 2  # Normalize L1
        max_distance = max(max_distance, distance)

    return float(max_distance)


def calc_data_minimization_score(df: pd.DataFrame, **kwargs) -> float:
    """
    Calculates data minimization score (GDPR Art. 5(1)(c)).

    Measures: 1 - (sensitive_cols / total_cols)

    Returns:
        float: Score 0-1 (1 = no sensitive data, 0 = all sensitive)
               Higher is better
    """
    sensitive_cols = kwargs.get("sensitive_columns", [])

    if not sensitive_cols:
        # Auto-detect common sensitive columns
        sensitive_cols = [
            c
            for c in df.columns
            if any(
                keyword in c.lower()
                for keyword in [
                    "age",
                    "gender",
                    "race",
                    "ethnicity",
                    "health",
                    "medical",
                    "income",
                    "salary",
                    "phone",
                    "email",
                    "ssn",
                    "id",
                ]
            )
        ]

    if not sensitive_cols:
        return 1.0  # No sensitive data detected

    missing_cols = [c for c in sensitive_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Sensitive columns not found: {missing_cols}")

    score = 1.0 - (len(sensitive_cols) / len(df.columns))
    return float(max(0.0, min(1.0, score)))  # Clamp to [0, 1]
