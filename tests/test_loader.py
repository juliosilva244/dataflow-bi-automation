from dataclasses import replace
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest

from services import loader
from services.loader import aplicar_filtro_periodo, limpar_dados, parse_brazilian_number
from services.metrics_engine import construir_analytics_state
from services.performance import SessionScopedCache, TelemetryCollector, content_signature

ROOT = Path(__file__).resolve().parents[1]


class Upload(BytesIO):
    name = "enviado.csv"


@pytest.fixture
def isolated_sources(monkeypatch, tmp_path):
    operational = tmp_path / "vendas.xlsx"
    demo = ROOT / "data/demo/vendas_demo.csv"
    monkeypatch.setattr(loader, "DEFAULT_DATA_PATH", operational)
    monkeypatch.setattr(loader, "DEMO_DATA_PATH", demo)
    monkeypatch.chdir(tmp_path)
    return operational, demo


def write_operational_sample(path):
    pd.DataFrame({
        "Data": ["2025-01-01"], "Loja": ["Local ficticia"],
        "Produto": ["Produto local ficticio"], "Quantidade": [2], "Faturamento": [123.45],
    }).to_excel(path, index=False)


@pytest.mark.parametrize("operational_exists", [False, True])
def test_upload_has_priority_without_mixing_sources(isolated_sources, operational_exists):
    operational, _ = isolated_sources
    if operational_exists:
        write_operational_sample(operational)
    upload = Upload(
        b"Data,Loja,Produto,Quantidade,Faturamento\n"
        b"2025-01-02,Upload ficticio,Produto enviado,1,987.65\n"
    )
    frame, source, error = loader.carregar_dados(upload)
    assert error is None
    assert source == "Arquivo enviado: enviado.csv"
    assert len(frame) == 1
    assert frame["Loja"].tolist() == ["Upload ficticio"]
    assert construir_analytics_state(frame)["faturamento_total_exato"] == Decimal("987.65")


def test_operational_file_has_priority_over_demo(isolated_sources):
    operational, _ = isolated_sources
    write_operational_sample(operational)
    frame, source, error = loader.carregar_dados()
    assert error is None
    assert source == "Arquivo padrão do sistema"
    assert len(frame) == 1
    assert frame["Loja"].tolist() == ["Local ficticia"]
    assert construir_analytics_state(frame)["faturamento_total_exato"] == Decimal("123.45")


@pytest.mark.parametrize("period", ["Tudo", "Últimos 7 dias"])
def test_missing_operational_uses_demo_with_same_pipeline(isolated_sources, period):
    _, demo = isolated_sources
    cache, telemetry = SessionScopedCache(), TelemetryCollector()
    frame, source, error = loader.carregar_dados(periodo=period, cache=cache, telemetry=telemetry)
    expected, _, expected_error = loader.carregar_dados(Upload(demo.read_bytes()), periodo=period)
    assert error is expected_error is None
    assert source == "Demonstração — dados fictícios"
    pd.testing.assert_frame_equal(frame, expected)
    assert frame.attrs["dataset_signature"] == content_signature(demo.read_bytes())
    assert frame.attrs["quality_report"].valid_records == 720
    if period == "Tudo":
        assert len(frame) == 720
    state = construir_analytics_state(frame)
    assert state["faturamento_total_exato"] == construir_analytics_state(expected)["faturamento_total_exato"]
    assert isinstance(state["faturamento_total_exato"], Decimal)
    cached, cached_source, cached_error = loader.carregar_dados(
        periodo=period, cache=cache, telemetry=telemetry,
    )
    assert cached_error is None
    assert cached_source == source
    pd.testing.assert_frame_equal(cached, frame)
    assert telemetry.latest["carregamento"]["cache_hit"] is True


def test_invalid_upload_does_not_fall_back_to_demo(isolated_sources):
    frame, _, error = loader.carregar_dados(Upload(b"invalid"))
    assert frame is None
    assert error is not None


def test_invalid_operational_file_does_not_fall_back_to_demo(isolated_sources):
    operational, _ = isolated_sources
    operational.write_bytes(b"invalid")
    frame, _, error = loader.carregar_dados()
    assert frame is None
    assert "XLSX_SIGNATURE_MISMATCH" in error


def test_inaccessible_operational_does_not_fall_back_to_demo(isolated_sources, monkeypatch):
    operational, _ = isolated_sources
    original_open = Path.open

    def deny_operational(path, *args, **kwargs):
        if path == operational:
            raise PermissionError("Access denied")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", deny_operational)
    frame, _, error = loader.carregar_dados()
    assert frame is None
    assert "LOAD_INTERNAL" in error


def test_demo_respects_upload_limits(isolated_sources, monkeypatch):
    settings = replace(loader.get_security_settings(), max_rows=1)
    monkeypatch.setattr(loader, "get_security_settings", lambda: settings)
    frame, _, error = loader.carregar_dados()
    assert frame is None
    assert "UPLOAD_TOO_MANY_ROWS" in error


def test_missing_both_sources_returns_actionable_error(isolated_sources, monkeypatch, tmp_path):
    monkeypatch.setattr(loader, "DEMO_DATA_PATH", tmp_path / "missing.csv")
    frame, source, error = loader.carregar_dados()
    assert frame is source is None
    assert "demonstração" in error
    assert "Envie um arquivo CSV ou XLSX" in error


def test_switching_upload_and_demo_keeps_cache_separate(isolated_sources):
    cache = SessionScopedCache()
    demo, demo_source, error = loader.carregar_dados(cache=cache)
    assert error is None
    upload = Upload(
        b"Data,Loja,Produto,Quantidade,Faturamento\n"
        b"2025-01-02,Upload ficticio,Produto enviado,1,987.65\n"
    )
    sent, sent_source, error = loader.carregar_dados(upload, cache=cache)
    assert error is None
    assert len(sent) == 1
    assert sent_source != demo_source
    assert sent.attrs["dataset_signature"] != demo.attrs["dataset_signature"]
    restored, source, error = loader.carregar_dados(cache=cache)
    assert error is None
    assert source == demo_source
    pd.testing.assert_frame_equal(restored, demo)


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

