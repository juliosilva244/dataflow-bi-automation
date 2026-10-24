"""Progressive, local presentation of already-validated financial evidence."""
from __future__ import annotations

import hashlib
import re
from decimal import Decimal, localcontext

from services.anomalies import financial_anomaly_notice
from services.formatter import moeda, moeda_integral


class GroundedAnswer(str):
    """Keep the string API; optional plain metadata is stored only in chat session."""

    def __new__(cls, content, presentation):
        answer = super().__new__(cls, content)
        answer.presentation = presentation
        return answer


def _label(value):
    # Names are rendered as plain table values or escaped Markdown, never HTML.
    return re.sub(r"([\\`*_{}\[\]()<>#+\-.!|$])", r"\\\1", str(value).replace("\n", " "))


def _percent(value):
    if value is None:
        return "Indisponível (denominador zero)"
    if 0 < abs(value) < Decimal("0.005"):
        return "Positiva, inferior a 0,005%" if value > 0 else "Negativa, superior a -0,005%"
    return f"{value:.2f}% (arredondada)".replace(".", ",")


def variation(current, previous, available):
    if not available or previous <= 0:
        return "Indisponível (sem base comparável)"
    with localcontext() as context:
        context.prec = max(50, len(current.as_tuple().digits) + len(previous.as_tuple().digits) + 10)
        value = (current - previous) / previous * 100
        if current > 0 and -100 < value <= Decimal("-99.995"):
            return "Queda próxima de 100%; receita atual positiva"
        return f"{value:+.2f}% (arredondada)".replace(".", ",")


def build_presentations(evidence):
    if "global" not in evidence:
        return {}
    total = evidence["global"]
    scope = evidence.get("scope_label", "Recorte consolidado após filtros")
    periods = evidence["label"]
    warnings = []
    if evidence["anomalies"]["records"]:
        warnings.append(financial_anomaly_notice(evidence["anomalies"]["records"]))

    def item(lead, rows, interpretation="", extra=()):
        return {"lead": lead, "rows": rows, "interpretation": interpretation, "warnings": list(dict.fromkeys([*warnings, *extra]))}

    items = {
        "global.revenue": item("Faturamento consolidado: " + moeda(total["revenue"]), [("Período", scope), ("Registros analisados", str(evidence["records"]))]),
        "global.orders": item("Ticket médio: " + (moeda(total["ticket"]) if total["orders"] else "indisponível"), [("Pedidos/denominador", str(total["orders"])), ("Receita do mesmo recorte", moeda(total["revenue"])), ("Período", scope)], "Ticket exibido arredondado para centavos; a fração de referência está na metodologia."),
    }
    items["global.orders"]["order_label"] = evidence.get("order_label", "Pedidos únicos")
    if evidence["available"]:
        now, before = evidence["current"], evidence["previous"]
        items["period.revenue"] = item("Variação da receita: " + variation(now["revenue"], before["revenue"], True), [("Receita atual", moeda(now["revenue"])), ("Receita anterior", moeda(before["revenue"])), ("Períodos comparados", periods)], "A comparação descreve receita registrada, não sua causa.")
        items["period.ticket"] = item("Comparação do ticket médio", [("Ticket atual", moeda(now["ticket"]) if now["orders"] else "Indisponível"), ("Ticket anterior", moeda(before["ticket"]) if before["orders"] else "Indisponível"), ("Pedidos atuais", str(now["orders"])), ("Pedidos anteriores", str(before["orders"])), ("Períodos", periods)])
    for collection, prefix in (("stores", "store"), ("products", "product")):
        for row in evidence.get(collection, []):
            name = _label(row["name"])
            if prefix == "product":
                lead = ("Produto líder: " if row["rank"] == 1 and not row["tied"] else "Produto entre os líderes (empate): " if row["rank"] == 1 else "Produto: ") + name
                rows = [("Faturamento consolidado", moeda(row["revenue"])), ("Participação no faturamento", _percent(row["share"])), ("Período", scope)]
            else:
                lead = "Situação de " + name
                rows = [("Receita atual", moeda(row["current"]["revenue"]) if evidence["available"] else "Indisponível"), ("Receita anterior", moeda(row["previous"]["revenue"]) if evidence["available"] else "Indisponível"), ("Variação", variation(row["current"]["revenue"], row["previous"]["revenue"], row["trend"] != "unavailable")), ("Receita consolidada da loja", moeda(row["revenue"])), ("Participação no consolidado", _percent(row["share"])), ("Pedidos no recorte da loja", str(row["orders"])), ("Posição por receita consolidada", str(row["rank"]) + (" (empate)" if row["tied"] else "")), ("Períodos da variação", periods)]
            interpretation = {
                "growth": "A receita registrada cresceu nos períodos comparáveis. Isso não demonstra uma causa ou eficiência operacional.",
                "decline": "A receita registrada caiu nos períodos comparáveis. Isso não comprova falha operacional.",
                "unchanged": "A receita registrada não variou entre os períodos comparáveis; isso não comprova estabilidade operacional.",
                "unavailable": "Não há base suficiente para concluir crescimento ou queda dessa entidade.",
            }[row["trend"]]
            if prefix == "product":
                interpretation = "Classificação por receita consolidada, não por quantidade, lucro ou eficiência."
            identifier = prefix + "." + hashlib.sha256(row["name"].encode("utf-8")).hexdigest()[:16]
            items[identifier] = item(lead, rows, interpretation)
            items[identifier]["entity_label"] = row["name"] + (" (empate por receita)" if row["tied"] else "")
            if row["rank"] == 1:
                items.setdefault(prefix + ".leader", items[identifier])
            if row["name"] in evidence.get(collection + "_lowest", []):
                items.setdefault(prefix + ".lowest", items[identifier])
    extremes = evidence["anomalies"]
    with localcontext() as context:
        context.prec = 50
        share = extremes["revenue"] / total["revenue"] * 100 if total["revenue"] else None
    items["quality.extremes"] = item(
        "Principal sinal de revisão: valores monetários extraordinários." if extremes["records"] else "Não há evidência para eleger um maior risco operacional.",
        [("Registros sinalizados", str(extremes["records"])), ("Valor observado nesses registros", moeda(extremes["revenue"])), ("Participação na receita do recorte", _percent(share)), ("Período", scope)],
        "Anomalia estatística é um sinal para conferir a origem. Não é erro comprovado, nem falha operacional demonstrada.",
    )
    census = evidence.get("stores_trends")
    if census:
        items["store.trends"] = item("Todas as lojas tiveram queda registrada." if census["all_declined"] else "Não houve queda comprovada em todas as lojas.", [("Lojas com crescimento", str(census["growth"])), ("Lojas com queda", str(census["decline"])), ("Lojas sem alteração", str(census["unchanged"])), ("Sem comparação disponível", str(census["unavailable"])), ("Períodos", periods)], "Censo de todas as lojas do recorte, não apenas do ranking exibido.")
    return items


def reconciliation_rows(evidence):
    if "global" not in evidence:
        return []
    rows = []
    for label, key in (("Consolidado após filtros", "global"), ("Período atual", "current"), ("Período anterior", "previous"), ("Fora das janelas", "outside_periods")):
        amounts = evidence[key]
        rows.append({"Escopo": label, "Receita integral": moeda_integral(amounts["revenue"]), "Registros": str(amounts["records"]), "Denominador do ticket": str(amounts["orders"]) if "orders" in amounts else "Ver escopo dos KPIs"})
    return rows


def answer_presentation(catalog, fact_ids, limitation_ids):
    presentations = catalog.get("_presentations", {})
    priority = list(dict.fromkeys([*catalog.get("required_facts", []), *fact_ids]))
    # A required alias may be fulfilled by a selected identical factual statement.
    selected = [key for key in priority if key in presentations and catalog["facts"].get(key) in {catalog["facts"][item] for item in fact_ids}]
    if not fact_ids:
        lead = "Não há evidência suficiente para responder a essa pergunta."
        rows, interpretation, warnings = [], "Os indicadores solicitados não foram inventados.", []
    elif selected:
        primary = presentations[selected[0]]
        lead, rows, interpretation = primary["lead"], list(primary["rows"]), primary["interpretation"]
        warnings = list(dict.fromkeys(warning for key in selected for warning in presentations[key]["warnings"]))
        if catalog.get("_intent") == "summary":
            sentences = []
            rows = []
            if "global.revenue" in selected:
                rows.append(("Faturamento consolidado", presentations["global.revenue"]["lead"].split(": ", 1)[1]))
                rows.extend(presentations["global.revenue"]["rows"])
                heading = presentations["global.revenue"]["lead"]
                sentences.append("Resumo executivo: " + heading[0].lower() + heading[1:] + ".")
            if "global.orders" in selected:
                rows.append(("Ticket médio (mesmo recorte)", presentations["global.orders"]["lead"].split(": ", 1)[1]))
                rows.append(presentations["global.orders"]["rows"][0])
                rows.append(("Denominação do denominador", presentations["global.orders"]["order_label"]))
            if "period.revenue" in selected:
                rows.append(("Variação entre períodos", presentations["period.revenue"]["lead"].split(": ", 1)[1]))
                rows.append(("Janelas da variação", presentations["period.revenue"]["rows"][-1][1]))
                sentences.append(presentations["period.revenue"]["lead"] + ".")
            for identifier, label in (("store.leader", "Loja líder por receita"), ("product.leader", "Produto líder por receita")):
                if identifier in selected:
                    rows.append((label, presentations[identifier]["entity_label"]))
            if "store.trends" in selected:
                census = presentations["store.trends"]
                rows.append(("Censo de lojas", "; ".join(label + ": " + value for label, value in census["rows"][:-1])))
                interpretation = census["lead"]
                sentences.append("Comparação das lojas: " + "; ".join(label + ": " + value for label, value in census["rows"][:2]) + ".")
            rows = list(dict.fromkeys(rows))
            lead = " ".join(sentences)
    else:
        lead, rows, interpretation, warnings = catalog["facts"][fact_ids[0]], [], "", []
    if catalog.get("_intent") == "orders" and "global.orders" in selected:
        lead = presentations["global.orders"]["order_label"] + " no recorte: " + dict(presentations["global.orders"]["rows"])["Pedidos/denominador"]
    return {
        "version": 1, "lead": lead, "rows": rows, "interpretation": interpretation,
        "warnings": warnings,
        "evidence": list(dict.fromkeys(catalog["facts"][key] for key in fact_ids)),
        "methodology": list(dict.fromkeys(catalog["limitations"][key] for key in limitation_ids)),
        "reconciliation": catalog.get("_reconciliation", []) if catalog.get("_intent") == "summary" and fact_ids else [],
    }
