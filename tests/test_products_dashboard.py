import pandas as pd

from components.products_dashboard import (
    build_product_comparison,
    build_product_concentration,
    build_product_kpi_comparison,
    build_product_summary,
    build_product_time_series,
    calculate_product_kpis,
    paginate_products,
)


def sample_products() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Data": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]),
            "Produto": ["B", "A", "A", "B"],
            "Loja": ["Norte"] * 4,
            "Faturamento": [25.0, 25.0, 50.0, 100.0],
            "Quantidade": [5.0, 5.0, 5.0, 5.0],
        }
    )


def test_product_kpis_use_the_complete_active_slice():
    kpis = calculate_product_kpis(sample_products())
    assert kpis.revenue == 200.0
    assert kpis.quantity == 20.0
    assert kpis.distinct_products == 2
    assert kpis.average_revenue_per_product == 100.0


def test_summary_has_correct_revenue_and_quantity_rankings_and_shares():
    summary = build_product_summary(sample_products())
    assert summary["Produto"].tolist() == ["B", "A"]
    assert summary["Receita"].tolist() == [125.0, 75.0]
    assert summary["Participação na receita"].tolist() == [62.5, 37.5]
    assert summary["Participação na quantidade"].tolist() == [50.0, 50.0]
    quantity_ranking = summary.sort_values(["Quantidade", "Produto"], ascending=[False, True])
    assert quantity_ranking["Produto"].tolist() == ["A", "B"]


def test_ranking_ties_are_deterministic_by_product_name():
    df = sample_products().assign(Faturamento=50.0)
    assert build_product_summary(df)["Produto"].tolist() == ["A", "B"]


def test_concentration_adapts_to_available_products():
    concentration = build_product_concentration(build_product_summary(sample_products()))
    assert concentration == {"leader": 62.5, "top3": 100.0, "top5": 100.0}


def test_zero_denominators_do_not_create_artificial_percentages():
    df = sample_products().assign(Faturamento=0.0, Quantidade=0.0)
    summary = build_product_summary(df)
    assert summary["Participação na receita"].sum() == 0
    assert summary["Participação na quantidade"].sum() == 0
    assert summary["Receita média por unidade"].isna().all()


def test_no_valid_product_returns_undefined_average():
    df = sample_products().assign(Produto=None)
    kpis = calculate_product_kpis(df)
    assert kpis.distinct_products == 0
    assert kpis.average_revenue_per_product is None


def test_product_comparison_uses_equivalent_periods_and_zero_base_is_undefined():
    comparison, label, available = build_product_comparison(sample_products())
    assert available is True
    assert "Atual:" in label
    row_a = comparison.set_index("Produto").loc["A"]
    assert row_a["Receita atual"] == 50.0
    assert row_a["Receita anterior"] == 25.0
    assert row_a["Variação da receita (%)"] == 100.0

    only_current = sample_products().copy()
    only_current.loc[only_current.index < 2, "Produto"] = "Outro"
    comparison, _, _ = build_product_comparison(only_current)
    row_a = comparison.set_index("Produto").loc["A"]
    assert pd.isna(row_a["Variação da receita (%)"])


def test_kpi_comparison_reports_missing_period_without_inventing_growth():
    metrics, _, available = build_product_kpi_comparison(sample_products().iloc[:1])
    assert metrics == {}
    assert available is False


def test_time_series_keeps_real_months_and_can_exclude_only_visual_indices():
    df = sample_products()
    complete = build_product_time_series(df, ["A", "B"], "Receita")
    typical = build_product_time_series(df, ["A", "B"], "Receita", {3})
    assert complete["Receita"].sum() == 200.0
    assert typical["Receita"].sum() == 100.0
    assert calculate_product_kpis(df).revenue == 200.0


def test_pagination_changes_only_visible_rows_not_analytical_totals():
    summary = build_product_summary(sample_products())
    page = paginate_products(summary, page=2, page_size=1)
    assert len(page) == 1
    assert len(summary) == 2
    assert summary["Receita"].sum() == 200.0


def test_extreme_values_are_preserved_in_product_totals():
    df = sample_products()
    df.loc[0, "Faturamento"] = 1e20
    assert calculate_product_kpis(df).revenue == 1e20 + 175.0

