"""
ESG-specific quality metrics for sustainability reporting datasets.

Measures balance and coverage of Environmental, Social, Governance categories,
plus provenance traceability and topical diversity within reports.
"""

import pandas as pd


def calc_classification_distribution(df: pd.DataFrame, **kwargs) -> tuple:
    """Compute classification diversity score (min_class_ratio / max_class_ratio).

    For ESG datasets: measures balance across Environmental, Social, Governance categories.
    Returns tuple: (diversity_score, {category: percentage})
    """
    target = kwargs.get("target") or kwargs.get("input:target")
    if not target:
        raise ValueError(
            "Missing required role 'target' for calc_classification_distribution"
        )
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in DataFrame")

    counts = df[target].dropna().value_counts()
    if counts.empty:
        return 0.0, {}

    total = counts.sum()
    percentages = {k: round(v / total * 100, 2) for k, v in counts.items()}

    if len(counts) == 1:
        return 0.0, percentages

    min_count = counts.min()
    max_count = counts.max()
    if max_count == 0:
        return 0.0, percentages

    diversity_score = round(min_count / max_count, 4)
    return diversity_score, percentages


def calc_report_coverage(df: pd.DataFrame, **kwargs) -> float:
    """Compute report coverage as unique_reports / total_samples.

    For ESG datasets: measures how many unique sustainability reports are represented.
    Returns coverage ratio (0.0 - 1.0).
    """
    target = kwargs.get("target") or kwargs.get("input:target")
    if not target:
        raise ValueError("Missing required role 'target' for calc_report_coverage")
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in DataFrame")

    unique_reports = df[target].dropna().nunique()
    total_samples = len(df)

    if total_samples == 0:
        return 0.0

    return round(unique_reports / total_samples, 4)


def calc_provenance_completeness(df: pd.DataFrame, **kwargs) -> float:
    """Compute provenance completeness as fraction of samples with traceable metadata.

    For ESG datasets: checks if page_number, chunk_number are present for traceability.
    Returns completeness score (0.0 - 1.0).
    """
    required_fields = kwargs.get("input:fields", ["page_number", "chunk_number"])
    if isinstance(required_fields, str):
        import ast

        try:
            required_fields = ast.literal_eval(required_fields)
        except Exception:
            required_fields = [required_fields]

    if not required_fields:
        required_fields = ["page_number", "chunk_number"]

    if not all(f in df.columns for f in required_fields):
        return 0.0

    complete_mask = df[required_fields].notna().all(axis=1)
    return round(complete_mask.mean(), 4)


def calc_chunk_diversity(df: pd.DataFrame, **kwargs) -> tuple:
    """Compute chunk diversity: unique_chunks_per_report average.

    For ESG datasets: measures if reports have sufficient chunk coverage.
    Returns tuple: (avg_chunks_per_report, {report: chunk_count}).
    """
    target = kwargs.get("target") or kwargs.get("input:target")
    dim = kwargs.get("input:dimension") or kwargs.get("dimension")

    if not target or not dim:
        raise ValueError(
            "Missing required roles: 'target' and 'dimension' for calc_chunk_diversity"
        )

    if dim not in df.columns or target not in df.columns:
        raise ValueError(f"Columns not found: target={target}, dimension={dim}")

    chunk_counts = df.groupby(target)[dim].nunique()
    avg_chunks = chunk_counts.mean()
    report_coverage = {str(k): int(v) for k, v in chunk_counts.items()}

    return round(avg_chunks, 2), report_coverage


def calc_subtitle_diversity(df: pd.DataFrame, **kwargs) -> float:
    """Compute subtitle/section diversity: how many unique subtitles per report.

    For ESG datasets: measures topical coverage within reports.
    Returns diversity score (0.0 - 1.0) as avg_subtitles / expected_max.
    """
    target = kwargs.get("target") or kwargs.get("input:target")
    dim = kwargs.get("input:dimension") or kwargs.get("dimension")

    if not target or not dim:
        raise ValueError(
            "Missing required roles: 'target' and 'dimension' for calc_subtitle_diversity"
        )

    if dim not in df.columns or target not in df.columns:
        raise ValueError("Columns not found")

    # Count unique subtitles per report
    def count_unique_subtitles(group):
        # Handle both list and string formats
        subtitles = group[dim]
        if isinstance(subtitles, list):
            unique = len(set([s for s in subtitles if s]))
        elif isinstance(subtitles, str):
            unique = len(set([s.strip() for s in subtitles.split(",") if s.strip()]))
        else:
            unique = 0
        return unique

    subtitle_counts = df.groupby(target).apply(count_unique_subtitles)
    avg_subtitles = subtitle_counts.mean()

    # Normalize: assume 10+ subtitles indicates good coverage
    return min(round(avg_subtitles / 10.0, 4), 1.0)
