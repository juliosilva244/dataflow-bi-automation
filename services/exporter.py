from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

import pandas as pd


def _safe_sheet_name(name: str) -> str:
    return str(name).replace("/", "-").replace("\\", "-").replace("*", "-").replace("?", "-")[:31] or "Dados"


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
            simple_metrics = {k: v for k, v in metricas.items() if not isinstance(v, (pd.DataFrame, dict, list, tuple))}
            if simple_metrics:
                sheets["KPIs"] = pd.DataFrame([simple_metrics])

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
                    sheets[_safe_sheet_name(key)] = value

        for key, value in data.items():
            if key in {"prepared_df", "metricas", "quality", "schema", "charts", "columns"}:
                continue
            if isinstance(value, pd.DataFrame) and not value.empty:
                sheets[_safe_sheet_name(key)] = value
            elif isinstance(value, dict):
                try:
                    df = pd.DataFrame([value])
                    if not df.empty:
                        sheets[_safe_sheet_name(key)] = df
                except Exception:
                    pass
            elif isinstance(value, list):
                try:
                    df = pd.DataFrame(value)
                    if not df.empty:
                        sheets[_safe_sheet_name(key)] = df
                except Exception:
                    pass

    if not sheets:
        sheets["Resumo"] = pd.DataFrame([{"status": "Nenhum dado tabular disponível para exportação.", "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}])

    return sheets


def gerar_excel(data: Any) -> bytes:
    output = BytesIO()
    sheets = _extract_dataframes(data)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            safe_name = _safe_sheet_name(sheet_name)
            export_df = df.copy()
            for column in export_df.columns:
                if pd.api.types.is_datetime64_any_dtype(export_df[column]):
                    export_df[column] = export_df[column].dt.strftime("%d/%m/%Y")
            export_df.to_excel(writer, index=False, sheet_name=safe_name)
    output.seek(0)
    return output.getvalue()


def _format_number(value: Any) -> str:
    try:
        number = float(value)
        return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(value)


def gerar_pdf(data: Any) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), rightMargin=1.2 * cm, leftMargin=1.2 * cm, topMargin=1.0 * cm, bottomMargin=1.0 * cm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="DataFlowTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=20, leading=24, textColor=colors.HexColor("#0F172A")))
    styles.add(ParagraphStyle(name="DataFlowSmall", parent=styles["Normal"], alignment=TA_LEFT, fontSize=8, leading=10, textColor=colors.HexColor("#334155")))
    styles.add(ParagraphStyle(name="DataFlowHeading", parent=styles["Heading2"], fontSize=12, leading=15, textColor=colors.HexColor("#0F172A")))

    elements = []
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    elements.append(Paragraph("Relatório Executivo — DataFlow BI Automation", styles["DataFlowTitle"]))
    elements.append(Paragraph(f"Gerado em {generated_at}", styles["DataFlowSmall"]))
    elements.append(Spacer(1, 10))

    if isinstance(data, dict):
        schema = data.get("schema", {}) or {}
        quality = data.get("quality", {}) or {}
        metricas = data.get("metricas", data) or {}
        overview = [
            ["Domínio", schema.get("domain", "generico"), "Métrica", schema.get("metric_column", "Não detectada")],
            ["Dimensão principal", schema.get("primary_dimension", "Não detectada"), "Dimensão secundária", schema.get("secondary_dimension", "Não detectada")],
            ["Registros", quality.get("linhas", metricas.get("total_pedidos", 0)), "Score schema", f"{quality.get('score_schema', 0)}%"],
            ["Total", _format_number(metricas.get("faturamento_total", 0)), "Média por registro", _format_number(metricas.get("ticket_medio", 0))],
            ["Top principal", metricas.get("top_primary_dimension", "Não informado"), "Top secundário", metricas.get("top_secondary_dimension", "Não informado")],
        ]
        table = Table(overview, colWidths=[4.0 * cm, 7.0 * cm, 4.0 * cm, 7.0 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0F172A")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 14))

    sheets = _extract_dataframes(data)
    for title, df in sheets.items():
        if title == "Base Preparada":
            continue
        elements.append(Paragraph(str(title), styles["DataFlowHeading"]))
        preview_df = df.head(18).copy()
        if preview_df.empty:
            continue
        preview_df = preview_df.iloc[:, :8]
        table_data = [preview_df.columns.astype(str).tolist()] + preview_df.astype(str).values.tolist()
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 6.5),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

    doc.build(elements)
    output.seek(0)
    return output.getvalue()
