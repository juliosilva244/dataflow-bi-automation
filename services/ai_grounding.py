"""A model selects fact IDs; only trusted local evidence supplies factual prose/numbers."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from decimal import Decimal

from services.ai_evidence import describe_change
from services.ai_presentation import (
    GroundedAnswer,
    answer_presentation,
    build_presentations,
    reconciliation_rows,
)
from services.errors import AIResponseValidationError
from services.formatter import moeda

CONTRACT = "DATAFLOW_FACT_SELECTION_V1"


def _name(value):
    return re.sub(r"([\\`*_{}\[\]()<>#+\-.!|$])", r"\\\1", str(value).replace("\n", " "))


def _share(value):
    if value is None:
        return "indisponível: receita total igual a zero"
    if 0 < value < Decimal("0.0001"):
        return "inferior a 0,0001% (positiva, não zero)"
    return f"{value:.4f}% (arredondada)".replace(".", ",")


def _ticket(amounts):
    return moeda(amounts["ticket"]) if amounts["orders"] else "indisponível (sem denominador de pedidos)"


def _required_facts(question, evidence, facts):
    text = "".join(char for char in unicodedata.normalize("NFKD", str(question).casefold()) if not unicodedata.combining(char))
    required = []
    for collection, prefix in (("stores", "store"), ("products", "product")):
        for row in evidence.get(collection, []):
            name = row["name"].casefold()
            if len(name) >= 3 and re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", str(question).casefold()):
                required.append(prefix + "." + hashlib.sha256(row["name"].encode("utf-8")).hexdigest()[:16])
    if "loja" in text or "unidade" in text:
        required.append("store.trends")
        if any(word in text for word in ("pior", "menor")):
            required.append("store.lowest")
        elif any(word in text for word in ("melhor", "maior", "lider")):
            required.append("store.leader")
    if any(word in text for word in ("produto", "item")) and any(word in text for word in ("lider", "mais", "maior", "melhor", "top")):
        required.append("product.leader")
    if "resumo" in text:
        required.extend(["global.revenue", "global.orders", "period.revenue", "store.trends", "store.leader", "product.leader", "period.coverage"])
    if "risco" in text:
        required.extend(["quality.extremes", "store.trends"])
    if not required:
        if "ticket" in text or "pedido" in text:
            required.append("global.orders")
        elif "faturamento" in text or "receita" in text:
            required.append("period.revenue" if any(word in text for word in ("variacao", "crescimento", "queda")) else "global.revenue")
    return [key for key in dict.fromkeys(required) if key in facts]


def build_fact_catalog(evidence, question=""):
    facts = {}
    limitations = {
        "evidence.limits": "Os dados não comprovam causalidade, lucro, eficiência, falha operacional nem ausência de riscos. Fatos descrevem somente os indicadores e o recorte disponíveis.",
        "evidence.insufficient": "Não há evidência quantitativa suficiente para responder ao que foi perguntado. Não foram criados números, previsões ou causas.",
        "method.ticket": "Ticket médio = receita do mesmo escopo / pedidos únicos desse escopo; na ausência do campo de pedido, usa registros. Pedidos únicos por loja/produto não são necessariamente aditivos. Ticket exibido é arredondado para centavos.",
        "method.ranking": "Maior/menor loja significa exclusivamente maior/menor receita consolidada do recorte. Empates são identificados; ordem alfabética é apenas desempate de apresentação, não superioridade operacional.",
        "privacy.session": "Pseudônimos são estáveis nesta sessão. Não são identificadores globais nem anonimização completa de texto livre.",
        "risk.taxonomy": "Queda de receita é uma comparação observada; anomalia estatística é um sinal de revisão, não erro confirmado. Inconsistência de dados exige divergência verificada. Ausência de evidência não é estabilidade. Risco operacional comprovado exige evidência operacional que este catálogo não contém; exposição apenas hipotética não é apresentada como fato.",
    }
    if "global" not in evidence:
        return {"facts": facts, "limitations": limitations}
    total = evidence["global"]
    facts["global.revenue"] = f"Receita global consolidada do recorte: {moeda(total['revenue'])}, com {evidence['records']} registros válidos analisados. Período: {evidence.get('scope_label', 'não informado')}."
    facts["global.orders"] = f"{evidence.get('order_label', 'Pedidos do recorte')}: {total['orders']}; ticket médio global calculado: {_ticket(total)}. Denominador: {evidence.get('order_method', 'pedidos do mesmo recorte')}."
    if evidence["available"]:
        now, before = evidence["current"], evidence["previous"]
        facts["period.revenue"] = (
            f"{evidence['label']}. Receita atual: {moeda(now['revenue'])}; anterior: {moeda(before['revenue'])}. "
            f"{describe_change(now['revenue'], before['revenue'], True)}"
        )
        facts["period.ticket"] = (
            f"{evidence['label']}. Ticket atual: {_ticket(now)}, pedidos atuais: {now['orders']}; "
            f"ticket anterior: {_ticket(before)}, pedidos anteriores: {before['orders']}. "
            f"{describe_change(now['ticket'], before['ticket'], True) if now['orders'] and before['orders'] else 'Variação indisponível: sem denominador de pedidos nos dois períodos.'}"
        )
        outside = evidence["outside_periods"]
        facts["period.coverage"] = f"Fora dos dois períodos equivalentes: {outside['records']} registros e {moeda(outside['revenue'])}. Permanecem nos consolidados, não foram descartados."
    else:
        limitations["period.unavailable"] = evidence["label"] + " Não há comparação temporal equivalente comprovada."
    trends = evidence.get("stores_trends")
    if trends:
        conclusion = "Todas as lojas tiveram queda de receita registrada nos mesmos períodos." if trends["all_declined"] else "Não é correto concluir que todas as lojas tiveram queda."
        facts["store.trends"] = (
            f"Censo de TODAS as {trends['total']} lojas do recorte, não apenas as exibidas no resumo. {evidence['label']}. "
            f"Crescimento: {trends['growth']}; queda: {trends['decline']}; sem alteração: {trends['unchanged']}; "
            f"comparação indisponível: {trends['unavailable']}. {conclusion} "
            "Comparação por loja exige registros em ambos os períodos e base anterior positiva; não comprova causa ou risco operacional."
        )
    for collection, prefix in (("stores", "store"), ("products", "product")):
        rows = evidence.get(collection, [])
        for row in rows:
            identifier = prefix + "." + hashlib.sha256(row["name"].encode("utf-8")).hexdigest()[:16]
            text = (
                f"{_name(row['name'])}: posição {row['rank']} por receita consolidada"
                f"{' (empate)' if row['tied'] else ''}; receita {moeda(row['revenue'])}; "
                f"participação na receita global do MESMO recorte: {_share(row['share'])}; "
                f"pedidos desse escopo: {row['orders']}."
            )
            if evidence["available"]:
                text += (
                    f" {evidence['label']}. Receita específica atual: {moeda(row['current']['revenue'])}; "
                    f"anterior: {moeda(row['previous']['revenue'])}. "
                    f"{describe_change(row['current']['revenue'], row['previous']['revenue'], True)}"
                )
            facts[identifier] = text
            if row["rank"] == 1:
                facts.setdefault(prefix + ".leader", text)
        lowest = evidence.get(collection + "_lowest", [])
        for row in rows:
            if row["name"] in lowest:
                facts[prefix + ".lowest"] = facts[prefix + "." + hashlib.sha256(row["name"].encode("utf-8")).hexdigest()[:16]]
                break
        limitations[prefix + ".coverage"] = f"Resumo limitado: {evidence.get(collection + '_omitted', 0)} entidades omitidas. Não inferir desempenho de entidades ausentes."
    anomalies = evidence["anomalies"]
    facts["quality.extremes"] = (
        f"Possíveis anomalias monetárias: {anomalies['records']} registros, soma {moeda(anomalies['revenue'])}. "
        "Critério: valor acima do maior limite entre Q3 + 10 × IQR e 1.000 × mediana positiva. "
        "Sinal de revisão da qualidade, não erro confirmado ou evidência de falha operacional. Valores mantidos nos cálculos."
    )
    quality = evidence["quality"]
    keys = ("registros_recebidos", "registros_validos", "registros_descartados", "registros_duplicados")
    if all(key in quality for key in keys):
        facts["quality.records"] = (
            f"Qualidade na origem carregada (não confundir com o recorte filtrado): recebidos {quality[keys[0]]}; "
            f"válidos {quality[keys[1]]}; descartados {quality[keys[2]]}; duplicados {quality[keys[3]]}."
        )
    limitations["source.scope"] = "Fonte: dados canônicos validados no recorte após filtros. Receita consolidada não é a receita de apenas um dos períodos comparativos; valores integrais e fração do ticket estão no detalhamento de escopos."
    intent = "summary" if "resumo" in str(question).casefold() else "risk" if "risco" in str(question).casefold() else "orders" if "pedido" in str(question).casefold() and "ticket" not in str(question).casefold() else "direct"
    return {"facts": facts, "limitations": limitations, "required_facts": _required_facts(question, evidence, facts), "_presentations": build_presentations(evidence), "_reconciliation": reconciliation_rows(evidence), "_intent": intent}


def render_grounded_selection(raw_response, catalog):
    """Reject free text/unknown claims, never manufacture a fallback provider answer."""
    try:
        if not isinstance(raw_response, str) or len(raw_response) > 32_000:
            raise ValueError()

        def unique_pairs(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError()
                result[key] = value
            return result

        selection = json.loads(raw_response, object_pairs_hook=unique_pairs)
        if not isinstance(selection, dict) or set(selection) != {"facts", "limitations"}:
            raise ValueError()
        for key in ("facts", "limitations"):
            identifiers = selection[key]
            if not isinstance(identifiers, list) or len(identifiers) > 12:
                raise ValueError()
            if any(not isinstance(item, str) or item not in catalog[key] for item in identifiers):
                raise ValueError()
            if len(set(identifiers)) != len(identifiers):
                raise ValueError()
        if not selection["facts"] and not selection["limitations"]:
            raise ValueError()
        selected_text = {catalog["facts"][key] for key in selection["facts"]}
        if any(key.startswith("store.") for key in selection["facts"]) and "store.trends" in catalog["facts"]:
            selected_text.add(catalog["facts"]["store.trends"])
        if any(catalog["facts"][key] not in selected_text for key in catalog.get("required_facts", [])):
            raise ValueError()
    except (ValueError, TypeError, RecursionError):
        raise AIResponseValidationError() from None
    fact_ids = list(selection["facts"])
    if any(key.startswith("store.") for key in fact_ids) and "store.trends" in catalog["facts"] and "store.trends" not in fact_ids:
        fact_ids.append("store.trends")
    required = ["evidence.limits", "method.ticket", "method.ranking"] if selection["facts"] else ["evidence.limits"]
    chosen = list(dict.fromkeys([*selection["limitations"], *required]))
    if any(key.startswith(("store.", "period.", "quality.")) for key in fact_ids):
        chosen.append("risk.taxonomy")
    if "source.scope" in catalog["limitations"]:
        chosen.append("source.scope")
    presentation = answer_presentation(catalog, fact_ids, list(dict.fromkeys(chosen)))
    lines = [presentation["lead"]]
    lines.extend(f"- {label}: {value}" for label, value in presentation["rows"])
    lines.extend([presentation["interpretation"], *presentation["warnings"], "", "### Evidências verificadas"])
    lines.extend("- " + text for text in presentation["evidence"])
    lines.extend(["", "### Limitações e metodologia"])
    lines.extend("- " + text for text in presentation["methodology"])
    return GroundedAnswer("\n".join(lines), presentation)
