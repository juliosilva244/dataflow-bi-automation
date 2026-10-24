from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class DataQualityReport:
    received_records: int
    valid_records: int
    discarded_records: int
    duplicate_records: int
    detected_fields: dict[str, str | None]
    missing_fields: tuple[str, ...] = ()
    rejection_reasons: dict[str, int] = field(default_factory=dict)
    schema_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "registros_recebidos": self.received_records,
            "registros_validos": self.valid_records,
            "registros_descartados": self.discarded_records,
            "registros_duplicados": self.duplicate_records,
            "colunas_detectadas": self.detected_fields,
            "colunas_ausentes": list(self.missing_fields),
            "motivos_rejeicao": self.rejection_reasons,
            "score_schema": self.schema_score,
            "linhas": self.valid_records,
        }


@dataclass(frozen=True)
class ComparisonPeriod:
    current_start: date | None
    current_end: date | None
    previous_start: date | None
    previous_end: date | None
    available: bool

    @property
    def label(self) -> str:
        if not self.available:
            return "Sem período comparativo equivalente disponível"
        return (
            f"Atual: {self.current_start:%d/%m/%Y}–{self.current_end:%d/%m/%Y} | "
            f"Anterior: {self.previous_start:%d/%m/%Y}–{self.previous_end:%d/%m/%Y}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "label": self.label}


@dataclass(frozen=True)
class GrowthMetrics:
    revenue: float
    average_ticket: float
    orders: float
    quantity: float
    stores: float
    comparison_available: bool

    def to_legacy_dict(self) -> dict[str, float | bool]:
        return {
            "crescimento_faturamento": self.revenue,
            "crescimento_ticket": self.average_ticket,
            "crescimento_pedidos": self.orders,
            "crescimento_quantidade": self.quantity,
            "crescimento_lojas": self.stores,
            "base_comparativa_disponivel": self.comparison_available,
        }


@dataclass(frozen=True)
class AnalyticalKPIs:
    total_revenue: float
    average_ticket: float
    total_orders: int
    total_quantity: float
    active_stores: int
    best_store: str
    best_store_value: float
    worst_store: str
    worst_store_performance: float
    top_product: str
    top_product_value: float
    top_product_share: float
    top_day: Any
    top_day_value: float
    ticket_methodology: str

    def to_legacy_dict(self) -> dict[str, Any]:
        return {
            "faturamento_total": self.total_revenue,
            "ticket_medio": self.average_ticket,
            "total_pedidos": self.total_orders,
            "quantidade_total": self.total_quantity,
            "lojas_ativas": self.active_stores,
            "melhor_loja": self.best_store,
            "valor_melhor_loja": self.best_store_value,
            "pior_loja": self.worst_store,
            "desempenho_pior_loja": self.worst_store_performance,
            "produto_top": self.top_product,
            "valor_produto_top": self.top_product_value,
            "participacao_produto_top": self.top_product_share,
            "dia_top": self.top_day,
            "valor_dia_top": self.top_day_value,
            "metodologia_ticket": self.ticket_methodology,
        }

