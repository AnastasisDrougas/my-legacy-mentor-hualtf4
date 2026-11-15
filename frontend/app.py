from __future__ import annotations

import html as html_lib

import streamlit as st

from api.backend_client import BackendError, check_health, send_chat

APP_NAME = "Knowledge Legacy AI"

MODES = {
    "ask": {
        "label": "Ask Senior",
        "title": "Ask your Senior",
        "description": (
            "Get technical answers grounded in the Senior Engineer's "
            "knowledge and experience."
        ),
    },
    "mentor": {
        "label": "Mentor Mode",
        "title": "Learn with your Senior",
        "description": (
            "Explore problems through questions, explanations "
            "and step-by-step guidance."
        ),
    },
}

# ---------------------------------------------------------
# Lucide icons (inline SVG, 24x24 grid, 1.75 stroke)
# ---------------------------------------------------------

_ICON_PATHS = {
    "layers": (
        '<path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 '
        '3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z"/>'
        '<path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"/>'
        '<path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"/>'
    ),
    "user": (
        '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>'
        '<circle cx="12" cy="7" r="4"/>'
    ),
    "wrench": (
        '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77'
        'a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 '
        '7.94-7.94l-3.76 3.76z"/>'
    ),
    "graduation-cap": (
        '<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0'
        'L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/>'
        '<path d="M22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>'
    ),
    "message-square": (
        '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
    ),
    "info": (
        '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>'
    ),
}


def icon(name: str, size: int = 16) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f"{_ICON_PATHS[name]}</svg>"
    )


def render_html(markup: str) -> None:
    """Render raw HTML. Lines are joined so markdown never treats
    indentation as a code block."""
    compact = " ".join(line.strip() for line in markup.strip().splitlines())
    st.markdown(compact, unsafe_allow_html=True)


def esc(value: object) -> str:
    return html_lib.escape(str(value))


st.set_page_config(
    page_title=APP_NAME,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Design system
#
# Spacing scale : 4 / 8 / 12 / 16 / 24 / 32 px
# Radii         : 6 (controls) / 8 (inputs, buttons) / 12 (cards)
# Accent        : indigo (single primary color)
# Type          : Space Grotesk, 12 / 13 / 14 / 15 / 24 px; weights 400, 500, 600
# ---------------------------------------------------------

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&display=swap');

        :root {
            color-scheme: dark;

            --bg: #0f1115;
            --surface: #161a22;
            --surface-muted: #1c212b;
            --border: #262c38;
            --border-strong: #343c4b;
            --text: #e6e9ef;
            --text-muted: #a3acba;
            --text-subtle: #8b95a5;

            --accent: #4f46e5;
            --accent-hover: #4338ca;
            --accent-text: #a5b4fc;
            --accent-soft: rgba(99, 102, 241, .16);

            --success: #4ade80;
            --success-bg: rgba(34, 197, 94, .12);
            --warning: #fbbf24;
            --warning-bg: rgba(245, 158, 11, .12);
            --error: #f87171;
            --error-bg: rgba(239, 68, 68, .12);
            --info: #60a5fa;
            --info-bg: rgba(59, 130, 246, .12);

            --s1: 4px;
            --s2: 8px;
            --s3: 12px;
            --s4: 16px;
            --s5: 24px;
            --s6: 32px;

            --r-sm: 6px;
            --r-md: 8px;
            --r-lg: 12px;

            --ease: 150ms ease;
            --font: 'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                    Roboto, 'Helvetica Neue', Arial, sans-serif;
        }

        /* ---------- Base ---------- */

        html, body, .stApp,
        .stApp button, .stApp input, .stApp textarea,
        .stApp p, .stApp label, .stApp li,
        .stApp h1, .stApp h2, .stApp h3, .stApp h4,
        .stApp div[data-testid="stMarkdownContainer"],
        .stApp span:not([data-testid="stIconMaterial"]) {
            font-family: var(--font);
        }

        .stApp {
            background-color: var(--bg);
            color: var(--text);
            -webkit-font-smoothing: antialiased;
        }

        .stApp p, .stApp li, .stApp label {
            color: var(--text);
            font-size: 15px;
            line-height: 1.6;
        }

        #MainMenu, footer,
        [data-testid="stDecoration"],
        [data-testid="stMainMenu"],
        [data-testid="stToolbarActions"],
        [data-testid="stAppDeployButton"],
        .stAppDeployButton {
            display: none !important;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        /* Sidebar open / close controls must stay visible */
        [data-testid="stExpandSidebarButton"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarCollapseButton"] button {
            color: var(--text-muted);
        }

        .block-container {
            max-width: 960px;
            padding: var(--s6) var(--s5) 7rem var(--s5);
        }

        hr {
            border: 0;
            border-top: 1px solid var(--border);
            margin: var(--s4) 0;
        }

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {
            color: var(--text-subtle);
            font-size: 13px;
            line-height: 1.5;
        }

        /* Keyboard focus */
        .stApp button:focus-visible,
        .stApp [role="radio"]:focus-visible,
        .stApp summary:focus-visible,
        .stApp a:focus-visible {
            outline: 2px solid var(--accent);
            outline-offset: 2px;
        }

        /* ---------- Sidebar ---------- */

        [data-testid="stSidebar"] {
            background-color: var(--surface);
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebarUserContent"] {
            padding: var(--s5) var(--s4) var(--s4) var(--s4);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: var(--s3);
        }

        .brand-mark {
            width: 32px;
            height: 32px;
            border-radius: var(--r-md);
            background: var(--accent);
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .brand-name {
            color: var(--text);
            font-size: 14px;
            font-weight: 600;
            line-height: 1.2;
        }

        .brand-sub {
            color: var(--text-subtle);
            font-size: 12px;
            line-height: 1.3;
        }

        .section-label {
            color: var(--text-subtle);
            font-size: 11px;
            font-weight: 500;
            letter-spacing: .06em;
            text-transform: uppercase;
            margin: var(--s5) 0 var(--s2) 0;
        }

        .profile-card {
            display: flex;
            gap: var(--s3);
            align-items: flex-start;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--r-lg);
            padding: var(--s4);
        }

        .profile-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--surface-muted);
            color: var(--text-muted);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .profile-title {
            color: var(--text);
            font-size: 14px;
            font-weight: 600;
            line-height: 1.3;
        }

        .profile-meta {
            color: var(--text-subtle);
            font-size: 13px;
            line-height: 1.45;
            margin-top: var(--s1);
        }

        .note {
            display: flex;
            gap: var(--s2);
            align-items: flex-start;
            background: var(--info-bg);
            color: var(--info);
            border-radius: var(--r-md);
            padding: var(--s3);
            margin-top: var(--s3);
            font-size: 13px;
            line-height: 1.45;
        }

        .note svg { flex-shrink: 0; margin-top: 2px; }

        /* Mode selector */
        [data-testid="stSidebar"] [role="radiogroup"] {
            gap: var(--s1);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label {
            width: 100%;
            padding: var(--s2) var(--s3);
            border-radius: var(--r-md);
            border: 1px solid transparent;
            transition: background-color var(--ease), border-color var(--ease);
            cursor: pointer;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background: var(--surface-muted);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
            background: var(--accent-soft);
            border-color: rgba(129, 140, 248, .4);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label p {
            font-size: 14px;
            font-weight: 500;
        }

        /* Buttons */
        .stApp .stButton > button {
            height: 36px;
            min-height: 36px;
            padding: 0 var(--s4);
            border-radius: var(--r-md);
            border: 1px solid var(--border-strong);
            background: var(--surface);
            color: var(--text);
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 1px 2px rgba(16, 24, 40, .04);
            transition: background-color var(--ease), border-color var(--ease),
                        color var(--ease);
        }

        .stApp .stButton > button p {
            font-size: 14px;
            font-weight: 500;
            color: inherit;
        }

        .stApp .stButton > button:hover {
            background: var(--surface-muted);
            border-color: var(--border-strong);
            color: var(--text);
        }

        .stApp .stButton > button:active {
            background: var(--border);
        }

        .stApp .stButton > button:disabled {
            background: var(--surface-muted);
            color: #6b7586;
            border-color: var(--border);
            box-shadow: none;
            cursor: not-allowed;
        }

        /* Status pill */
        .status {
            display: inline-flex;
            align-items: center;
            gap: var(--s2);
            border-radius: 999px;
            padding: 4px 12px 4px 10px;
            font-size: 13px;
            font-weight: 500;
            line-height: 1.4;
        }

        .status .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
        }

        .status.success { background: var(--success-bg); color: var(--success); }
        .status.warning { background: var(--warning-bg); color: var(--warning); }
        .status.error   { background: var(--error-bg);   color: var(--error); }

        .sidebar-footer {
            color: var(--text-subtle);
            font-size: 12px;
            margin-top: var(--s5);
        }

        /* ---------- Page header ---------- */

        .page-header {
            padding-bottom: var(--s5);
            margin-bottom: var(--s5);
            border-bottom: 1px solid var(--border);
        }

        .breadcrumb {
            color: var(--text-subtle);
            font-size: 13px;
            margin-bottom: var(--s2);
        }

        .breadcrumb .sep { margin: 0 var(--s2); color: var(--border-strong); }
        .breadcrumb .current { color: var(--text-muted); }

        .page-title {
            color: var(--text);
            font-size: 24px;
            font-weight: 600;
            letter-spacing: -0.015em;
            line-height: 1.25;
            margin: 0 0 var(--s2) 0;
            padding: 0;
        }

        .page-desc {
            color: var(--text-muted) !important;
            font-size: 15px;
            line-height: 1.6;
            margin: 0;
            max-width: 640px;
        }

        /* ---------- Empty state ---------- */

        .empty {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--r-lg);
            padding: var(--s6);
            margin-bottom: var(--s4);
        }

        .empty-title {
            color: var(--text);
            font-size: 18px;
            font-weight: 600;
            letter-spacing: -0.01em;
            margin: 0 0 var(--s2) 0;
        }

        .empty-text {
            color: var(--text-muted) !important;
            margin: 0;
            max-width: 560px;
        }

        .cap-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--r-lg);
            padding: var(--s4) var(--s5);
            height: 100%;
            transition: border-color var(--ease);
        }

        .cap-card:hover { border-color: var(--border-strong); }

        .cap-icon {
            width: 32px;
            height: 32px;
            border-radius: var(--r-md);
            background: var(--accent-soft);
            color: var(--accent-text);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: var(--s3);
        }

        .cap-title {
            color: var(--text);
            font-size: 14px;
            font-weight: 600;
            margin-bottom: var(--s1);
        }

        .cap-text {
            color: var(--text-muted) !important;
            font-size: 14px !important;
            line-height: 1.5;
            margin: 0;
        }

        .hint {
            color: var(--text-subtle);
            font-size: 13px;
            margin-top: var(--s4);
        }

        /* ---------- Chat ---------- */

        [data-testid="stChatMessage"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--r-lg);
            padding: var(--s4) var(--s5);
            margin-bottom: var(--s3);
            gap: var(--s4);
        }

        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
            background: var(--surface-muted);
        }

        [data-testid="stChatMessageAvatarUser"] {
            background: #344054;
            color: #ffffff;
            border-radius: var(--r-md);
        }

        [data-testid="stChatMessageAvatarAssistant"] {
            background: var(--accent);
            color: #ffffff;
            border-radius: var(--r-md);
        }

        [data-testid="stChatMessage"] p {
            font-size: 15px;
            line-height: 1.65;
        }

        [data-testid="stChatMessage"] code {
            font-size: 13px;
            border-radius: var(--r-sm);
        }

        /* Chat input */
        [data-testid="stChatInput"] {
            background: var(--surface);
            border: 1px solid var(--border-strong);
            border-radius: var(--r-lg);
            box-shadow: 0 1px 2px rgba(16, 24, 40, .05);
            transition: border-color var(--ease), box-shadow var(--ease);
        }

        [data-testid="stChatInput"]:focus-within {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, .35);
        }

        [data-testid="stChatInput"] textarea {
            font-size: 15px;
            color: var(--text);
        }

        [data-testid="stChatInput"] textarea::placeholder {
            color: var(--text-subtle);
        }

        [data-testid="stChatInput"] button {
            background: var(--accent);
            color: #ffffff;
            border-radius: var(--r-md);
            transition: background-color var(--ease);
        }

        [data-testid="stChatInput"] button:hover:not(:disabled) {
            background: var(--accent-hover);
        }

        [data-testid="stChatInput"] button:disabled {
            background: var(--surface-muted);
            color: #6b7586;
        }

        /* ---------- Sources ---------- */

        div[data-testid="stExpander"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--r-md);
            margin-top: var(--s3);
        }

        div[data-testid="stExpander"] summary {
            padding: var(--s2) var(--s4);
            transition: background-color var(--ease);
        }

        div[data-testid="stExpander"] summary:hover {
            background: var(--surface-muted);
        }

        div[data-testid="stExpander"] summary p {
            font-size: 13px;
            font-weight: 500;
            color: var(--text-muted);
        }

        .source {
            padding: var(--s3) 0;
            border-bottom: 1px solid var(--border);
        }

        .source:last-child { border-bottom: 0; padding-bottom: 0; }
        .source:first-child { padding-top: 0; }

        .source-title {
            color: var(--text);
            font-size: 14px;
            font-weight: 500;
        }

        .source-index { color: var(--text-subtle); margin-right: var(--s2); }

        .source-meta {
            color: var(--text-subtle);
            font-size: 12px;
            margin-top: 2px;
        }

        .source-excerpt {
            color: var(--text-muted);
            font-size: 13px;
            line-height: 1.55;
            margin-top: var(--s2);
        }

        /* ---------- Alerts and spinner ---------- */

        [data-testid="stAlert"] {
            border-radius: var(--r-md);
            border: 1px solid var(--border);
        }

        [data-testid="stSpinner"] p,
        [data-testid="stSpinner"] {
            color: var(--text-muted);
            font-size: 14px;
        }

        /* ---------- Responsive ---------- */

        @media (max-width: 900px) {
            .block-container { padding: var(--s5) var(--s4) 7rem var(--s4); }
            .page-title { font-size: 22px; }
        }

        @media (max-width: 640px) {
            .block-container { padding: var(--s4) var(--s3) 7rem var(--s3); }
            .page-title { font-size: 20px; }
            .empty { padding: var(--s5) var(--s4); }
            [data-testid="stChatMessage"] { padding: var(--s3) var(--s4); }
        }

        @media (prefers-reduced-motion: reduce) {
            * { transition: none !important; animation: none !important; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "mode" not in st.session_state:
    st.session_state.mode = "ask"


def reset_conversation() -> None:
    st.session_state.messages = []


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return

    with st.expander(f"Knowledge sources ({len(sources)})"):
        items = []
        for index, source in enumerate(sources, start=1):
            title = esc(source.get("title", "Untitled source"))
            doc_id = esc(source.get("document_id", "N/A"))
            excerpt = source.get("excerpt")
            excerpt_html = (
                f'<div class="source-excerpt">'
                f'{esc(excerpt).replace(chr(10), "<br>")}</div>'
                if excerpt
                else ""
            )
            items.append(
                '<div class="source">'
                '<div class="source-title">'
                f'<span class="source-index">{index}.</span>{title}</div>'
                f'<div class="source-meta">Document ID: {doc_id}</div>'
                f"{excerpt_html}"
                "</div>"
            )
        render_html("".join(items))


def status_pill(kind: str, text: str) -> None:
    render_html(
        f'<span class="status {kind}" role="status">'
        f'<span class="dot"></span>{esc(text)}</span>'
    )


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:

    render_html(
        f"""
        <div class="brand">
            <div class="brand-mark">{icon("layers", 18)}</div>
            <div>
                <div class="brand-name">{APP_NAME}</div>
                <div class="brand-sub">Senior Digital Twin</div>
            </div>
        </div>
        """
    )

    render_html('<div class="section-label">Profile</div>')

    render_html(
        f"""
        <div class="profile-card">
            <div class="profile-avatar">{icon("user", 18)}</div>
            <div>
                <div class="profile-title">Senior Software Engineer</div>
                <div class="profile-meta">
                    Technical expertise, engineering decisions
                    and mentoring experience.
                </div>
            </div>
        </div>
        <div class="note">
            {icon("info", 16)}
            <span>
                The Senior persona profile will be populated
                when AI persona integration is available.
            </span>
        </div>
        """
    )

    render_html('<div class="section-label">Conversation mode</div>')

    selected_mode = st.radio(
        "Choose interaction style",
        options=list(MODES),
        format_func=lambda key: MODES[key]["label"],
        index=list(MODES).index(st.session_state.mode),
        label_visibility="collapsed",
    )

    if selected_mode != st.session_state.mode:
        st.session_state.mode = selected_mode
        reset_conversation()
        st.rerun()

    render_html('<div class="section-label">Session</div>')

    if st.button(
        "Clear conversation",
        use_container_width=True,
        disabled=not st.session_state.messages,
    ):
        reset_conversation()
        st.rerun()

    render_html('<div class="section-label">System status</div>')

    try:
        health = check_health()

        if health.get("status") == "ok":
            status_pill("success", "Backend connected")
        else:
            status_pill("warning", "Unexpected backend response")

    except BackendError:
        status_pill("error", "Backend disconnected")

    render_html(f'<div class="sidebar-footer">{APP_NAME} &middot; Prototype</div>')


# ---------------------------------------------------------
# Main interface
# ---------------------------------------------------------

mode_info = MODES[st.session_state.mode]

render_html(
    f"""
    <div class="page-header">
        <div class="breadcrumb">
            Senior Digital Twin<span class="sep">/</span>
            <span class="current">{mode_info['label']}</span>
        </div>
        <div class="page-title" role="heading" aria-level="1">{mode_info['title']}</div>
        <p class="page-desc">{mode_info['description']}</p>
    </div>
    """
)

# ---------------------------------------------------------
# Empty state
# ---------------------------------------------------------

if not st.session_state.messages:

    render_html(
        """
        <div class="empty">
            <div class="empty-title" role="heading" aria-level="2">Your Senior Engineer is available</div>
            <p class="empty-text">
                Access technical knowledge, engineering experience
                and decision-making insights preserved through AI.
            </p>
        </div>
        """
    )

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        render_html(
            f"""
            <div class="cap-card">
                <div class="cap-icon">{icon("wrench", 18)}</div>
                <div class="cap-title">Technical problems</div>
                <p class="cap-text">
                    Understand architecture, debugging, incidents
                    and engineering decisions.
                </p>
            </div>
            """
        )

    with col2:
        render_html(
            f"""
            <div class="cap-card">
                <div class="cap-icon">{icon("graduation-cap", 18)}</div>
                <div class="cap-title">Engineering guidance</div>
                <p class="cap-text">
                    Learn how an experienced engineer approaches
                    complex technical challenges.
                </p>
            </div>
            """
        )

    render_html(
        '<div class="hint">'
        "Start a conversation using the message field below."
        "</div>"
    )

# ---------------------------------------------------------
# Chat history
# ---------------------------------------------------------

for message in st.session_state.messages:

    avatar = "user" if message["role"] == "user" else "assistant"

    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        render_sources(message.get("sources", []))


# ---------------------------------------------------------
# Chat input and response
# ---------------------------------------------------------

prompt = st.chat_input(
    "Ask your Senior Engineer a technical question..."
)

if prompt:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user", avatar="user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="assistant"):

        with st.spinner("Generating response..."):

            try:
                result = send_chat(
                    prompt,
                    st.session_state.mode,
                )

                answer = result.get(
                    "answer",
                    "The backend returned an empty answer.",
                )

                sources = result.get("sources", [])

                st.markdown(answer)
                render_sources(sources)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    }
                )

            except BackendError as exc:

                st.error(
                    "Unable to get a response from the Senior Digital Twin."
                )

                st.caption(str(exc))

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            "I could not process your request "
                            "because the backend is unavailable."
                        ),
                        "sources": [],
                    }
                )