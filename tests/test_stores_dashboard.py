import pandas as pd

from components.stores_dashboard import (
    build_store_comparison,
    build_store_concentration,
    build_store_kpi_comparison,
    build_store_profile,
    build_store_summary,
    build_store_time_series,
    calculate_store_kpis,
    paginate_stores,
)


def sample_stores() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Data": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]),
            "Loja": ["Sul", "Norte", "Norte", "Sul"],
            "Produto": ["B", "A", "B", "A"],
            "Faturamento": [25.0, 25.0, 50.0, 100.0],
            "Quantidade": [5.0, 5.0, 5.0, 5.0],
        }
    )


def test_store_kpis_use_complete_active_slice():
    kpis = calculate_store_kpis(sample_stores())
    assert kpis.revenue == 200.0
    assert kpis.quantity == 20.0
    assert kpis.distinct_stores == 2
    assert kpis.average_revenue_per_store == 100.0


def test_store_summary_has_correct_rankings_shares_and_record_methodology():
    summary = build_store_summary(sample_stores())
    assert summary["Loja"].tolist() == ["Sul", "Norte"]
    assert summary["Receita"].tolist() == [125.0, 75.0]
    assert summary["Participação na receita"].tolist() == [62.5, 37.5]
    assert summary["Participação na quantidade"].tolist() == [50.0, 50.0]
    assert summary["Receita média por registro"].tolist() == [62.5, 37.5]
    assert summary["Produtos distintos"].tolist() == [2, 2]


def test_store_ranking_ties_use_name_as_deterministic_tiebreaker():
    df = sample_stores().assign(Faturamento=50.0)
    assert build_store_summary(df)["Loja"].tolist() == ["Norte", "Sul"]


def test_store_concentration_adapts_to_available_count():
    result = build_store_concentration(build_store_summary(sample_stores()))
    assert result == {"leader": 62.5, "top3": 100.0, "top5": 100.0}


def test_zero_denominators_are_safe_and_average_is_undefined_without_stores():
    zero = sample_stores().assign(Faturamento=0.0, Quantidade=0.0)
    summary = build_store_summary(zero)
    assert summary["Participação na receita"].sum() == 0
    assert summary["Participação na quantidade"].sum() == 0
    empty = calculate_store_kpis(sample_stores().assign(Loja=None))
    assert empty.average_revenue_per_store is None


def test_store_comparison_uses_equivalent_periods_and_undefined_zero_base():
    comparison, label, available = build_store_comparison(sample_stores())
    assert available is True
    assert "Atual:" in label
    north = comparison.set_index("Loja").loc["Norte"]
    assert north["Receita atual"] == 50.0
    assert north["Receita anterior"] == 25.0
    assert north["Variação da receita (%)"] == 100.0

    df = sample_stores().copy()
    df.loc[df.index < 2, "Loja"] = "Outra"
    comparison, _, _ = build_store_comparison(df)
    assert pd.isna(comparison.set_index("Loja").loc["Norte", "Variação da receita (%)"])


def test_store_kpi_comparison_does_not_invent_period():
    metrics, _, available = build_store_kpi_comparison(sample_stores().iloc[:1])
    assert metrics == {}
    assert available is False


def test_store_time_series_respects_selection_and_visual_exclusion():
    df = sample_stores()
    north = build_store_time_series(df, ["Norte"], "Receita")
    typical = build_store_time_series(df, ["Norte", "Sul"], "Receita", {3})
    assert north["Receita"].sum() == 75.0
    assert typical["Receita"].sum() == 100.0
    assert calculate_store_kpis(df).revenue == 200.0


def test_store_profile_uses_real_products_and_slice_denominators():
    profile = build_store_profile(sample_stores(), "Norte")
    assert profile["revenue"] == 75.0
    assert profile["quantity"] == 10.0
    assert profile["revenue_share"] == 37.5
    assert profile["quantity_share"] == 50.0
    assert profile["top_revenue"].iloc[0]["Produto"] == "B"
    assert profile["top_quantity"]["Produto"].tolist() == ["A", "B"]


def test_store_pagination_does_not_change_totals():
    summary = build_store_summary(sample_stores())
    assert len(paginate_stores(summary, 2, 1)) == 1
    assert summary["Receita"].sum() == 200.0


def test_store_extreme_values_are_preserved():
    df = sample_stores()
    df.loc[0, "Faturamento"] = 1e20
    assert calculate_store_kpis(df).revenue == 1e20 + 175.0


def test_store_functions_respect_an_already_filtered_slice():
    filtered = sample_stores().query("Loja == 'Norte'")
    kpis = calculate_store_kpis(filtered)
    assert kpis.distinct_stores == 1
    assert kpis.revenue == 75.0

