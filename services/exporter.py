from io import BytesIO
from datetime import datetime
from typing import Any, Dict

import pandas as pd


def _extract_dataframes(data: Any) -> Dict[str, pd.DataFrame]:
    sheets: Dict[str, pd.DataFrame] = {}

    if isinstance(data, pd.DataFrame):
        sheets["Dados"] = data
        return sheets

    if isinstance(data, dict):
        for key, value in data.items():
            sheet_name = str(key)[:31] or "Dados"

            if isinstance(value, pd.DataFrame) and not value.empty:
                sheets[sheet_name] = value

            elif isinstance(value, dict):
                try:
                    df = pd.DataFrame([value])
                    if not df.empty:
                        sheets[sheet_name] = df
                except Exception:
                    pass

            elif isinstance(value, list):
                try:
                    df = pd.DataFrame(value)
                    if not df.empty:
                        sheets[sheet_name] = df
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
        for sheet_name, df in sheets.items():
            safe_name = str(sheet_name).replace("/", "-").replace("\\", "-")[:31]
            df.to_excel(writer, index=False, sheet_name=safe_name or "Dados")

    output.seek(0)
    return output.getvalue()


def gerar_pdf(data: Any) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Relatório DataFlow BI Automation", styles["Title"]))
        elements.append(Spacer(1, 12))

        sheets = _extract_dataframes(data)

        for title, df in sheets.items():
            elements.append(Paragraph(str(title), styles["Heading2"]))
            elements.append(Spacer(1, 8))

            preview_df = df.head(25).copy()
            table_data = [preview_df.columns.tolist()] + preview_df.astype(str).values.tolist()

            table = Table(table_data, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 7),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ]
                )
            )

            elements.append(table)
            elements.append(Spacer(1, 16))

        doc.build(elements)
        output.seek(0)
        return output.getvalue()

    except Exception as error:
        message = f"Erro ao gerar PDF: {error}"
        return message.encode("utf-8")