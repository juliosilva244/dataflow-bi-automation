"""Bounded, verifiable AI context; never changes the dashboard's analytical state."""
from __future__ import annotations

from decimal import Decimal, localcontext

import pandas as pd

from domain.periods import split_equivalent_periods
from services.anomalies import ANOMALY_CRITERION, assess_monetary_anomalies
from services.errors import AIPayloadError
from services.metrics_engine import exact_decimal_sum, exact_revenue_ranking, safe_count_unique


def describe_change(current: Decimal, previous: Decimal, available: bool) -> str:
    if not available:
        return "Indisponível: não há dois períodos equivalentes com registros."
    if previous <= 0:
        return "Indisponível: base anterior não positiva; não interpretar como crescimento de 0%."
    if current == 0:
        return "-100% exatos: valor atual igual a zero. Isso não demonstra uma causa."
    with localcontext() as context:
        context.prec = max(50, len(current.as_tuple().digits) + len(previous.as_tuple().digits) + 10)
        change = (current - previous) / previous * 100
        if current > 0 and -100 < change < Decimal("-99.995"):
            return (
                "Queda próxima de 100%, NÃO igual a -100% exatos: valor atual positivo. "
                "O arredondamento não significa receita zerada nem prova paralisação da operação."
            )
        return f"{change:.4f}% (arredondado; fórmula: (atual - anterior) / anterior × 100)."


def known_identifiers(state) -> dict[str, str]:
    """Local inventory only: includes non-leading entities mentioned in questions."""
    identifiers = {}
    for field, prefix in (("melhor_loja", "Loja"), ("pior_loja", "Loja"), ("produto_top", "Produto")):
        value = state.get(field)
        if value and str(value) != "Não informado":
            identifiers[str(value)] = prefix
    frame, columns = state.get("prepared_df"), state.get("columns")
    if isinstance(frame, pd.DataFrame) and columns is not None:
        for attribute, prefix in (("loja", "Loja"), ("produto", "Produto")):
            column = getattr(columns, attribute, None)
            if column and column in frame:
                for value in frame[column].dropna().unique():
                    identifiers.setdefault(str(value), prefix)
    return identifiers


def scope_amounts(rows, columns):
    revenue = exact_decimal_sum(rows[columns.faturamento])
    orders = safe_count_unique(rows, columns.pedido) if columns.pedido else len(rows)
    with localcontext() as context:
        # Keep the established 28-digit ticket representation for ordinary values;
        # enlarge it only when integer/cents digits would otherwise be lost.
        context.prec = max(28, revenue.adjusted() + 1 + max(0, -revenue.as_tuple().exponent) + len(str(orders)) + 2)
        return {"revenue": revenue, "orders": orders, "ticket": revenue / orders if orders else Decimal(0), "records": len(rows)}


def scope_summary(state):
    frame, columns = state.get("prepared_df"), state.get("columns")
    if not isinstance(frame, pd.DataFrame) or not getattr(columns, "faturamento", None):
        return None
    current, previous, period = split_equivalent_periods(frame, columns.data)
    if period.previous_start is not None:
        dates = frame[columns.data]
        outside = frame[dates.isna() | (dates < pd.Timestamp(period.previous_start)) | (dates >= pd.Timestamp(period.current_end) + pd.Timedelta(days=1))]
    else:
        outside = frame[frame[columns.data].isna()] if columns.data else frame.iloc[0:0]
    return {
        "global": scope_amounts(frame, columns), "current": scope_amounts(current, columns),
        "previous": scope_amounts(previous, columns), "outside": scope_amounts(outside, columns),
        "label": period.label, "available": period.available,
        "order_method": "pedidos únicos do campo Pedido" if columns.pedido else "registros como proxy de pedidos (não há campo Pedido)",
    }


def _trend(current, previous, current_records, previous_records, available):
    if not available or not current_records or not previous_records or previous <= 0:
        return "unavailable"
    return "growth" if current > previous else "decline" if current < previous else "unchanged"


def build_ai_evidence(state, question="") -> dict:
    frame, columns = state.get("prepared_df"), state.get("columns")
    column = getattr(columns, "faturamento", None)
    if not isinstance(frame, pd.DataFrame) or not column or column not in frame:
        return _build_ai_evidence(state, question)
    numbers = [Decimal(str(value)) for value in frame[column].dropna()]
    finite = [value for value in numbers if value.is_finite()]
    with localcontext() as context:
        # Decimal arithmetic (including subtraction) otherwise uses only 28 digits.
        context.prec = max(50, max((value.adjusted() + 1 for value in finite), default=1) + max((-value.as_tuple().exponent for value in finite), default=0) + len(str(len(finite))) + 20)
        return _build_ai_evidence(state, question)


def _build_ai_evidence(state, question="") -> dict:
    frame, columns = state.get("prepared_df"), state.get("columns")
    revenue_column = getattr(columns, "faturamento", None)
    if not isinstance(frame, pd.DataFrame) or not revenue_column or revenue_column not in frame:
        return {"available": False, "label": "Sem dados canônicos para comprovar a comparação temporal.", "stores": []}
    current, previous, period = split_equivalent_periods(frame, getattr(columns, "data", None))

    def amounts(rows):
        return scope_amounts(rows, columns)

    result = {
        "available": period.available, "label": period.label,
        "current": amounts(current), "previous": amounts(previous), "stores": [],
    }
    result["global"] = amounts(frame)
    dates = frame[columns.data].dropna() if columns.data else pd.Series(dtype="datetime64[ns]")
    result["scope_label"] = f"{dates.min():%d/%m/%Y}–{dates.max():%d/%m/%Y} (recorte após filtros)" if not dates.empty else "Período não disponível"
    result["records"] = len(frame)
    result["order_label"] = "Pedidos únicos" if columns.pedido else "Registros (proxy de pedidos)"
    result["order_method"] = "pedidos únicos do campo Pedido" if columns.pedido else "registros como proxy de pedidos (não há campo Pedido)"
    result["quality"] = dict(state.get("quality", {}))
    extremes = assess_monetary_anomalies(frame, revenue_column)
    result["anomalies"] = {"records": len(extremes.positions), "revenue": exact_decimal_sum(frame[revenue_column].iloc[list(extremes.positions)]), "criterion": ANOMALY_CRITERION}
    result["outside_periods"] = {
        "records": len(frame) - len(current) - len(previous),
        "revenue": exact_decimal_sum(frame[revenue_column]) - result["current"]["revenue"] - result["previous"]["revenue"],
    }
    for attribute, collection, limit in (("loja", "stores", 8), ("produto", "products", 8)):
        dimension = getattr(columns, attribute, None)
        if not dimension or dimension not in frame:
            result[collection] = []
            continue
        ordered = exact_revenue_ranking(frame, dimension, revenue_column)
        totals = dict(ordered)
        ranking = sorted(totals, key=totals.get, reverse=True)
        current_totals = dict(exact_revenue_ranking(current, dimension, revenue_column))
        previous_totals = dict(exact_revenue_ranking(previous, dimension, revenue_column))
        current_counts = {str(name): len(rows) for name, rows in current.groupby(dimension, dropna=False)}
        previous_counts = {str(name): len(rows) for name, rows in previous.groupby(dimension, dropna=False)}
        trends = {
            name: _trend(current_totals.get(name, Decimal(0)), previous_totals.get(name, Decimal(0)), current_counts.get(name, 0), previous_counts.get(name, 0), period.available)
            for name in ranking
        }
        counts = {kind: sum(value == kind for value in trends.values()) for kind in ("growth", "decline", "unchanged", "unavailable")}
        result[collection + "_trends"] = {**counts, "total": len(ranking), "all_declined": bool(ranking) and counts["decline"] == len(ranking)}
        mentioned = [name for name in ranking if name.casefold() in str(question).casefold()]
        growing = [name for name in ranking if trends[name] == "growth"]
        priorities = [*mentioned[:4], *ranking[:1], *ranking[-1:], *growing[:1], *ranking[:4], *ranking[-2:]]
        selected = list(dict.fromkeys(priorities))[:limit]
        result[collection] = []
        for name in selected:
            result[collection].append({
                "name": name, "revenue": totals[name],
                "orders": amounts(frame[frame[dimension].astype(str) == name])["orders"],
                "trend": trends[name],
                "rank": 1 + sum(value > totals[name] for value in totals.values()),
                "tied": sum(value == totals[name] for value in totals.values()) > 1,
                "share": totals[name] / result["global"]["revenue"] * 100 if result["global"]["revenue"] else None,
                "current": amounts(current[current[dimension].astype(str) == name]),
                "previous": amounts(previous[previous[dimension].astype(str) == name]),
            })
        result[collection + "_omitted"] = len(totals) - len(selected)
        result[collection + "_total"] = exact_decimal_sum(pd.Series(totals.values(), dtype=object))
        result[collection + "_count"] = len(totals)
        result[collection + "_leaders"] = [name for name, value in ordered if value == ordered[0][1]] if ordered else []
        result[collection + "_lowest"] = [name for name, value in ordered if value == ordered[-1][1]] if ordered else []
    return result


def validate_ai_evidence(state, evidence):
    """Fail closed before external calls if critical aggregates disagree."""
    if "global" not in evidence:
        return
    total = evidence["global"]["revenue"]
    pieces = [evidence[key]["revenue"] for key in ("current", "previous", "outside_periods")]
    if not total.is_finite() or exact_decimal_sum(pd.Series(pieces)) != total:
        raise AIPayloadError()
    for collection in ("stores", "products"):
        if evidence.get(collection + "_total", total) != total:
            raise AIPayloadError()
        census = evidence.get(collection + "_trends")
        if census is not None:
            count = evidence.get(collection + "_count", 0)
            if sum(census[key] for key in ("growth", "decline", "unchanged", "unavailable")) != count or census["all_declined"] != (count > 0 and census["decline"] == count):
                raise AIPayloadError()
    for field, expected in (("faturamento_total_exato", total), ("ticket_medio_exato", evidence["global"]["ticket"])):
        if field in state and Decimal(str(state[field])) != expected:
            raise AIPayloadError()
    if "total_pedidos" in state and Decimal(str(state["total_pedidos"])) != evidence["global"]["orders"]:
        raise AIPayloadError()
    if "lojas_ativas" in state and Decimal(str(state["lojas_ativas"])) != evidence.get("stores_count", 0):
        raise AIPayloadError()
    quality = evidence["quality"]
    counters = ("registros_recebidos", "registros_validos", "registros_descartados", "registros_duplicados")
    if all(key in quality for key in counters):
        values = [quality[key] for key in counters]
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values):
            raise AIPayloadError()
        received, valid, discarded, duplicated = values
        if valid + discarded != received or duplicated > discarded or evidence["records"] > valid:
            raise AIPayloadError()
    for field, leaders in (("melhor_loja", "stores_leaders"), ("pior_loja", "stores_lowest"), ("produto_top", "products_leaders")):
        if field in state and evidence.get(leaders) and state[field] not in evidence[leaders]:
            raise AIPayloadError()


def evidence_text(evidence) -> str:
    if not evidence["available"]:
        return evidence["label"] + " Variações percentuais não comprovadas; não concluir crescimento ou ausência de riscos."
    current, previous = evidence["current"], evidence["previous"]
    outside = evidence["outside_periods"]
    lines = [
        evidence["label"],
        f"Fora dos dois períodos equivalentes: {outside['records']} registros, receita exata R$ {outside['revenue']}. "
        "Permanecem nos totais consolidados; não foram descartados. Não confundir total do recorte com receita de um período.",
        f"Receita atual exata: R$ {current['revenue']}; anterior exata: R$ {previous['revenue']}.",
        f"Variação da receita: {describe_change(current['revenue'], previous['revenue'], True)}",
        f"Pedidos atuais: {current['orders']}; anteriores: {previous['orders']}.",
        f"Ticket atual: R$ {current['ticket']}; anterior: R$ {previous['ticket']}.",
        f"Variação do ticket: {describe_change(current['ticket'], previous['ticket'], True)}",
        "Ticket = receita / pedidos únicos, ou registros quando não há campo de pedido.",
        "LOJAS (ranking somente por faturamento, não por eficiência, lucro ou risco):",
    ]
    for store in evidence["stores"]:
        now, before = store["current"], store["previous"]
        lines.append(
            f"{store['name']!r}: receita consolidada exata R$ {store['revenue']}; "
            f"receita atual R$ {now['revenue']}; anterior R$ {before['revenue']}; "
            f"pedidos atuais {now['orders']}; anteriores {before['orders']}; "
            f"variação: {describe_change(now['revenue'], before['revenue'], True)}"
        )
    lines.append(f"Lojas omitidas deste resumo limitado: {evidence.get('stores_omitted', 0)}.")
    return "\n".join(lines)
