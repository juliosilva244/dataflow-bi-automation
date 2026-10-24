from __future__ import annotations

import pandas as pd

from domain.models import ComparisonPeriod


def split_equivalent_periods(
    df: pd.DataFrame, data_col: str | None
) -> tuple[pd.DataFrame, pd.DataFrame, ComparisonPeriod]:
    empty = pd.DataFrame(columns=df.columns)
    if not data_col or data_col not in df.columns:
        return df.copy(), empty, ComparisonPeriod(None, None, None, None, False)

    valid = df.dropna(subset=[data_col]).sort_values(data_col).copy()
    if valid.empty or len(valid) < 2:
        return valid, empty, ComparisonPeriod(None, None, None, None, False)

    start = valid[data_col].min().normalize()
    end = valid[data_col].max().normalize()
    total_days = (end - start).days + 1
    current_days = total_days // 2
    if current_days < 1:
        return valid, empty, ComparisonPeriod(None, None, None, None, False)

    current_start = end - pd.Timedelta(days=current_days - 1)
    previous_end = current_start - pd.Timedelta(days=1)
    previous_start = previous_end - pd.Timedelta(days=current_days - 1)
    current = valid[valid[data_col] >= current_start].copy()
    previous = valid[
        (valid[data_col] >= previous_start) & (valid[data_col] < current_start)
    ].copy()
    comparison = ComparisonPeriod(
        current_start=current_start.date(),
        current_end=end.date(),
        previous_start=previous_start.date(),
        previous_end=previous_end.date(),
        available=not current.empty and not previous.empty,
    )
    return current, previous, comparison

