"""Local sensitivity simulation. Never normalizes, mutates or replaces official KPIs."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext

import pandas as pd

from domain.models import ComparisonPeriod
from domain.periods import split_equivalent_periods
from services.anomalies import assess_monetary_anomalies
from services.metrics_engine import (
    ColumnMap,
    exact_decimal_sum,
    exact_revenue_ranking,
    safe_count_unique,
)


@dataclass(frozen=True)
class Amounts:
    revenue: Decimal
    records: int
    orders: int
    ticket: Decimal | None


@dataclass(frozen=True)
class RankedEntity:
    name: str
    rank: int
    tied: bool
    revenue: Decimal
    orders: int
    ticket: Decimal | None
    share: Decimal | None


@dataclass(frozen=True)
class Scenario:
    total: Amounts
    current: Amounts
    previous: Amounts
    outside: Amounts
    stores: tuple[RankedEntity, ...] | None
    products: tuple[RankedEntity, ...] | None
    date_label: str


@dataclass(frozen=True)
class SensitivityAnalysis:
    integral: Scenario
    simulated: Scenario
    period: ComparisonPeriod
    flagged_records: int
    flagged_revenue: Decimal
    threshold: Decimal | None
    criterion: str
    uses_order_id: bool
    revenue_difference: Decimal


def _sum(values):
    return exact_decimal_sum(pd.Series(list(values), dtype=object))


def _amounts(frame, columns):
    revenue = exact_decimal_sum(frame[columns.faturamento])
    orders = safe_count_unique(frame, columns.pedido) if columns.pedido else len(frame)
    ticket = revenue / orders if orders else None
    return Amounts(revenue, len(frame), orders, ticket)


def _ranking(frame, dimension, columns, total):
    if not dimension or dimension not in frame:
        return None
    ordered = exact_revenue_ranking(frame, dimension, columns.faturamento)
    values = [value for _, value in ordered]
    counts = Counter(values)
    ranks = {}
    for position, (_, revenue) in enumerate(ordered, 1):
        ranks.setdefault(revenue, position)
    groups = {str(name): _amounts(group, columns) for name, group in frame.groupby(dimension, dropna=False)}
    result = []
    for name, revenue in ordered:
        amounts = groups[name]
        result.append(RankedEntity(
            name, ranks[revenue], counts[revenue] > 1,
            revenue, amounts.orders, amounts.ticket, revenue / total * 100 if total else None,
        ))
    return tuple(result)


def _scenario(frame, columns, period):
    empty = frame.iloc[0:0]
    if columns.data and period.previous_start is not None:
        dates = frame[columns.data]
        current_mask = (dates >= pd.Timestamp(period.current_start)) & (dates < pd.Timestamp(period.current_end) + pd.Timedelta(days=1))
        previous_mask = (dates >= pd.Timestamp(period.previous_start)) & (dates < pd.Timestamp(period.previous_end) + pd.Timedelta(days=1))
        current, previous, outside = frame[current_mask], frame[previous_mask], frame[~(current_mask | previous_mask)]
    else:
        current, previous, outside = empty, empty, frame
    dates = frame[columns.data].dropna() if columns.data else pd.Series(dtype="datetime64[ns]")
    date_label = f"{dates.min():%d/%m/%Y}–{dates.max():%d/%m/%Y}" if not dates.empty else "Sem datas disponíveis"
    total = _amounts(frame, columns)
    scenario = Scenario(
        total, _amounts(current, columns), _amounts(previous, columns), _amounts(outside, columns),
        _ranking(frame, columns.loja, columns, total.revenue),
        _ranking(frame, columns.produto, columns, total.revenue), date_label,
    )
    validate_scenario(scenario)
    return scenario


def validate_scenario(scenario):
    """Orders are unique per scope, not necessarily additive between groups/periods."""
    parts = (scenario.current, scenario.previous, scenario.outside)
    if _sum(item.revenue for item in parts) != scenario.total.revenue:
        raise ValueError("Sensitivity period reconciliation failed")
    if sum(item.records for item in parts) != scenario.total.records:
        raise ValueError("Sensitivity record reconciliation failed")
    for ranking in (scenario.stores, scenario.products):
        if ranking is not None and _sum(row.revenue for row in ranking) != scenario.total.revenue:
            raise ValueError("Sensitivity dimension reconciliation failed")


def build_sensitivity_analysis(frame: pd.DataFrame, columns: ColumnMap):
    if not columns.faturamento or columns.faturamento not in frame:
        return None
    # Canonical rows are expected. Reject unaccounted invalid money, not silent zeros.
    try:
        numbers = [Decimal(str(value)) for value in frame[columns.faturamento]]
    except InvalidOperation:
        raise ValueError("Sensitivity requires valid canonical money") from None
    if any(not value.is_finite() for value in numbers):
        raise ValueError("Sensitivity requires finite canonical money")
    integer_digits = max((value.adjusted() + 1 for value in numbers), default=1)
    scale = max((-value.as_tuple().exponent for value in numbers), default=0)
    with localcontext() as context:
        context.prec = max(50, integer_digits + scale + len(str(len(numbers))) + 20)
        assessment = assess_monetary_anomalies(frame, columns.faturamento)
        _, _, period = split_equivalent_periods(frame, columns.data)
        excluded = set(assessment.positions)
        typical = frame.iloc[[position for position in range(len(frame)) if position not in excluded]]
        integral = _scenario(frame, columns, period)
        simulated = _scenario(typical, columns, period)
        flagged_revenue = exact_decimal_sum(frame[columns.faturamento].iloc[list(assessment.positions)])
        difference = simulated.total.revenue - integral.total.revenue
        if integral.total.records - simulated.total.records != len(excluded) or difference != -flagged_revenue:
            raise ValueError("Sensitivity scenario reconciliation failed")
        return SensitivityAnalysis(
            integral, simulated, period, len(excluded), flagged_revenue,
            assessment.threshold, assessment.criterion, bool(columns.pedido), difference,
        )
