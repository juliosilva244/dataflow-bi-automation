from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext

import pandas as pd

ANOMALY_CRITERION = "valor acima do maior limite entre Q3 + 10 × IQR e 1.000 × mediana positiva"
ANOMALY_MESSAGE = (
    "Foram identificados valores financeiros atípicos nos dados analisados. "
    "Esses registros foram preservados nos cálculos e podem influenciar significativamente "
    "os indicadores. Sua presença não comprova erro nos dados nem falha operacional."
)


def financial_anomaly_notice(records: int) -> str:
    return ANOMALY_MESSAGE + f" Registros sinalizados: {records}."


@dataclass(frozen=True)
class MonetaryAnomalies:
    positions: tuple[int, ...]
    threshold: Decimal | None
    criterion: str = ANOMALY_CRITERION


def assess_monetary_anomalies(df, column="Faturamento", *, median_multiplier=Decimal(1000)):
    """Same statistical rule, Decimal quantiles, row positions (even with duplicate indexes)."""
    if column not in df or df.empty:
        return MonetaryAnomalies((), None)
    numbers = []
    for position, value in enumerate(df[column]):
        try:
            number = Decimal(str(value))
        except InvalidOperation:
            continue
        if number.is_finite():
            numbers.append((position, number))
    positive = sorted(number for _, number in numbers if number > 0)
    if not positive:
        return MonetaryAnomalies((), None)
    digits = max(value.adjusted() + 1 for value in positive)
    scale = max(-value.as_tuple().exponent for value in positive)
    with localcontext() as context:
        context.prec = max(50, digits + scale + 20)

        def quantile(fraction):
            index = Decimal(len(positive) - 1) * fraction
            lower = int(index)
            upper = min(lower + 1, len(positive) - 1)
            return positive[lower] + (positive[upper] - positive[lower]) * (index - lower)

        q1, q3 = quantile(Decimal(".25")), quantile(Decimal(".75"))
        limit = max(q3 + 10 * (q3 - q1), quantile(Decimal(".5")) * Decimal(str(median_multiplier)))
    positions = tuple(position for position, value in numbers if value > limit)
    return MonetaryAnomalies(positions, limit)


def detect_extreme_monetary_values(
    df: pd.DataFrame,
    column: str = "Faturamento",
    *,
    median_multiplier: float = 1_000.0,
) -> pd.DataFrame:
    """Flag exceptionally large values without classifying or removing them as errors."""
    assessment = assess_monetary_anomalies(df, column, median_multiplier=median_multiplier)
    if not assessment.positions:
        return pd.DataFrame(columns=["indice", "valor", "limite", "criterio"])
    # Compatibility adapter for existing Plotly/quality tables only. Financial sums
    # use source rows and Decimal assessment, never these presentation values.
    flagged = pd.to_numeric(df[column].iloc[list(assessment.positions)]).sort_values(ascending=False)
    return pd.DataFrame(
        {
            "indice": flagged.index,
            "valor": flagged.values,
            "limite": float(assessment.threshold),
            "criterio": assessment.criterion,
        }
    )
