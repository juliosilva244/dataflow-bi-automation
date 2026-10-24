from __future__ import annotations

import html

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from assets.styles import DESIGN_TOKENS
from services.data_quality import (
    CLASSIFICATIONS,
    QualityAudit,
    audit_data_quality,
    filter_findings,
    findings_dataframe,
    paginate_findings,
)
from services.formatter import numero

PLOT_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": DESIGN_TOKENS["text"], "family": "Inter, sans-serif", "size": 12},
    "margin": {"l": 18, "r": 18, "t": 48, "b": 28},
    "hoverlabel": {"bgcolor": "#07152F", "font_color": "#FFFFFF"},
}

CLASSIFICATION_COLORS = dict(zip(CLASSIFICATIONS, (
    DESIGN_TOKENS["error"], DESIGN_TOKENS["warning"],
    DESIGN_TOKENS["cyan"], DESIGN_TOKENS["muted"],
), strict=True))


def _period_label(df: pd.DataFrame) -> str:
    if "Data" not in df.columns or df.empty:
        return "Período não disponível"
    dates = pd.to_datetime(df["Data"], errors="coerce").dropna()
    if dates.empty:
        return "Período não disponível"
    return f"{dates.min():%d/%m/%Y}–{dates.max():%d/%m/%Y}"


def _status_label(audit: QualityAudit) -> str:
    if not audit.records_analyzed:
        return "Sem registros para avaliar"
    if audit.findings:
        return "Avaliação concluída com achados"
    return "Avaliação concluída sem achados"


def _render_header(df: pd.DataFrame, source: str, audit: QualityAudit) -> None:
    status = _status_label(audit)
    st.html(
        f"""
        <div class="quality-hero">
          <div>
            <div class="quality-eyebrow">CONFIABILIDADE E GOVERNANÇA</div>
            <div class="quality-title">Qualidade dos Dados</div>
            <div class="quality-subtitle">Diagnóstico, consistência e confiabilidade das informações analisadas.</div>
          </div>
          <div class="quality-meta">
            <span>{html.escape(source)}</span><span>{numero(len(df))} registros</span>
            <span>{len(df.columns)} colunas</span><span>{_period_label(df)}</span>
            <span>{len(audit.checks)} verificações</span><span class="quality-status">{status}</span>
          </div>
        </div>
        <div class="quality-scope"><strong>Escopo:</strong> {html.escape(audit.source_scope)}. A auditoria não altera os dados.</div>
        """
    )


def _render_kpis(audit: QualityAudit) -> None:
    values = (
        ("▦", "Registros analisados", numero(audit.records_analyzed), "Linhas efetivamente submetidas"),
        ("◫", "Completude dos dados", f"{audit.completeness:.2f}%".replace(".", ","), f"{numero(audit.filled_cells)} de {numero(audit.eligible_cells)} células elegíveis"),
        ("!", "Registros com alertas", numero(audit.alerted_records), f"{audit.alert_percentage:.2f}% dos registros".replace(".", ",")),
        ("✓", "Verificações aprovadas", f"{audit.approved_checks}/{audit.executed_checks}", "Não avaliadas não contam como aprovadas"),
    )
    with st.container(key="quality-kpis"):
        columns = st.columns(4)
        for column, (icon, label, value, foot) in zip(columns, values):
            with column:
                st.html(
                    f"""<div class="quality-kpi"><div class="quality-kpi-head"><span>{icon}</span>
                    <strong>{label}</strong></div><div class="quality-kpi-value">{value}</div>
                    <div class="quality-kpi-foot">{foot}</div></div>"""
                )


def _render_completeness(audit: QualityAudit) -> None:
    table = audit.completeness_table.sort_values("Completude (%)", ascending=True)
    if table.empty:
        st.info("Não há colunas canônicas disponíveis para calcular completude.")
        return
    figure = px.bar(
        table,
        x="Completude (%)",
        y="Coluna",
        orientation="h",
        color="Completude (%)",
        color_continuous_scale=[DESIGN_TOKENS["error"], DESIGN_TOKENS["violet"], DESIGN_TOKENS["cyan"]],
        range_color=(0, 100),
        custom_data=["Preenchidos", "Ausentes", "Obrigatória"],
    )
    figure.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>Completude: %{x:.2f}%<br>Preenchidos: %{customdata[0]}"
            "<br>Ausentes: %{customdata[1]}<br>Obrigatória: %{customdata[2]}<extra></extra>"
        )
    )
    figure.update_layout(**PLOT_LAYOUT, title="Preenchimento por coluna", coloraxis_showscale=False)
    figure.update_xaxes(range=[0, 100], ticksuffix="%", gridcolor="rgba(106,145,205,.13)")
    figure.update_yaxes(gridcolor="rgba(0,0,0,0)")
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
    st.dataframe(
        table.sort_values(["Completude (%)", "Coluna"]),
        width="stretch",
        hide_index=True,
        column_config={"Completude (%)": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.2f%%")},
    )


def _render_distributions(audit: QualityAudit) -> None:
    findings = findings_dataframe(audit)
    left, right = st.columns([1.35, 1])
    with left:
        with st.container(border=True):
            if findings.empty:
                st.info("Nenhuma ocorrência detalhada foi encontrada nos dados disponíveis.")
            else:
                occurrences = findings.groupby("Categoria", as_index=False).size().rename(columns={"size": "Ocorrências"})
                affected = (
                    findings[findings["Linha técnica"].str.startswith("linha:")]
                    .groupby("Categoria")["Linha técnica"].nunique().rename("Registros afetados")
                )
                distribution = occurrences.merge(affected, on="Categoria", how="left").fillna(0)
                long = distribution.melt("Categoria", var_name="Métrica", value_name="Quantidade")
                figure = px.bar(
                    long, x="Categoria", y="Quantidade", color="Métrica", barmode="group",
                    color_discrete_map={"Ocorrências": DESIGN_TOKENS["cyan"], "Registros afetados": DESIGN_TOKENS["violet"]},
                )
                figure.update_layout(**PLOT_LAYOUT, title="Ocorrências e registros distintos por categoria", legend_title_text="")
                figure.update_xaxes(tickangle=-18, gridcolor="rgba(0,0,0,0)")
                figure.update_yaxes(gridcolor="rgba(106,145,205,.13)", dtick=1)
                st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
    with right:
        with st.container(border=True):
            if findings.empty:
                st.info("Sem severidades para distribuir.")
            else:
                severity = findings.groupby("Classificação", as_index=False).size().rename(columns={"size": "Ocorrências"})
                figure = go.Figure(
                    go.Pie(
                        labels=severity["Classificação"], values=severity["Ocorrências"], hole=0.64,
                        textinfo="none", hovertemplate="%{label}: %{value}<extra></extra>",
                        marker={"colors": [CLASSIFICATION_COLORS[label] for label in severity["Classificação"]]},
                    )
                )
                figure.update_layout(**PLOT_LAYOUT, title="Classificação dos achados", legend={"orientation": "h", "y": -0.08})
                figure.add_annotation(text=f"<b>{len(findings)}</b><br>ocorrências", showarrow=False, font={"size": 15, "color": "#FFFFFF"})
                st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def _render_checks(audit: QualityAudit) -> None:
    rows = pd.DataFrame(
        [
            {
                "Verificação": item.name,
                "Estado": item.status,
                "Ocorrências": item.occurrences,
                "Registros afetados": item.affected_records,
                "Critério": item.criterion,
            }
            for item in audit.checks
        ]
    )
    st.dataframe(rows, width="stretch", hide_index=True)
    st.caption("Uma verificação não avaliada nunca é contabilizada como aprovada.")


def _render_investigation(audit: QualityAudit) -> None:
    findings = findings_dataframe(audit)
    if findings.empty:
        st.success("Nenhuma ocorrência detalhada foi encontrada para investigação.")
        return
    categories = ["Todas", *sorted(findings["Categoria"].unique())]
    controls = st.columns([1.15, 1.15, 2, 0.75])
    with controls[0]:
        category = st.selectbox("Categoria", categories, key="quality_category")
    with controls[1]:
        classification = st.selectbox("Classificação", ["Todas", *CLASSIFICATIONS], key="quality_classification")
    with controls[2]:
        query = st.text_input("Busca nos achados", placeholder="Buscar coluna, regra ou descrição...", key="quality_query")
    with controls[3]:
        page_size = st.selectbox("Itens por página", [10, 20, 50], key="quality_page_size")
    filtered = filter_findings(findings, category=category, classification=classification, query=query)
    page = st.number_input("Página", min_value=1, value=1, step=1, key="quality_page")
    visible, total_pages, safe_page = paginate_findings(filtered, int(page), int(page_size))
    if visible.empty:
        st.info("Nenhum achado corresponde aos filtros atuais.")
    else:
        st.dataframe(visible, width="stretch", hide_index=True)
    st.caption(
        f"Exibindo {len(visible)} de {len(filtered)} ocorrências · página {safe_page} de {total_pages}. "
        "A paginação afeta somente a visualização."
    )


def _render_summary(audit: QualityAudit) -> None:
    findings = findings_dataframe(audit)
    if audit.completeness_table.empty:
        absence = "Não há colunas avaliáveis para identificar ausências."
    else:
        worst = audit.completeness_table.sort_values(["Completude (%)", "Coluna"]).iloc[0]
        absence = f"{worst['Coluna']} tem {worst['Completude (%)']:.2f}% de completude e {int(worst['Ausentes'])} ausências.".replace(".", ",")
    frequent = "Nenhuma ocorrência detalhada."
    if not findings.empty:
        counts = findings["Categoria"].value_counts()
        frequent = f"{counts.index[0]} é a categoria mais frequente, com {int(counts.iloc[0])} ocorrências."
    duplicates = sum(item.occurrences for item in audit.checks if item.name == "Duplicidade exata")
    extremes = sum(item.occurrences for item in audit.checks if item.name == "Valores monetários extremos")
    cards = (
        ("COMPLETUDE", "Campo mais sensível", absence),
        ("ACHADOS", "Ocorrência predominante", frequent),
        ("DUPLICIDADE", "Linhas exatamente repetidas", f"{duplicates} duplicidades exatas detectadas; repetições não idênticas não são presumidas como erro."),
        ("EXTREMOS", "Valores preservados", f"{extremes} valores monetários atípicos sinalizados e mantidos integralmente."),
    )
    with st.container(key="quality-insights"):
        columns = st.columns(4)
        for column, (badge, title, text) in zip(columns, cards):
            with column:
                st.html(f'<div class="quality-insight"><em>{badge}</em><strong>{title}</strong><p>{html.escape(text)}</p></div>')


def render_quality_dashboard(df: pd.DataFrame, source: str, *, active_records: int | None = None) -> QualityAudit:
    with st.container(key="quality-native-title"):
        st.title("Qualidade dos Dados")
    scope = "Base carregada após validação, normalização e período rápido"
    audit = audit_data_quality(df, source_scope=scope)
    _render_header(df, source, audit)
    if active_records is not None and active_records != len(df):
        st.info(
            f"Os filtros comerciais selecionam {numero(active_records)} registros, mas esta auditoria usa "
            f"os {numero(len(df))} registros da base carregada para não ocultar problemas de qualidade."
        )
    _render_kpis(audit)

    st.html('<div class="quality-section"><span>Completude dos campos</span><small>Percentuais verificáveis sobre células elegíveis</small></div>')
    _render_completeness(audit)
    st.html('<div class="quality-section"><span>Distribuição dos achados</span><small>Ocorrências não equivalem a registros únicos</small></div>')
    _render_distributions(audit)
    st.html('<div class="quality-section"><span>Verificações executadas</span><small>Critérios e estados transparentes</small></div>')
    _render_checks(audit)
    st.html('<div class="quality-section"><span>Investigação de registros</span><small>Valores seguros e regras rastreáveis</small></div>')
    _render_investigation(audit)
    st.html('<div class="quality-section"><span>Rastreabilidade do pipeline</span><small>Somente transformações realmente conhecidas</small></div>')
    with st.container(border=True):
        st.markdown(
            "**Transformações confirmadas:** aliases convertidos para o schema canônico; datas interpretadas "
            "com preferência brasileira; monetários convertidos pela normalização central; textos aparados; "
            "linhas inválidas e duplicidades exatas resumidas no relatório de carga."
        )
        for limitation in audit.limitations:
            st.warning(limitation)
    st.html('<div class="quality-section"><span>Resumo executivo determinístico</span><small>Sem IA externa ou pontuação arbitrária</small></div>')
    _render_summary(audit)
    return audit
