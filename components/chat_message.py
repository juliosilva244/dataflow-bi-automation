import html
import re

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

    role = message.get(
        "role",
        "assistant",
    )

    content = sanitize_content(
        message.get(
            "content",
            "",
        )
    )

    if role == "user":

        avatar = "🔴"

        background = "#111827"

        border = "#7f1d1d"

        title = "Você"

    else:

        avatar = "🤖"

        background = "#0f172a"

        border = "#0ea5e9"

        title = "AI BI Assistant"

    with st.container():

        st.markdown(
            f"""
<div style="
    background:{background};
    border:1px solid {border};
    border-radius:16px;
    padding:16px;
    margin-bottom:14px;
">
<div style="
    display:flex;
    align-items:center;
    gap:10px;
    font-weight:700;
    margin-bottom:12px;
">
<span>{avatar}</span>
<span>{title}</span>
</div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            content
        )


def render_chat_history(messages):

    for message in messages:

        render_chat_message(
            message
        )