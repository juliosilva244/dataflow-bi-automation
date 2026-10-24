from __future__ import annotations

import html
from typing import Any

EXCEL_FORMULA_PREFIXES = ("=", "+", "-", "@")


def escape_html(value: Any) -> str:
    """Escape untrusted values before inserting them into HTML templates."""
    return html.escape(str(value), quote=True)


def neutralize_excel_formula(value: Any) -> Any:
    """Prevent spreadsheet applications from evaluating untrusted text as formulas."""
    if not isinstance(value, str):
        return value

    first_visible = value.lstrip()
    if first_visible.startswith(EXCEL_FORMULA_PREFIXES):
        return "'" + value

    return value

