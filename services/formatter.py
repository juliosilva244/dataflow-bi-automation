def moeda_integral(value):
    """Decimal text without rounding, including the reference fraction of a ticket."""
    integer, _, fraction = format(value, "f").partition(".")
    grouped = f"{int(integer):,}".replace(",", ".")
    if integer.startswith("-") and int(integer) == 0:
        grouped = "-" + grouped
    return "R$ " + grouped + "," + fraction.ljust(2, "0")


def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def numero(valor):
    numeric = float(valor)
    if numeric.is_integer():
        return f"{int(numeric):,}".replace(",", ".")
    return f"{numeric:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def moeda_resumida(valor):
    scales = (
        (1_000_000_000_000_000_000, "qi"),
        (1_000_000_000_000_000, "qua"),
        (1_000_000_000_000, "tri"),
        (1_000_000_000, "bi"),
        (1_000_000, "mi"),
        (1_000, "mil"),
    )
    for divisor, suffix in scales:
        if abs(valor) >= divisor:
            return f"R$ {valor / divisor:.2f} {suffix}".replace(".", ",")

    return moeda(valor)
