import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from services.metrics_engine import construir_analytics_state
from services.formatter import format_currency, format_percent


def chart_container_start() -> None:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)


def chart_container_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_section_header() -> None:
    st.markdown(
        """
        <div class="section-header charts-section-header">
            <div>
                <div class="section-title">Análise Visual Inteligente</div>
                <div class="section-subtitle">
                    Gráficos adaptados automaticamente ao schema da planilha carregada
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def prepare_numeric_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    df = df.copy()

    if column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    return df


def add_value_columns(
    df: pd.DataFrame,
    value_col: str,
    scaled_col: str = "valor_milhoes",
) -> pd.DataFrame:
    df = df.copy()
    df[scaled_col] = df[value_col] / 1_000_000
    df["label"] = df[value_col].apply(format_currency)
    return df


def apply_layout(fig, title: str, height: int = 390):
    fig.update_layout(
        title=dict(
            text=title,
            x=0.03,
            xanchor="left",
            font=dict(size=19, color="white"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", family="Inter"),
        margin=dict(l=28, r=42, t=58, b=46),
        hoverlabel=dict(
            bgcolor="#0F172A",
            bordercolor="#22D3EE",
            font_size=13,
            font_color="#F8FAFC",
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            color="#CBD5E1",
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(148,163,184,0.12)",
            zeroline=False,
            color="#CBD5E1",
            tickfont=dict(size=11),
        ),
        height=height,
        showlegend=False,
    )

    return fig


def get_schema(metricas: dict | None = None) -> dict:
    if metricas and isinstance(metricas, dict):
        return metricas.get("schema", {}) or {}
    return {}


def get_metric_label(metricas: dict | None = None) -> str:
    schema = get_schema(metricas)
    return schema.get("metric_column") or "Métrica Principal"


def get_primary_dimension_label(metricas: dict | None = None) -> str:
    schema = get_schema(metricas)
    return schema.get("primary_dimension") or "Dimensão Principal"


def get_secondary_dimension_label(metricas: dict | None = None) -> str:
    schema = get_schema(metricas)
    return schema.get("secondary_dimension") or "Dimensão Secundária"


def render_revenue_chart(chart_df: pd.DataFrame, metric_label: str = "Métrica") -> None:
    if chart_df is None or chart_df.empty:
        st.info("Não há dados temporais suficientes para montar a evolução.")
        return

    df_plot = chart_df.copy()

    if "periodo" not in df_plot.columns or "faturamento" not in df_plot.columns:
        st.info("As colunas necessárias para a evolução temporal não foram encontradas.")
        return

    df_plot["periodo"] = pd.to_datetime(df_plot["periodo"], errors="coerce")
    df_plot = prepare_numeric_column(df_plot, "faturamento")
    df_plot = df_plot.dropna(subset=["periodo"]).sort_values("periodo")
    df_plot = df_plot[df_plot["faturamento"] > 0]

    if df_plot.empty:
        st.info("Não há valores válidos para montar a evolução temporal.")
        return

    df_plot = add_value_columns(df_plot, "faturamento")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df_plot["periodo"],
            y=df_plot["valor_milhoes"],
            mode="lines+markers",
            line=dict(color="#38BDF8", width=4, shape="spline", smoothing=1.15),
            marker=dict(
                size=8,
                color="#7DD3FC",
                line=dict(width=2, color="#E0F2FE"),
            ),
            fill="tozeroy",
            fillcolor="rgba(56,189,248,0.18)",
            customdata=df_plot[["label"]],
            hovertemplate=(
                "<b>%{x|%m/%Y}</b><br>"
                f"{metric_label}: " + "%{customdata[0]}"
                "<extra></extra>"
            ),
            name=metric_label,
        )
    )

    apply_layout(fig, f"Evolução Mensal de {metric_label}", height=390)

    fig.update_xaxes(tickformat="%m/%Y")
    fig.update_yaxes(
        title_text=f"{metric_label} em milhões",
        tickprefix="R$ ",
        ticksuffix=" mi",
        tickformat=".1f",
        rangemode="tozero",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
    )


def render_dimension_chart(
    chart_df: pd.DataFrame,
    dimension_label: str,
    metric_label: str,
    title: str,
) -> None:
    if chart_df is None or chart_df.empty:
        st.info(f"Não há dados suficientes para montar o ranking por {dimension_label}.")
        return

    df_plot = chart_df.copy()

    if "dimensao" not in df_plot.columns or "valor" not in df_plot.columns:
        st.info("As colunas necessárias para o gráfico dinâmico não foram encontradas.")
        return

    df_plot = prepare_numeric_column(df_plot, "valor")
    df_plot["dimensao"] = df_plot["dimensao"].fillna("Não informado").astype(str)
    df_plot = df_plot[df_plot["valor"] > 0].sort_values("valor", ascending=True)

    if df_plot.empty:
        st.info(f"Não há valores válidos para montar o ranking por {dimension_label}.")
        return

    df_plot = add_value_columns(df_plot, "valor")

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df_plot["valor_milhoes"],
            y=df_plot["dimensao"],
            orientation="h",
            marker=dict(color="#38BDF8", opacity=0.9),
            text=df_plot["label"],
            textposition="auto",
            customdata=df_plot[["label"]],
            hovertemplate=(
                "<b>%{y}</b><br>"
                f"{metric_label}: " + "%{customdata[0]}"
                "<extra></extra>"
            ),
        )
    )

    apply_layout(fig, title, height=410)

    fig.update_xaxes(
        title_text=f"{metric_label} em milhões",
        tickprefix="R$ ",
        ticksuffix=" mi",
        tickformat=".1f",
        rangemode="tozero",
    )

    fig.update_yaxes(title_text=dimension_label)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
    )


def render_legacy_store_chart(chart_df: pd.DataFrame, metric_label: str = "Métrica") -> None:
    if chart_df is None or chart_df.empty:
        st.info("Não há dados suficientes para montar a dimensão principal.")
        return

    df_plot = chart_df.copy()

    if "loja" not in df_plot.columns or "faturamento" not in df_plot.columns:
        st.info("As colunas necessárias para o gráfico legado não foram encontradas.")
        return

    df_plot = df_plot.rename(columns={"loja": "dimensao", "faturamento": "valor"})

    render_dimension_chart(
        chart_df=df_plot,
        dimension_label="Dimensão Principal",
        metric_label=metric_label,
        title="Ranking por Dimensão Principal",
    )


def render_legacy_products_chart(chart_df: pd.DataFrame, metric_label: str = "Métrica") -> None:
    if chart_df is None or chart_df.empty:
        st.info("Não há dados suficientes para montar a dimensão secundária.")
        return

    df_plot = chart_df.copy()

    if "produto" not in df_plot.columns or "faturamento" not in df_plot.columns:
        st.info("As colunas necessárias para o gráfico legado não foram encontradas.")
        return

    df_plot = df_plot.rename(columns={"produto": "dimensao", "faturamento": "valor"})

    render_dimension_chart(
        chart_df=df_plot,
        dimension_label="Dimensão Secundária",
        metric_label=metric_label,
        title="Ranking por Dimensão Secundária",
    )


def render_category_donut_chart(chart_df: pd.DataFrame, metric_label: str = "Métrica") -> None:
    if chart_df is None or chart_df.empty:
        return

    df_plot = chart_df.copy()

    if "categoria" not in df_plot.columns or "faturamento" not in df_plot.columns:
        return

    df_plot = prepare_numeric_column(df_plot, "faturamento")
    df_plot["categoria"] = df_plot["categoria"].fillna("Não informado").astype(str)
    df_plot = df_plot[df_plot["faturamento"] > 0].sort_values(
        "faturamento",
        ascending=False,
    )

    if df_plot.empty:
        return

    invalid_categories = {"sem categoria", "não informado", "nao informado", "none", "nan"}

    unique_categories = {
        str(value).strip().lower()
        for value in df_plot["categoria"].dropna().unique().tolist()
    }

    if len(unique_categories) <= 1 and unique_categories.intersection(invalid_categories):
        st.info("Categoria não encontrada na planilha. O gráfico de participação foi ocultado.")
        return

    total = df_plot["faturamento"].sum()

    if total <= 0:
        return

    df_plot["participacao"] = df_plot["faturamento"] / total * 100
    df_plot["valor_formatado"] = df_plot["faturamento"].apply(format_currency)
    df_plot["participacao_formatada"] = df_plot["participacao"].apply(format_percent)

    fig = px.pie(
        df_plot,
        values="faturamento",
        names="categoria",
        hole=0.55,
        custom_data=["valor_formatado", "participacao_formatada"],
    )

    fig.update_traces(
        textinfo="percent+label",
        insidetextfont=dict(color="white"),
        hovertemplate=(
            "<b>%{label}</b><br>"
            f"{metric_label}: " + "%{customdata[0]}<br>"
            "Participação: %{customdata[1]}"
            "<extra></extra>"
        ),
        marker=dict(line=dict(color="#020617", width=1)),
    )

    apply_layout(fig, "Participação por Categoria", height=390)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
    )


def get_charts_payload(df=None, metricas=None) -> dict:
    if metricas and "charts" in metricas:
        return metricas["charts"]

    if df is not None:
        return construir_analytics_state(df).get("charts", {})

    return {
        "revenue_by_month": pd.DataFrame(),
        "revenue_by_store": pd.DataFrame(),
        "top_products": pd.DataFrame(),
        "revenue_by_category": pd.DataFrame(),
        "primary_dimension_summary": pd.DataFrame(),
        "secondary_dimension_summary": pd.DataFrame(),
    }


def render_charts(df=None, metricas=None) -> None:
    charts = get_charts_payload(df=df, metricas=metricas)

    metric_label = get_metric_label(metricas)
    primary_dimension_label = get_primary_dimension_label(metricas)
    secondary_dimension_label = get_secondary_dimension_label(metricas)

    render_section_header()

    col1, col2 = st.columns(2)

    with col1:
        chart_container_start()
        render_revenue_chart(
            charts.get("revenue_by_month"),
            metric_label=metric_label,
        )
        chart_container_end()

    with col2:
        chart_container_start()
        render_dimension_chart(
            chart_df=charts.get("primary_dimension_summary"),
            dimension_label=primary_dimension_label,
            metric_label=metric_label,
            title=f"Ranking por {primary_dimension_label}",
        )
        chart_container_end()

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    chart_container_start()
    render_dimension_chart(
        chart_df=charts.get("secondary_dimension_summary"),
        dimension_label=secondary_dimension_label,
        metric_label=metric_label,
        title=f"Ranking por {secondary_dimension_label}",
    )
    chart_container_end()

    category_df = charts.get("revenue_by_category")

    if category_df is not None and not category_df.empty:
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        chart_container_start()
        render_category_donut_chart(category_df, metric_label=metric_label)
        chart_container_end()


render_chart = render_charts
show_charts = render_charts
display_charts = render_charts