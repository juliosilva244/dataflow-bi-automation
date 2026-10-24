from __future__ import annotations

import html
import time

import pandas as pd
import plotly.express as px
import streamlit as st

from assets.styles import DESIGN_TOKENS
from components.charts import _log_currency_ticks
from services.anomalies import detect_extreme_monetary_values
from services.formatter import moeda, moeda_resumida, numero
from services.performance import dataframe_fingerprint
from services.reporting import REPORT_MODELS, build_report_document, export_report


def _format_indicator(label: str, value) -> str:
    lowered = label.casefold()
    if any(term in lowered for term in ("receita", "faturamento")):
        return moeda_resumida(float(value))
    if "%" in label or "completude" in lowered:
        return f"{float(value):.2f}%".replace(".", ",")
    if isinstance(value, (int, float)):
        return numero(value)
    return str(value)


def _render_catalog() -> None:
    st.html('<div class="report-section"><span>Catálogo de relatórios</span><small>Cinco modelos funcionais</small></div>')
    with st.container(key="report-catalog"):
        columns = st.columns(5)
        for column, model in zip(columns, REPORT_MODELS):
            with column:
                st.html(
                    f'<div class="report-model"><b>{model.icon}</b><strong>{html.escape(model.name)}</strong>'
                    f'<p>{html.escape(model.description)}</p></div>'
                )


def report_revenue_figure(table: pd.DataFrame, log_scale: bool):
    """Plot approximations only; keep the exact report amounts in customdata."""
    figure = px.bar(
        table, x="Período", y="Receita",
        color_discrete_sequence=[DESIGN_TOKENS["cyan"]],
    )
    figure.update_traces(
        customdata=table["Receita"].map(moeda),
        hovertemplate="%{x|%m/%Y}<br>Receita: %{customdata}<extra></extra>",
    )
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": DESIGN_TOKENS["text"]},
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        xaxis_title="Período", yaxis_title="Receita (R$)",
        hoverlabel={"bgcolor": DESIGN_TOKENS["panel"]},
    )
    if log_scale and not table.empty and table["Receita"].gt(0).all():
        ticks, labels = _log_currency_ticks(table["Receita"])
        figure.update_yaxes(type="log", tickvals=ticks, ticktext=labels, title="Receita (R$ · escala log)")
    else:
        figure.update_yaxes(type="linear", tickformat="~s")
    return figure


def _render_preview(document) -> None:
    st.html(
        f'<div class="report-preview-head"><div><em>PRÉ-VISUALIZAÇÃO</em><strong>{html.escape(document.model.name)}</strong>'
        f'<p>{html.escape(document.source)} · {html.escape(document.scope)} · {html.escape(document.period)}</p></div>'
        f'<span>{numero(document.records)} registros</span></div>'
    )
    with st.container(key="report-preview-kpis"):
        columns = st.columns(min(len(document.indicators), 4))
        for index, (label, value) in enumerate(document.indicators):
            with columns[index % len(columns)]:
                st.html(
                    f'<div class="report-kpi"><span>{html.escape(label)}</span>'
                    f'<strong>{html.escape(_format_indicator(label, value))}</strong></div>'
                )
    for name, table in document.tables:
        if table.empty:
            continue
        st.subheader(name)
        if name == "Evolução temporal" and {"Período", "Receita"}.issubset(table.columns):
            positive = table["Receita"].gt(0).all()
            extreme_range = positive and table["Receita"].max() / table["Receita"].min() > 1000
            log_scale = st.toggle(
                "Escala logarítmica da prévia", value=bool(extreme_range),
                disabled=not positive, key="report_revenue_log",
                help="Altera somente a escala deste gráfico; valores e arquivos exportados permanecem integrais.",
            )
            st.caption(
                "Escala logarítmica: distâncias iguais representam razões, não diferenças monetárias."
                if log_scale and positive else "Escala linear: inclui zeros e valores negativos."
            )
            figure = report_revenue_figure(table, log_scale)
            st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
        else:
            st.dataframe(table.head(20), width="stretch", hide_index=True)
        if len(table) > 20:
            st.caption(f"Prévia limitada a 20 de {len(table)} linhas. O arquivo mantém o conteúdo integral aplicável.")
        if name == "Dados do escopo":
            break
    if document.alerts:
        for alert in document.alerts:
            st.warning(alert)
    with st.expander("Metodologia e limites", expanded=False):
        for item in document.methodology:
            st.write(f"• {item}")


def render_reports_dashboard(base_df: pd.DataFrame, filtered_df: pd.DataFrame, source: str) -> None:
    with st.container(key="report-native-title"):
        st.title("Relatórios")
    anomalies = detect_extreme_monetary_values(filtered_df)
    period = "Período não disponível"
    if not filtered_df.empty and "Data" in filtered_df:
        period = f"{filtered_df['Data'].min():%d/%m/%Y}–{filtered_df['Data'].max():%d/%m/%Y}"
    warning = f"{len(anomalies)} valores atípicos preservados" if len(anomalies) else "Sem extremos sinalizados"
    st.html(
        f"""<div class="report-hero"><div><div class="report-eyebrow">DOCUMENTOS E EXPORTAÇÕES</div>
        <div class="report-title">Central de Relatórios</div>
        <div class="report-subtitle">Transforme dados em documentos executivos claros, verificáveis e prontos para compartilhar.</div></div>
        <div class="report-meta"><span>{html.escape(source)}</span><span>{period}</span>
        <span>{numero(len(filtered_df))} registros no recorte</span><span>{len(REPORT_MODELS)} modelos</span>
        <span class="report-warning">{warning}</span></div></div>"""
    )
    _render_catalog()
    st.html('<div class="report-section"><span>Configuração</span><small>Geração local e sob demanda</small></div>')
    controls = st.columns([1.35, 1.1, 0.8])
    with controls[0]:
        model_name = st.selectbox("Modelo", [model.name for model in REPORT_MODELS], key="report_model")
    with controls[1]:
        scope_label = st.selectbox(
            "Escopo dos dados",
            ["Recorte comercial filtrado", "Base carregada após período rápido"],
            key="report_scope",
        )
    with controls[2]:
        format_label = st.selectbox("Formato", ["CSV (ZIP)", "Excel", "PDF"], key="report_format")
    model = next(item for item in REPORT_MODELS if item.name == model_name)
    selected_df = filtered_df if scope_label == "Recorte comercial filtrado" else base_df
    st.info(
        f"{scope_label}: {numero(len(selected_df))} registros. Alterar este controle não modifica os filtros globais."
    )
    document = build_report_document(model.key, selected_df, source, scope_label)
    signature = f"{model.key}:{format_label}:{scope_label}:{dataframe_fingerprint(selected_df)}"
    if st.session_state.get("report_download_signature") != signature:
        st.session_state.report_download_signature = None
        st.session_state.report_download_content = None
        st.session_state.report_download_name = None
        st.session_state.report_download_mime = None

    st.html('<div class="report-section"><span>Pré-visualização funcional</span><small>Mesma estrutura consolidada usada na exportação</small></div>')
    _render_preview(document)
    st.html('<div class="report-section"><span>Preparar arquivo</span><small>Nenhum arquivo é salvo automaticamente</small></div>')
    left, right = st.columns([1, 1.4])
    with left:
        if st.button("Preparar relatório", type="primary", width="stretch", key="prepare_report_file"):
            started = time.perf_counter()
            try:
                with st.status("Gerando arquivo localmente...", expanded=True) as status:
                    content, filename, mime = export_report(document, format_label)
                    st.session_state.report_download_content = content
                    st.session_state.report_download_name = filename
                    st.session_state.report_download_mime = mime
                    st.session_state.report_download_signature = signature
                    status.update(label="Arquivo validado e pronto", state="complete", expanded=False)
                st.session_state.performance_telemetry.record(
                    "exportacao_relatorio", time.perf_counter() - started, rows=len(selected_df)
                )
                st.rerun()
            except Exception as error:
                st.session_state.performance_telemetry.record(
                    "exportacao_relatorio", time.perf_counter() - started, rows=len(selected_df), failed=True
                )
                st.error(f"Não foi possível gerar o relatório local. Tipo técnico: {type(error).__name__}.")
    with right:
        if st.session_state.get("report_download_content") is not None:
            st.download_button(
                "Baixar arquivo preparado",
                data=st.session_state.report_download_content,
                file_name=st.session_state.report_download_name,
                mime=st.session_state.report_download_mime,
                type="primary",
                width="stretch",
                key="download_prepared_report",
            )
            size = len(st.session_state.report_download_content)
            st.caption(f"{st.session_state.report_download_name} · {size / 1024:.1f} KB")
        else:
            st.caption("Escolha o modelo, o escopo e o formato; depois prepare o arquivo para habilitar o download.")
