from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

import pandas as pd


# =============================================================================
# DataFlow BI Automation
# services/exporter.py
#
# Exportador premium para Excel e PDF.
# Objetivos:
# - Gerar Excel analítico com múltiplas abas.
# - Gerar PDF executivo mais limpo, legível e profissional.
# - Traduzir nomes técnicos para nomes de negócio.
# - Formatar moeda, percentuais e datas.
# - Evitar PDF com aparência de "dump de DataFrame".
# =============================================================================


SHEET_NAME_MAP: dict[str, str] = {
    "Dados": "Dados",
    "Resumo": "Resumo",
    "Base Preparada": "Base Preparada",
    "KPIs": "KPIs",
    "Qualidade": "Qualidade",
    "Schema": "Schema",
    "revenue_by_month": "Faturamento por mês",
    "revenue_by_store": "Faturamento por loja",
    "top_products": "Top produtos",
    "revenue_by_day": "Faturamento por dia",
    "primary_dimension_summary": "Resumo dimensão principal",
    "secondary_dimension_summary": "Resumo dimensão secundária",
    "secondary_metrics": "Métricas secundárias",
    "kpi_cards": "Cards de KPI",
}


PDF_SECTION_TITLE_MAP: dict[str, str] = {
    "Dados": "Dados",
    "Resumo": "Resumo da análise",
    "KPIs": "Indicadores executivos",
    "Qualidade": "Qualidade e leitura da base",
    "Schema": "Schema detectado",
    "revenue_by_month": "Faturamento por mês",
    "revenue_by_store": "Faturamento por loja",
    "top_products": "Produtos com maior faturamento",
    "revenue_by_day": "Faturamento por dia",
    "primary_dimension_summary": "Resumo por dimensão principal",
    "secondary_dimension_summary": "Resumo por dimensão secundária",
    "secondary_metrics": "Métricas secundárias detectadas",
    "kpi_cards": "Cards executivos configurados",
    "Base Preparada": "Base preparada",
}


COLUMN_NAME_MAP: dict[str, str] = {
    "faturamento_total": "Faturamento Total",
    "ticket_medio": "Ticket Médio",
    "total_pedidos": "Registros Analisados",
    "quantidade_total": "Quantidade Total",
    "lojas_ativas": "Lojas Ativas",
    "primary_dimension_count": "Qtd. Dimensão Principal",
    "secondary_dimension_count": "Qtd. Dimensão Secundária",
    "category_dimension_count": "Qtd. Categorias",
    "linhas": "Linhas",
    "colunas": "Colunas",
    "colunas_detectadas": "Colunas Detectadas",
    "colunas_ausentes": "Colunas Ausentes",
    "score_schema": "Score do Schema",
    "schema_domain": "Domínio",
    "schema_confidence": "Confiança do Schema",
    "metric_confidence": "Confiança da Métrica",
    "name": "Coluna",
    "role": "Papel",
    "confidence": "Confiança",
    "dtype": "Tipo",
    "unique_count": "Valores Únicos",
    "unique_ratio": "Taxa de Unicidade",
    "null_ratio": "Taxa de Nulos",
    "sample_values": "Amostras",
    "periodo": "Período",
    "faturamento": "Faturamento",
    "loja": "Loja",
    "produto": "Produto",
    "data": "Data",
    "dimensao": "Dimensão",
    "valor": "Valor",
    "icon": "Ícone",
    "title": "Título",
    "metric_key": "Métrica",
    "growth_key": "Crescimento",
    "badge": "Categoria",
    "featured": "Destaque",
}


METRIC_LABEL_MAP: dict[str, str] = {
    "faturamento_total": "Faturamento Total",
    "ticket_medio": "Ticket Médio",
    "total_pedidos": "Registros Analisados",
    "quantidade_total": "Quantidade Total",
    "lojas_ativas": "Lojas Ativas",
    "primary_dimension_count": "Qtd. Dimensão Principal",
    "secondary_dimension_count": "Qtd. Dimensão Secundária",
    "category_dimension_count": "Qtd. Categorias",
    "top_primary_dimension": "Top Dimensão Principal",
    "top_secondary_dimension": "Top Dimensão Secundária",
    "domain": "Domínio Detectado",
}


CURRENCY_COLUMNS = {
    "faturamento",
    "faturamento_total",
    "ticket_medio",
    "preco_unitario",
    "preço_unitario",
    "preço unitário",
    "preco unitario",
    "total",
    "receita",
    "vendas",
}

COUNT_COLUMNS = {
    "total_pedidos",
    "quantidade_total",
    "lojas_ativas",
    "primary_dimension_count",
    "secondary_dimension_count",
    "category_dimension_count",
    "registros",
    "linhas",
    "colunas",
    "valores_unicos",
    "unique_count",
}

PERCENT_COLUMNS = {
    "score_schema",
    "schema_confidence",
    "metric_confidence",
    "confidence",
    "unique_ratio",
    "null_ratio",
}


def _safe_sheet_name(name: str) -> str:
    cleaned = (
        str(name)
        .replace("/", "-")
        .replace("\\", "-")
        .replace("*", "-")
        .replace("?", "-")
        .replace("[", "(")
        .replace("]", ")")
        .replace(":", "-")
        .strip()
    )
    return cleaned[:31] or "Dados"


def _display_sheet_name(name: str) -> str:
    return SHEET_NAME_MAP.get(str(name), str(name).replace("_", " ").title())


def _display_section_title(name: str) -> str:
    return PDF_SECTION_TITLE_MAP.get(str(name), str(name).replace("_", " ").title())


def _display_column_name(name: Any) -> str:
    key = str(name)
    return COLUMN_NAME_MAP.get(key, key.replace("_", " ").title())


def _normalize_key(value: Any) -> str:
    return str(value).strip().lower().replace(" ", "_")


def _is_missing(value: Any) -> bool:
    if value is None:
        return True

    try:
        if pd.isna(value):
            return True
    except Exception:
        pass

    text = str(value).strip().lower()
    return text in {"", "nan", "none", "null", "nat"}


def _format_number(value: Any, decimals: int = 2) -> str:
    if _is_missing(value):
        return "-"

    try:
        number = float(value)
        return f"{number:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(value)


def _format_integer(value: Any) -> str:
    if _is_missing(value):
        return "-"

    try:
        number = float(value)
        return f"{number:,.0f}".replace(",", ".")
    except Exception:
        return str(value)


def _format_currency(value: Any) -> str:
    if _is_missing(value):
        return "-"

    try:
        number = float(value)
        return f"R$ {number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(value)


def _format_percent(value: Any) -> str:
    if _is_missing(value):
        return "-"

    try:
        number = float(value)

        if 0 <= number <= 1:
            number *= 100

        return f"{number:,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(value)


def _format_date(value: Any) -> str:
    if _is_missing(value):
        return "-"

    try:
        parsed = pd.to_datetime(value)
        return parsed.strftime("%d/%m/%Y")
    except Exception:
        return str(value)


def _format_cell(value: Any, column_name: Any = "") -> str:
    normalized_column = _normalize_key(column_name)

    if _is_missing(value):
        return "-"

    # Se o valor já veio pré-formatado como texto executivo, não tente converter de novo.
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("R$ ") or text.endswith("%") or "/" in text:
            return text

    if "data" in normalized_column or "periodo" in normalized_column or "date" in normalized_column:
        return _format_date(value)

    if normalized_column in COUNT_COLUMNS or any(
        token in normalized_column
        for token in ["quantidade", "qtd", "count", "registros", "linhas", "colunas"]
    ):
        return _format_integer(value)

    if normalized_column in CURRENCY_COLUMNS or any(
        token in normalized_column
        for token in ["faturamento", "receita", "ticket", "preco", "preço"]
    ):
        return _format_currency(value)

    if normalized_column in PERCENT_COLUMNS or any(
        token in normalized_column for token in ["ratio", "confidence", "score", "taxa"]
    ):
        return _format_percent(value)

    if isinstance(value, float):
        return _format_number(value)

    return str(value)


def _rename_columns_for_display(df: pd.DataFrame) -> pd.DataFrame:
    renamed = df.copy()
    renamed.columns = [_display_column_name(col) for col in renamed.columns]
    return renamed


def _format_dataframe_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    export_df = df.copy()

    for column in export_df.columns:
        if pd.api.types.is_datetime64_any_dtype(export_df[column]):
            export_df[column] = export_df[column].dt.strftime("%d/%m/%Y")

    return export_df


def _format_dataframe_for_pdf(df: pd.DataFrame, section_key: str = "") -> pd.DataFrame:
    preview_df = df.copy()
    normalized_section = _normalize_key(section_key)

    for column in preview_df.columns:
        normalized_column = _normalize_key(column)

        # Tabelas de resumo por dimensão representam faturamento agregado.
        # Nelas, a coluna "valor" deve ser exibida como moeda.
        if normalized_section in {
            "primary_dimension_summary",
            "secondary_dimension_summary",
            "revenue_by_store",
            "top_products",
            "revenue_by_month",
            "revenue_by_day",
        } and normalized_column == "valor":
            preview_df[column] = preview_df[column].map(_format_currency)
        else:
            preview_df[column] = preview_df[column].map(lambda value: _format_cell(value, column))

    preview_df = _rename_columns_for_display(preview_df)
    return preview_df


def _extract_dataframes(data: Any) -> dict[str, pd.DataFrame]:
    sheets: dict[str, pd.DataFrame] = {}

    if isinstance(data, pd.DataFrame):
        sheets["Dados"] = data
        return sheets

    if isinstance(data, dict):
        prepared_df = data.get("prepared_df")
        if isinstance(prepared_df, pd.DataFrame) and not prepared_df.empty:
            sheets["Base Preparada"] = prepared_df

        metricas = data.get("metricas")
        if isinstance(metricas, dict):
            simple_metrics = {
                key: value
                for key, value in metricas.items()
                if not isinstance(value, (pd.DataFrame, dict, list, tuple))
            }

            if simple_metrics:
                readable_metrics = {
                    METRIC_LABEL_MAP.get(key, key): value
                    for key, value in simple_metrics.items()
                }
                sheets["KPIs"] = pd.DataFrame([readable_metrics])

        quality = data.get("quality")
        if isinstance(quality, dict):
            sheets["Qualidade"] = pd.DataFrame([quality])

        schema = data.get("schema")
        if isinstance(schema, dict):
            schema_rows = schema.get("columns", [])

            if schema_rows:
                sheets["Schema"] = pd.DataFrame(schema_rows)
            else:
                sheets["Schema"] = pd.DataFrame([schema])

        charts = data.get("charts")
        if isinstance(charts, dict):
            for key, value in charts.items():
                if isinstance(value, pd.DataFrame) and not value.empty:
                    sheets[str(key)] = value

        ignored_keys = {
            "prepared_df",
            "metricas",
            "quality",
            "schema",
            "charts",
            "columns",
        }

        for key, value in data.items():
            if key in ignored_keys:
                continue

            if isinstance(value, pd.DataFrame) and not value.empty:
                sheets[str(key)] = value

            elif isinstance(value, dict):
                try:
                    df = pd.DataFrame([value])
                    if not df.empty:
                        sheets[str(key)] = df
                except Exception:
                    pass

            elif isinstance(value, list):
                try:
                    df = pd.DataFrame(value)
                    if not df.empty:
                        sheets[str(key)] = df
                except Exception:
                    pass

    if not sheets:
        sheets["Resumo"] = pd.DataFrame(
            [
                {
                    "status": "Nenhum dado tabular disponível para exportação.",
                    "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                }
            ]
        )

    return sheets


def gerar_excel(data: Any) -> bytes:
    output = BytesIO()
    sheets = _extract_dataframes(data)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        used_sheet_names: set[str] = set()

        for sheet_name, df in sheets.items():
            display_name = _display_sheet_name(sheet_name)
            safe_name = _safe_sheet_name(display_name)

            original_safe_name = safe_name
            counter = 2

            while safe_name in used_sheet_names:
                suffix = f" {counter}"
                safe_name = _safe_sheet_name(f"{original_safe_name[:31 - len(suffix)]}{suffix}")
                counter += 1

            used_sheet_names.add(safe_name)

            export_df = _format_dataframe_for_excel(df)
            export_df.to_excel(writer, index=False, sheet_name=safe_name)

            worksheet = writer.sheets[safe_name]

            for column_cells in worksheet.columns:
                max_length = 0
                column_letter = column_cells[0].column_letter

                for cell in column_cells:
                    try:
                        max_length = max(max_length, len(str(cell.value)))
                    except Exception:
                        pass

                adjusted_width = min(max(max_length + 2, 12), 42)
                worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)
    return output.getvalue()


def _build_table_style():
    from reportlab.lib import colors
    from reportlab.platypus import TableStyle

    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FFFFFF")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#111827")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, 0), 7),
            ("FONTSIZE", (0, 1), (-1, -1), 6.5),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )


def _build_overview_table(data: dict[str, Any]):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Table, TableStyle

    schema = data.get("schema", {}) or {}
    quality = data.get("quality", {}) or {}
    metricas = data.get("metricas", data) or {}

    total_value = metricas.get("faturamento_total", metricas.get("total", 0))
    avg_value = metricas.get("ticket_medio", metricas.get("media", 0))

    overview = [
        [
            "Domínio",
            str(schema.get("domain", "genérico")).title(),
            "Métrica principal",
            schema.get("metric_column", "Não detectada"),
        ],
        [
            "Dimensão principal",
            schema.get("primary_dimension", "Não detectada"),
            "Dimensão secundária",
            schema.get("secondary_dimension", "Não detectada"),
        ],
        [
            "Registros analisados",
            _format_integer(quality.get("linhas", metricas.get("total_pedidos", 0))),
            "Score do schema",
            _format_percent(quality.get("score_schema", 0)),
        ],
        [
            "Faturamento total",
            _format_currency(total_value),
            "Ticket médio",
            _format_currency(avg_value),
        ],
        [
            "Top dimensão principal",
            metricas.get("top_primary_dimension", "Não informado"),
            "Top dimensão secundária",
            metricas.get("top_secondary_dimension", "Não informado"),
        ],
    ]

    table = Table(
        overview,
        colWidths=[4.3 * cm, 7.1 * cm, 4.3 * cm, 7.1 * cm],
        hAlign="CENTER",
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0F172A")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return table


def _build_kpi_summary(data: dict[str, Any]) -> pd.DataFrame:
    metricas = data.get("metricas", {}) or {}

    rows = [
        {
            "Indicador": "Faturamento Total",
            "Valor": _format_currency(metricas.get("faturamento_total", 0)),
        },
        {
            "Indicador": "Ticket Médio",
            "Valor": _format_currency(metricas.get("ticket_medio", 0)),
        },
        {
            "Indicador": "Registros Analisados",
            "Valor": _format_integer(metricas.get("total_pedidos", 0)),
        },
        {
            "Indicador": "Quantidade Total",
            "Valor": _format_integer(metricas.get("quantidade_total", 0)),
        },
        {
            "Indicador": "Top Dimensão Principal",
            "Valor": metricas.get("top_primary_dimension", "Não informado"),
        },
        {
            "Indicador": "Top Dimensão Secundária",
            "Valor": metricas.get("top_secondary_dimension", "Não informado"),
        },
    ]

    return pd.DataFrame(rows)


def _build_pdf_dataframe_table(df: pd.DataFrame, max_rows: int = 14, max_cols: int = 7, section_key: str = ""):
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, Table
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    if df.empty:
        return None

    preview_df = df.head(max_rows).copy()
    preview_df = preview_df.iloc[:, :max_cols]
    preview_df = _format_dataframe_for_pdf(preview_df, section_key=section_key)

    cell_style = ParagraphStyle(
        name="TableCell",
        fontName="Helvetica",
        fontSize=6.2,
        leading=7.2,
        alignment=TA_CENTER,
    )

    header_style = ParagraphStyle(
        name="TableHeader",
        fontName="Helvetica-Bold",
        fontSize=6.4,
        leading=7.4,
        textColor="#FFFFFF",
        alignment=TA_CENTER,
    )

    table_data = [
        [Paragraph(str(column), header_style) for column in preview_df.columns]
    ]

    for _, row in preview_df.iterrows():
        table_data.append([Paragraph(str(value), cell_style) for value in row.tolist()])

    available_width = 26.0 * cm
    col_count = max(len(preview_df.columns), 1)
    col_width = available_width / col_count
    col_widths = [col_width] * col_count

    table = Table(
        table_data,
        repeatRows=1,
        colWidths=col_widths,
        hAlign="CENTER",
    )
    table.setStyle(_build_table_style())

    return table


def _should_skip_pdf_section(title: str, df: pd.DataFrame) -> bool:
    if title == "Base Preparada":
        return True

    if title == "secondary_metrics":
        return True

    if title == "kpi_cards":
        return True

    if df.empty:
        return True

    if len(df) > 200 and title.lower() in {"dados", "base"}:
        return True

    return False


def gerar_pdf(data: Any) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    output = BytesIO()

    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
        title="Relatório Executivo — DataFlow BI Automation",
        author="DataFlow BI Automation",
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="DataFlowTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="DataFlowSubtitle",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#475569"),
            spaceAfter=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="DataFlowSmall",
            parent=styles["Normal"],
            alignment=TA_LEFT,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#334155"),
        )
    )

    styles.add(
        ParagraphStyle(
            name="DataFlowHeading",
            parent=styles["Heading2"],
            fontSize=12.5,
            leading=15,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=12,
            spaceAfter=7,
        )
    )

    styles.add(
        ParagraphStyle(
            name="DataFlowNote",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#64748B"),
            alignment=TA_LEFT,
        )
    )

    elements: list[Any] = []

    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    elements.append(Paragraph("Relatório Executivo — DataFlow BI Automation", styles["DataFlowTitle"]))
    elements.append(
        Paragraph(
            f"Gerado automaticamente em {generated_at} · Análise tabular com KPIs, schema e rankings executivos",
            styles["DataFlowSubtitle"],
        )
    )

    if isinstance(data, dict):
        elements.append(_build_overview_table(data))
        elements.append(Spacer(1, 10))

        kpi_summary = _build_kpi_summary(data)
        elements.append(Paragraph("Resumo executivo dos indicadores", styles["DataFlowHeading"]))

        kpi_table = _build_pdf_dataframe_table(kpi_summary, max_rows=8, max_cols=2, section_key="kpi_summary")
        if kpi_table is not None:
            elements.append(kpi_table)
            elements.append(Spacer(1, 8))

    sheets = _extract_dataframes(data)

    for title, df in sheets.items():
        if _should_skip_pdf_section(title, df):
            continue

        if title == "KPIs":
            continue

        section_title = _display_section_title(title)
        elements.append(Paragraph(section_title, styles["DataFlowHeading"]))

        if title in {"Qualidade", "Schema"}:
            max_rows = 10
            max_cols = 6
        elif title in {"revenue_by_day"}:
            max_rows = 12
            max_cols = 2
        else:
            max_rows = 12
            max_cols = 6

        table = _build_pdf_dataframe_table(df, max_rows=max_rows, max_cols=max_cols, section_key=title)

        if table is not None:
            elements.append(table)

            if len(df) > max_rows:
                elements.append(
                    Paragraph(
                        f"Exibindo {max_rows} de {len(df)} registros. A versão completa está disponível no Excel.",
                        styles["DataFlowNote"],
                    )
                )

            elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 10))
    elements.append(
        Paragraph(
            "Relatório gerado pelo DataFlow BI Automation. Para auditoria completa, utilize também a exportação em Excel.",
            styles["DataFlowNote"],
        )
    )

    doc.build(elements)

    output.seek(0)
    return output.getvalue()
