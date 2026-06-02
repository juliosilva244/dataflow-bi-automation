import pandas as pd

def sanitize_numeric(value):
    if pd.isna(value) or value is None:
        return 0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0

def format_currency(value):
    value = sanitize_numeric(value)
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_percent(value):
    value = sanitize_numeric(value)
    return f"{value:.2f}%".replace(".", ",")

def format_number(value):
    value = sanitize_numeric(value)
    return f"{value:,.0f}".replace(",", ".")

def safe_divide(numerator, denominator):
    numerator = sanitize_numeric(numerator)
    denominator = sanitize_numeric(denominator)
    if denominator == 0:
        return 0
    return numerator / denominator

def moeda_resumida(valor):
    valor = sanitize_numeric(valor)
    if valor >= 1_000_000:
        return f"R$ {valor / 1_000_000:,.2f}M".replace(",", "X").replace(".", ",").replace("X", ".")
    if valor >= 1_000:
        return f"R$ {valor / 1_000:,.2f}K".replace(",", "X").replace(".", ",").replace("X", ".")
    return format_currency(valor)
