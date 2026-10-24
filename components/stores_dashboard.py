from __future__ import annotations

import html
import math
from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.charts import _log_currency_ticks, apply_layout
from domain.periods import split_equivalent_periods
from services.anomalies import detect_extreme_monetary_values
from services.formatter import moeda, moeda_resumida, numero
from services.metrics_engine import exact_decimal_sum


@dataclass(frozen=True)
class StoreKPIs:
    revenue: float
    quantity: float
    distinct_stores: int
    average_revenue_per_store: float | None


def percentage_change(current: float, previous: float) -> float | None:
    return None if previous == 0 else ((current - previous) / previous) * 100


def build_store_summary(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "Posição", "Loja", "Receita", "Quantidade", "Participação na receita",
        "Participação na quantidade", "Registros", "Receita média por registro",
        "Produtos distintos",
    ]
    if df.empty or not {"Loja", "Produto", "Faturamento", "Quantidade"}.issubset(df.columns):
        return pd.DataFrame(columns=columns)
    valid = df.dropna(subset=["Loja"]).copy()
    valid["Loja"] = valid["Loja"].astype(str).str.strip()
    valid = valid[valid["Loja"].ne("")]
    if valid.empty:
        return pd.DataFrame(columns=columns)
    summary = (
        valid.groupby("Loja", as_index=False)
        .agg(
            Receita=("Faturamento", "sum"),
            Quantidade=("Quantidade", "sum"),
            Registros=("Loja", "size"),
            **{"Produtos distintos": ("Produto", "nunique")},
        )
        .sort_values(["Receita", "Loja"], ascending=[False, True], kind="mergesort")
        .reset_index(drop=True)
    )
    revenue_total = float(summary["Receita"].sum())
    quantity_total = float(summary["Quantidade"].sum())
    summary.insert(0, "Posição", summary.index + 1)
    summary["Participação na receita"] = summary["Receita"].div(revenue_total).mul(100) if revenue_total else 0.0
    summary["Participação na quantidade"] = summary["Quantidade"].div(quantity_total).mul(100) if quantity_total else 0.0
    summary["Receita média por registro"] = summary["Receita"].div(summary["Registros"].replace(0, pd.NA))
    return summary[columns]


def calculate_store_kpis(df: pd.DataFrame) -> StoreKPIs:
    summary = build_store_summary(df)
    revenue = float(summary["Receita"].sum()) if not summary.empty else 0.0
    quantity = float(summary["Quantidade"].sum()) if not summary.empty else 0.0
    count = len(summary)
    return StoreKPIs(revenue, quantity, count, revenue / count if count else None)


def build_store_kpi_comparison(df: pd.DataFrame) -> tuple[dict[str, float | None], str, bool]:
    current, previous, period = split_equivalent_periods(df, "Data")
    if not period.available:
        return {}, period.label, False
    now, before = calculate_store_kpis(current), calculate_store_kpis(previous)
    return {
        "revenue": percentage_change(now.revenue, before.revenue),
        "quantity": percentage_change(now.quantity, before.quantity),
        "distinct_stores": percentage_change(now.distinct_stores, before.distinct_stores),
        "average_revenue_per_store": percentage_change(
            now.average_revenue_per_store or 0.0, before.average_revenue_per_store or 0.0
        ),
    }, period.label, True


def build_store_concentration(summary: pd.DataFrame) -> dict[str, float]:
    shares = summary["Participação na receita"] if not summary.empty else pd.Series(dtype=float)
    return {"leader": float(shares.head(1).sum()), "top3": float(shares.head(3).sum()), "top5": float(shares.head(5).sum())}


def build_store_time_series(
    df: pd.DataFrame, stores: list[str], metric: str, excluded_indices: set | None = None
) -> pd.DataFrame:
    value_column = "Faturamento" if metric == "Receita" else "Quantidade"
    work = df[df["Loja"].astype(str).isin(stores)].copy()
    if excluded_indices:
        work = work.drop(index=list(excluded_indices), errors="ignore")
    work = work.dropna(subset=["Data"])
    if work.empty:
        return pd.DataFrame(columns=["Período", "Loja", metric])
    return (
        work.groupby([pd.Grouper(key="Data", freq="ME"), "Loja"], as_index=False)[value_column]
        .sum().rename(columns={"Data": "Período", value_column: metric})
        .sort_values(["Período", "Loja"])
    )


def build_store_comparison(df: pd.DataFrame) -> tuple[pd.DataFrame, str, bool]:
    current, previous, period = split_equivalent_periods(df, "Data")
    columns = [
        "Loja", "Receita atual", "Receita anterior", "Diferença de receita",
        "Variação da receita (%)", "Quantidade atual", "Quantidade anterior",
        "Diferença de quantidade", "Variação da quantidade (%)",
    ]
    if not period.available:
        return pd.DataFrame(columns=columns), period.label, False

    def grouped(frame: pd.DataFrame, suffix: str) -> pd.DataFrame:
        return frame.groupby("Loja", as_index=False).agg(**{
            f"Receita {suffix}": ("Faturamento", "sum"),
            f"Quantidade {suffix}": ("Quantidade", "sum"),
        })

    result = grouped(current, "atual").merge(grouped(previous, "anterior"), on="Loja", how="outer").fillna(0)
    result["Diferença de receita"] = result["Receita atual"] - result["Receita anterior"]
    result["Diferença de quantidade"] = result["Quantidade atual"] - result["Quantidade anterior"]
    result["Variação da receita (%)"] = result.apply(lambda row: percentage_change(row["Receita atual"], row["Receita anterior"]), axis=1)
    result["Variação da quantidade (%)"] = result.apply(lambda row: percentage_change(row["Quantidade atual"], row["Quantidade anterior"]), axis=1)
    result = result.sort_values(["Receita atual", "Loja"], ascending=[False, True], kind="mergesort")
    return result[columns].reset_index(drop=True), period.label, True


def build_store_profile(df: pd.DataFrame, store: str) -> dict[str, object]:
    selected = df[df["Loja"].astype(str).eq(str(store))].copy()
    total_revenue = float(df["Faturamento"].sum())
    total_quantity = float(df["Quantidade"].sum())
    revenue = float(selected["Faturamento"].sum())
    quantity = float(selected["Quantidade"].sum())
    products = (
        selected.groupby("Produto", as_index=False)
        .agg(Receita=("Faturamento", "sum"), Quantidade=("Quantidade", "sum"))
    )
    by_revenue = products.sort_values(["Receita", "Produto"], ascending=[False, True], kind="mergesort")
    by_quantity = products.sort_values(["Quantidade", "Produto"], ascending=[False, True], kind="mergesort")
    return {
        "store": store,
        "revenue": revenue,
        "quantity": quantity,
        "revenue_share": revenue / total_revenue * 100 if total_revenue else 0.0,
        "quantity_share": quantity / total_quantity * 100 if total_quantity else 0.0,
        "top_revenue": by_revenue.head(5).reset_index(drop=True),
        "top_quantity": by_quantity.head(5).reset_index(drop=True),
        "data": selected,
    }


def paginate_stores(summary: pd.DataFrame, page: int, page_size: int) -> pd.DataFrame:
    size = max(int(page_size), 1)
    total_pages = max(math.ceil(len(summary) / size), 1)
    safe_page = min(max(int(page), 1), total_pages)
    start = (safe_page - 1) * size
    return summary.iloc[start : start + size].copy()


def _growth(value: float | None, available: bool) -> tuple[str, str]:
    if not available or value is None:
        return "Comparação indisponível", "neutral"
    tone = "positive" if value > 0 else "negative" if value < 0 else "neutral"
    arrow = "↑" if value > 0 else "↓" if value < 0 else "→"
    return f"{arrow} {abs(value):.1f}%".replace(".", ","), tone


def _kpi(label: str, value: str, full: str, badge: str, tone: str, icon: str) -> str:
    return f"""<div class="store-kpi"><div class="store-kpi-head"><span>{icon}</span><strong>{html.escape(label)}</strong>
    <em class="fusion-delta fusion-delta-{tone}">{html.escape(badge)}</em></div>
    <div class="store-kpi-value" title="{html.escape(full)}">{html.escape(value)}</div>
    <div class="store-kpi-foot">Valor integral disponível ao passar o cursor</div></div>"""


def _ranking_figure(summary: pd.DataFrame, metric: str) -> go.Figure:
    data = summary.sort_values([metric, "Loja"], ascending=[False, True]).sort_values(metric)
    currency = metric == "Receita"
    full = data[metric].map(moeda if currency else numero)
    compact = data[metric].map(moeda_resumida if currency else numero)
    palette = ["#22D3EE", "#38BDF8", "#3B82F6", "#6366F1", "#8B5CF6"]
    fig = go.Figure(go.Bar(
        x=data[metric], y=data["Loja"], orientation="h", text=compact, customdata=full,
        textposition="auto", cliponaxis=False, marker=dict(color=palette[: len(data)]),
        hovertemplate=f"<b>%{{y}}</b><br>{metric}: %{{customdata}}<extra></extra>",
    ))
    apply_layout(fig, f"Lojas por {metric.lower()}", height=345)
    fig.update_layout(margin=dict(l=18, r=30, t=58, b=44))
    fig.update_yaxes(title=None, automargin=True)
    if currency and (data[metric] > 0).all():
        ticks, labels = _log_currency_ticks(data[metric])
        fig.update_xaxes(type="log", tickvals=ticks, ticktext=labels, title="Receita (R$ · escala log)")
    else:
        fig.update_xaxes(title="Unidades", tickformat=",.0f")
    return fig


def _concentration_figure(summary: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=summary["Loja"], values=summary["Receita"], hole=.66, textinfo="none",
        customdata=summary["Receita"].map(moeda),
        hovertemplate="<b>%{label}</b><br>Receita: %{customdata}<br>Participação: %{percent}<extra></extra>",
        marker=dict(colors=["#22D3EE", "#3B82F6", "#6366F1", "#8B5CF6", "#10B981"]),
    ))
    apply_layout(fig, "Distribuição entre lojas", height=345)
    fig.update_layout(legend=dict(orientation="h", x=.5, xanchor="center", y=-.04, yanchor="top"), margin=dict(l=8, r=8, t=58, b=60))
    return fig


def _time_figure(data: pd.DataFrame, metric: str, log_scale: bool, title: str) -> go.Figure:
    fig = go.Figure()
    months = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")
    for store, group in data.groupby("Loja", sort=True):
        full = group[metric].map(moeda if metric == "Receita" else numero)
        fig.add_trace(go.Scatter(
            x=group["Período"], y=group[metric], name=str(store), mode="lines+markers",
            line=dict(width=2, shape="linear"), customdata=full,
            hovertemplate=f"<b>{html.escape(str(store))}</b><br>%{{x|%m/%Y}}<br>{metric}: %{{customdata}}<extra></extra>",
        ))
    apply_layout(fig, title, height=355)
    periods = sorted(pd.to_datetime(data["Período"].unique())) if not data.empty else []
    fig.update_xaxes(tickmode="array", tickvals=periods, ticktext=[f"{months[p.month-1]} {p.year}" for p in periods])
    if log_scale and not data.empty and (data[metric] > 0).all():
        fig.update_yaxes(type="log", title=f"{metric} · escala log")
    else:
        fig.update_yaxes(title=metric)
    return fig


def _format_summary(summary: pd.DataFrame) -> pd.DataFrame:
    display = summary.copy()
    display["Receita"] = display["Receita"].map(moeda)
    display["Quantidade"] = display["Quantidade"].map(numero)
    display["Participação na receita"] = display["Participação na receita"].map(lambda x: f"{x:.2f}%".replace(".", ","))
    display["Participação na quantidade"] = display["Participação na quantidade"].map(lambda x: f"{x:.2f}%".replace(".", ","))
    display["Receita média por registro"] = display["Receita média por registro"].map(lambda x: "Indefinida" if pd.isna(x) else moeda(x))
    return display


def render_stores_dashboard(df: pd.DataFrame, source: str) -> None:
    summary = build_store_summary(df)
    if summary.empty:
        st.info("Não há lojas válidas no recorte selecionado.")
        return
    kpis = calculate_store_kpis(df)
    exact_revenue = exact_decimal_sum(df["Faturamento"])
    exact_average = exact_revenue / kpis.distinct_stores if kpis.distinct_stores else None
    growth, period_label, comparison_available = build_store_kpi_comparison(df)
    anomalies = detect_extreme_monetary_values(df)
    dates = pd.to_datetime(df["Data"], errors="coerce").dropna()
    period = "Período não identificado" if dates.empty else f"{dates.min():%d/%m/%Y}–{dates.max():%d/%m/%Y}"
    warning = f"{len(anomalies)} valores atípicos preservados" if len(anomalies) else "Sem anomalias monetárias sinalizadas"
    st.markdown(f"""<div class="store-hero"><div><div class="store-eyebrow">REDE COMERCIAL</div>
    <div class="store-title">Inteligência de Lojas</div><div class="store-subtitle">Desempenho comercial, participação e evolução das unidades de venda.</div></div>
    <div class="store-meta"><span>{html.escape(source)}</span><span>{period}</span><span>{len(df):,} registros</span>
    <span>{len(summary)} lojas na base</span><span class="store-warning">{warning}</span></div></div>""", unsafe_allow_html=True)

    cards = [
        ("Faturamento total", moeda_resumida(exact_revenue), moeda(exact_revenue), "revenue", "◇"),
        ("Unidades vendidas", numero(kpis.quantity), numero(kpis.quantity), "quantity", "↗"),
        ("Lojas ativas na base", numero(kpis.distinct_stores), numero(kpis.distinct_stores), "distinct_stores", "▦"),
        ("Receita média por loja", moeda_resumida(exact_average or 0), "Indefinida" if exact_average is None else moeda(exact_average), "average_revenue_per_store", "◎"),
    ]
    with st.container(key="store-kpis"):
        for column, (label, value, full, key, icon) in zip(st.columns(4), cards):
            badge, tone = _growth(growth.get(key), comparison_available)
            with column:
                st.markdown(_kpi(label, value, full, badge, tone, icon), unsafe_allow_html=True)
    st.caption("Lojas ativas = lojas distintas com registros válidos na base; não comprova operação física. Receita média por loja = faturamento total ÷ lojas válidas. " + period_label)

    st.markdown('<div class="store-section"><span>Ranking e concentração</span><small>Percentuais usam o recorte ativo</small></div>', unsafe_allow_html=True)
    metric = st.segmented_control("Métrica das lojas", ("Receita", "Quantidade"), default="Receita", key="store_ranking_metric", label_visibility="collapsed") or "Receita"
    left, right = st.columns([1.55, 1])
    with left:
        with st.container(border=True):
            st.plotly_chart(_ranking_figure(summary, metric), width="stretch", config={"displayModeBar": False, "responsive": True})
            basis = "Participação na receita" if metric == "Receita" else "Participação na quantidade"
            st.caption(f"{basis} (%) calculada sobre o total do recorte ativo.")
    with right:
        with st.container(border=True):
            st.plotly_chart(_concentration_figure(summary), width="stretch", config={"displayModeBar": False, "responsive": True})
            concentration = build_store_concentration(summary)
            st.markdown(
                f'<div class="store-concentration"><span>Líder<strong>{concentration["leader"]:.1f}%</strong></span>'
                f'<span>Top 3<strong>{concentration["top3"]:.1f}%</strong></span>'
                f'<span>Top {min(5, len(summary))}<strong>{concentration["top5"]:.1f}%</strong></span></div>'.replace(".", ","),
                unsafe_allow_html=True,
            )

    st.markdown('<div class="store-section"><span>Evolução por loja</span><small>Sem suavização ou períodos inventados</small></div>', unsafe_allow_html=True)
    a, b, c = st.columns([2, 1, 1])
    stores = summary["Loja"].tolist()
    with a:
        selected = st.multiselect("Lojas comparadas", stores, default=stores[: min(3, len(stores))], max_selections=4, key="store_temporal_selection")
    with b:
        temporal_metric = st.segmented_control("Métrica temporal de lojas", ("Receita", "Quantidade"), default="Receita", key="store_temporal_metric", label_visibility="collapsed") or "Receita"
    with c:
        view = st.segmented_control("Visão temporal de lojas", ("Completa", "Faixa típica"), default="Completa", key="store_temporal_view", label_visibility="collapsed") or "Completa"
    log_scale = st.toggle("Escala logarítmica", value=True, key="store_temporal_log", help="Aplicada somente quando todos os valores são positivos.")
    excluded = set(anomalies["indice"].tolist()) if view == "Faixa típica" and not anomalies.empty else None
    temporal = build_store_time_series(df, selected, temporal_metric, excluded)
    if not selected or temporal.empty:
        st.info("Selecione ao menos uma loja com dados no período.")
    else:
        if excluded:
            st.caption("Faixa típica exclusivamente visual: valores sinalizados permanecem nos KPIs, rankings e comparação.")
        with st.container(border=True, key="store-timeline"):
            st.plotly_chart(_time_figure(temporal, temporal_metric, log_scale, f"Evolução mensal das lojas · {temporal_metric.lower()}"), width="stretch", config={"displayModeBar": False, "responsive": True})

    st.markdown('<div class="store-section"><span>Perfil analítico</span><small>Uma unidade, dados reais do recorte</small></div>', unsafe_allow_html=True)
    selected_store = st.selectbox("Loja analisada", stores, key="store_profile_selection")
    profile = build_store_profile(df, selected_store)
    st.markdown(f"""<div class="store-profile-strip"><span>Receita<strong>{moeda_resumida(profile['revenue'])}</strong></span>
    <span>Unidades<strong>{numero(profile['quantity'])}</strong></span><span>Participação na receita<strong>{profile['revenue_share']:.1f}%</strong></span>
    <span>Participação na quantidade<strong>{profile['quantity_share']:.1f}%</strong></span></div>""".replace(".", ","), unsafe_allow_html=True)
    profile_left, profile_right = st.columns(2)
    with profile_left:
        st.markdown("**Produtos líderes por receita**")
        detail = profile["top_revenue"].copy()
        detail["Receita"] = detail["Receita"].map(moeda)
        detail["Quantidade"] = detail["Quantidade"].map(numero)
        st.dataframe(detail, width="stretch", hide_index=True)
    with profile_right:
        st.markdown("**Produtos líderes por quantidade**")
        detail = profile["top_quantity"].copy()
        detail["Receita"] = detail["Receita"].map(moeda)
        detail["Quantidade"] = detail["Quantidade"].map(numero)
        st.dataframe(detail, width="stretch", hide_index=True)

    comparison, comparison_label, comparison_ok = build_store_comparison(df)
    st.markdown('<div class="store-section"><span>Comparação temporal</span><small>Janelas equivalentes</small></div>', unsafe_allow_html=True)
    st.caption(comparison_label)
    if comparison_ok:
        if not anomalies.empty:
            st.markdown('<div class="store-comparison-note">Valores monetários sinalizados permanecem nas janelas e podem ampliar variações; os dados não demonstram causa.</div>', unsafe_allow_html=True)
        display = comparison.copy()
        for column in ("Receita atual", "Receita anterior", "Diferença de receita"):
            display[column] = display[column].map(moeda)
        for column in ("Quantidade atual", "Quantidade anterior", "Diferença de quantidade"):
            display[column] = display[column].map(numero)
        for column in ("Variação da receita (%)", "Variação da quantidade (%)"):
            display[column] = display[column].map(lambda x: "Indefinida" if pd.isna(x) else f"{x:+.1f}%".replace(".", ","))
        st.dataframe(display, width="stretch", hide_index=True)
    else:
        st.info("Não há dois períodos equivalentes com dados suficientes.")

    revenue_leader = summary.iloc[0]
    quantity_leader = summary.sort_values(["Quantidade", "Loja"], ascending=[False, True]).iloc[0]
    concentration = build_store_concentration(summary)
    insights = [
        ("RECEITA", "Liderança de faturamento", f"{revenue_leader['Loja']} concentra {revenue_leader['Participação na receita']:.1f}% da receita."),
        ("VOLUME", "Liderança em unidades", f"{quantity_leader['Loja']} representa {quantity_leader['Participação na quantidade']:.1f}% das unidades."),
        ("CONCENTRAÇÃO", "Participação acumulada", f"As três primeiras lojas somam {concentration['top3']:.1f}% da receita; isso não implica risco por si só."),
        ("QUALIDADE", "Valores preservados", f"{len(anomalies)} valores monetários sinalizados permanecem nos cálculos." if len(anomalies) else "Sem extremos monetários sinalizados neste recorte."),
    ]
    st.markdown('<div class="store-section"><span>Leituras verificáveis</span><small>Sem IA externa ou causalidade inventada</small></div>', unsafe_allow_html=True)
    with st.container(key="store-insights"):
        for column, (badge, title, text) in zip(st.columns(4), insights):
            with column:
                st.markdown(f'<div class="store-insight"><em>{badge}</em><strong>{html.escape(title)}</strong><p>{html.escape(text)}</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="store-section"><span>Tabela analítica de lojas</span><small>Paginação somente visual</small></div>', unsafe_allow_html=True)
    page_size = st.selectbox("Lojas por página", sorted({3, 5, 10, max(len(summary), 1)}), key="store_table_page_size")
    total_pages = max(math.ceil(len(summary) / page_size), 1)
    page = st.number_input("Página de lojas", min_value=1, max_value=total_pages, value=1, step=1, key="store_table_page")
    visible = paginate_stores(summary, page, page_size)
    st.caption(f"Exibindo {len(visible)} de {len(summary)} lojas. Totais usam o recorte completo.")
    st.dataframe(_format_summary(visible), width="stretch", hide_index=True)

