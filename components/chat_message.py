import html
import re

import pandas as pd
import streamlit as st


def sanitize_content(content):

    content = str(content)

    content = re.sub(
        r"<[^>]*>",
        "",
        content,
        flags=re.IGNORECASE,
    )

    content = html.unescape(content)

    content = content.replace(
        "```",
        "",
    )

    return content.strip()


def render_chat_message(message):
    role = "user" if message.get("role") == "user" else "assistant"
    with st.chat_message(role):
        presentation = message.get("presentation")
        if role == "assistant" and isinstance(presentation, dict) and presentation.get("version") == 1:
            render_progressive_answer(presentation)
        else:
            # Old histories and public error messages retain their complete content.
            st.markdown(prepare_chat_markdown(message.get("content", "")))


def render_progressive_answer(presentation):
    st.markdown(prepare_chat_markdown(presentation["lead"]))
    rows = presentation.get("rows", [])
    if rows:
        table = pd.DataFrame([(sanitize_content(label), sanitize_content(value)) for label, value in rows], columns=["Indicador", "Valor / escopo"])
        st.dataframe(table, hide_index=True, width="stretch", height=min(350, 35 * (len(table) + 1) + 3))
    if presentation.get("interpretation"):
        st.markdown(prepare_chat_markdown(presentation["interpretation"]))
    for warning in dict.fromkeys(presentation.get("warnings", [])):
        st.warning(sanitize_content(warning))
    if presentation.get("evidence"):
        with st.expander("Evidências verificadas", expanded=False):
            for fact in presentation["evidence"]:
                st.markdown(prepare_chat_markdown("- " + fact))
    if presentation.get("methodology"):
        if presentation.get("reconciliation"):
            with st.expander("Reconciliação financeira", expanded=False):
                st.dataframe(pd.DataFrame(presentation["reconciliation"]), hide_index=True, width="stretch")
                st.caption("Receita atual + anterior + fora das janelas = consolidado. Denominadores únicos não são necessariamente aditivos; a comparação temporal não abrange obrigatoriamente todo o consolidado.")
        with st.expander("Metodologia e limitações", expanded=False):
            for limitation in presentation["methodology"]:
                st.markdown(prepare_chat_markdown("- " + limitation))


def prepare_chat_markdown(content):
    """Currency is literal text, not a pair of accidental LaTeX delimiters."""
    content = sanitize_content(content)
    content = re.sub(r"\\\[(.*?)\\\]", lambda match: "\n$$\n" + match[1] + "\n$$\n", content, flags=re.DOTALL)
    content = re.sub(r"\\\((.*?)\\\)", lambda match: "$" + match[1] + "$", content, flags=re.DOTALL)
    return re.sub(r"(?<!\\)R\$", r"R\\$", content)


def render_chat_history(messages):

    for message in messages:

        render_chat_message(
            message
        )
