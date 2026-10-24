"""Gera a base pública e inteiramente fictícia de demonstração do DataFlow."""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

SEED = 20261020
ROW_COUNT = 720
DEFAULT_OUTPUT = Path("data/demo/vendas_demo.csv")

STORES = ("Loja Aurora", "Loja Horizonte", "Loja Prisma", "Loja Vértice")
PRODUCTS = (
    ("Estação Atlas", "Informática", Decimal("4299.90")),
    ("Monitor Boreal", "Informática", Decimal("1299.90")),
    ("Teclado Íris", "Acessórios", Decimal("249.90")),
    ("Mouse Órbita", "Acessórios", Decimal("159.90")),
    ("Headset Nébula", "Áudio", Decimal("399.90")),
    ("Cadeira Lumen", "Mobiliário", Decimal("1149.90")),
)
FIELDNAMES = (
    "Data",
    "Loja",
    "Produto",
    "Quantidade",
    "Faturamento",
    "Pedido",
    "Categoria",
    "Preço Unitário",
)


def build_rows(seed: int = SEED, row_count: int = ROW_COUNT) -> list[dict[str, object]]:
    """Retorna registros comerciais fictícios e determinísticos."""
    rng = random.Random(seed)
    start = date(2025, 1, 1)
    rows: list[dict[str, object]] = []
    for index in range(row_count):
        product, category, base_price = rng.choice(PRODUCTS)
        quantity = rng.randint(1, 8)
        price_factor = Decimal(rng.choice((95, 98, 100, 100, 102, 105))) / Decimal(100)
        unit_price = (base_price * price_factor).quantize(Decimal("0.01"))
        revenue = (unit_price * quantity).quantize(Decimal("0.01"))
        rows.append(
            {
                "Data": (start + timedelta(days=rng.randrange(365))).isoformat(),
                "Loja": rng.choice(STORES),
                "Produto": product,
                "Quantidade": quantity,
                "Faturamento": f"{revenue:.2f}",
                "Pedido": f"DEMO-{index + 1:05d}",
                "Categoria": category,
                "Preço Unitário": f"{unit_price:.2f}",
            }
        )
    return rows


def write_demo_csv(output: Path = DEFAULT_OUTPUT) -> Path:
    """Grava o CSV UTF-8 separado da base operacional."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(build_rows())
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = write_demo_csv(args.output)
    print(f"Base sintética criada em {output} ({ROW_COUNT} registros; seed {SEED}).")


if __name__ == "__main__":
    main()
