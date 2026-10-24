import pandas as pd
import pytest

from services.loader import aplicar_filtro_periodo, limpar_dados, parse_brazilian_number


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("R$ 1.234,56", 1234.56),
        ("1.234,56", 1234.56),
        ("1234.56", 1234.56),
        ("(R$ 50,25)", -50.25),
    ],
)
def test_parse_brazilian_number(raw, expected):
    assert parse_brazilian_number(raw) == pytest.approx(expected)


def test_limpar_dados_descarta_nulos_sem_transformar_nan_em_texto():
    raw = pd.DataFrame(
        {
            "Data": ["2024-01-01", "2024-01-02"],
            "Loja": ["Centro", None],
            "Produto": ["Notebook", "Mouse"],
            "Quantidade": ["2", "1"],
            "Faturamento": ["R$ 1.234,56", "R$ 10,00"],
        }
    )

    cleaned, error = limpar_dados(raw)

    assert error is None
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["Faturamento"] == pytest.approx(1234.56)


def test_periodo_usa_data_maxima_da_base_e_nao_relogio_atual():
    df = pd.DataFrame(
        {
            "Data": pd.to_datetime(["2020-01-01", "2020-01-25", "2020-01-31"]),
        }
    )

    result = aplicar_filtro_periodo(df, "Últimos 7 dias")

    assert result["Data"].tolist() == list(pd.to_datetime(["2020-01-25", "2020-01-31"]))

