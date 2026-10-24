import pandas as pd

from components.sales_dashboard import (
    _compact_ranking_table,
    build_anomaly_comparison_note,
    build_comparison_metrics,
    build_sales_breakdowns,
    safe_percentage_change,
)


def test_sales_breakdowns_rank_revenue_quantity_and_share_without_mutation():
    df = pd.DataFrame(
        {
            "Produto": ["B", "A", "A"],
            "Loja": ["Sul", "Norte", "Norte"],
            "Faturamento": [25.0, 50.0, 25.0],
            "Quantidade": [8, 2, 3],
        }
    )
    original = df.copy(deep=True)

    products, stores = build_sales_breakdowns(df)

    assert products["Produto"].tolist() == ["A", "B"]
    assert products["Posição"].tolist() == [1, 2]
    assert products["Quantidade"].tolist() == [5, 8]
    assert products["Participação na receita"].tolist() == [75.0, 25.0]
    assert products["Participação na quantidade"].tolist() == [5 / 13 * 100, 8 / 13 * 100]
    assert stores["Loja"].tolist() == ["Norte", "Sul"]
    assert stores["Participação na receita"].tolist() == [75.0, 25.0]
    assert stores["Participação na quantidade"].tolist() == [5 / 13 * 100, 8 / 13 * 100]
    pd.testing.assert_frame_equal(df, original)


def test_ranking_table_identifies_and_uses_the_selected_participation_basis():
    df = pd.DataFrame(
        {
            "Produto": ["A", "B"],
            "Loja": ["Norte", "Sul"],
            "Faturamento": [75.0, 25.0],
            "Quantidade": [1, 3],
        }
    )
    products, _ = build_sales_breakdowns(df)

    revenue_table = _compact_ranking_table(products, "Produto", "Receita")
    quantity_table = _compact_ranking_table(products, "Produto", "Quantidade")

    assert "Participação na receita (%)" in revenue_table
    assert "75,0%" in revenue_table
    assert "Participação na quantidade (%)" in quantity_table
    assert "25,0%" in quantity_table


def test_anomaly_note_is_factual_only_when_concentration_is_material():
    df = pd.DataFrame(
        {
            "Data": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]),
            "Faturamento": [900.0, 100.0, 40.0, 60.0],
            "Quantidade": [1, 1, 1, 1],
        }
    )
    anomalies = pd.DataFrame({"indice": [0], "valor": [900.0]})

    note = build_anomaly_comparison_note(df, anomalies)

    assert note is not None
    assert "90,0% da receita do período anterior" in note
    assert "sem demonstrar sua causa" in note
    assert build_anomaly_comparison_note(df, anomalies.iloc[0:0]) is None


def test_percentage_change_is_undefined_for_zero_previous_base():
    assert safe_percentage_change(100.0, 0.0) is None
    assert safe_percentage_change(150.0, 100.0) == 50.0


def test_comparison_reports_insufficient_data_without_inventing_percentage():
    df = pd.DataFrame(
        {
            "Data": [pd.Timestamp("2024-01-01")],
            "Faturamento": [100.0],
            "Quantidade": [1],
        }
    )

    metrics, label, available = build_comparison_metrics(df)

    assert metrics == []
    assert available is False
    assert label == "Sem período comparativo equivalente disponível"


def test_comparison_uses_equivalent_windows_and_real_absolute_difference():
    df = pd.DataFrame(
        {
            "Data": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]),
            "Faturamento": [10.0, 20.0, 40.0, 60.0],
            "Quantidade": [1, 2, 4, 6],
        }
    )

    metrics, _, available = build_comparison_metrics(df)
    revenue = next(metric for metric in metrics if metric.label == "Faturamento")

    assert available is True
    assert revenue.current == 100.0
    assert revenue.previous == 30.0
    assert revenue.difference == 70.0
    assert revenue.percentage == (70.0 / 30.0) * 100
