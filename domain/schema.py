from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum


class AnalyticalType(str, Enum):
    DATE = "date"
    TEXT = "text"
    DECIMAL = "decimal"
    IDENTIFIER = "identifier"


@dataclass(frozen=True)
class FieldDefinition:
    name: str
    data_type: AnalyticalType
    required: bool
    aliases: tuple[str, ...]
    nullable: bool = True


def normalize_column_token(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value).strip())
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "_", text.casefold()).strip("_")


CANONICAL_FIELDS = (
    FieldDefinition(
        "Data", AnalyticalType.DATE, True, ("data", "date", "dt_venda", "data_venda"), False
    ),
    FieldDefinition(
        "Loja", AnalyticalType.TEXT, True, ("loja", "store", "unidade", "filial"), False
    ),
    FieldDefinition(
        "Produto",
        AnalyticalType.TEXT,
        True,
        ("produto", "product", "item", "sku", "nome_produto"),
        False,
    ),
    FieldDefinition(
        "Quantidade",
        AnalyticalType.DECIMAL,
        True,
        ("quantidade", "qtd", "qtde", "volume", "itens", "qty", "quantity"),
        False,
    ),
    FieldDefinition(
        "Faturamento",
        AnalyticalType.DECIMAL,
        True,
        ("faturamento", "receita", "vendas", "valor", "total", "revenue", "preco_total"),
        False,
    ),
    FieldDefinition(
        "Pedido",
        AnalyticalType.IDENTIFIER,
        False,
        ("pedido", "id_pedido", "order_id", "venda", "id_venda"),
    ),
    FieldDefinition(
        "Categoria", AnalyticalType.TEXT, False, ("categoria", "category", "segmento")
    ),
    FieldDefinition(
        "Lucro", AnalyticalType.DECIMAL, False, ("lucro", "profit", "margem", "resultado")
    ),
    FieldDefinition(
        "Preço Unitário",
        AnalyticalType.DECIMAL,
        False,
        ("preco_unitario", "preço_unitário", "unit_price", "valor_unitario"),
    ),
)

FIELD_BY_NAME = {field.name: field for field in CANONICAL_FIELDS}
ALIAS_TO_CANONICAL = {
    normalize_column_token(alias): field.name
    for field in CANONICAL_FIELDS
    for alias in (field.name, *field.aliases)
}
REQUIRED_FIELDS = tuple(field.name for field in CANONICAL_FIELDS if field.required)
OPTIONAL_FIELDS = tuple(field.name for field in CANONICAL_FIELDS if not field.required)


def resolve_column_name(value: object) -> str | None:
    return ALIAS_TO_CANONICAL.get(normalize_column_token(value))


def schema_description() -> dict[str, dict[str, object]]:
    return {
        field.name: {
            "type": field.data_type.value,
            "required": field.required,
            "nullable": field.nullable,
            "aliases": list(field.aliases),
        }
        for field in CANONICAL_FIELDS
    }

