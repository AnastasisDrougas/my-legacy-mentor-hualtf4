from __future__ import annotations

import html as html_lib

import streamlit as st

from api.backend_client import BackendError, check_health, send_chat

APP_NAME = "My Legacy Mentor"

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
    "brain": (
        '<path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>'
        '<path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/>'
        '<path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/>'
        '<path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/>'
        '<path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/>'
        '<path d="M3.477 10.896a4 4 0 0 1 .585-.396"/>'
        '<path d="M19.938 10.5a4 4 0 0 1 .585.396"/>'
        '<path d="M6 18a4 4 0 0 1-1.967-.516"/>'
        '<path d="M19.967 17.484A4 4 0 0 1 18 18"/>'
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
# Design system (Material Design 3 / Gemini Tonal Surfaces)
# ---------------------------------------------------------

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');

        :root {
            color-scheme: dark;

            --bg: #131314;
            --surface: #1e1f20;
            --surface-muted: #282a2c;
            --surface-hover: #333537;
            --border: rgba(255, 255, 255, 0.06);
            --border-strong: #444746;

            --text: #e3e3e3;
            --text-muted: #c4c7c5;
            --text-subtle: #8e918f;

            --accent: #8ab4f8;
            --accent-hover: #aecbfa;
            --accent-on: #041e49;
            --accent-text: #a8c7fa;
            --accent-soft: #004a77;
            --ai-gradient: linear-gradient(74deg, #4285f4 0%, #9b72cb 50%, #d96570 100%);

            --success: #81c995;
            --success-bg: rgba(129, 201, 149, 0.14);
            --warning: #fdd663;
            --warning-bg: rgba(253, 214, 99, 0.14);
            --error: #f28b82;
            --error-bg: rgba(242, 139, 130, 0.14);
            --info: #a8c7fa;
            --info-bg: rgba(168, 199, 250, 0.10);

            --s1: 4px;
            --s2: 8px;
            --s3: 12px;
            --s4: 16px;
            --s5: 24px;
            --s6: 32px;

            --r-sm: 12px;
            --r-md: 16px;
            --r-lg: 24px;
            --r-pill: 9999px;

            --ease: 200ms cubic-bezier(0.2, 0, 0, 1);
            --font: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                    Roboto, 'Helvetica Neue', Arial, sans-serif;
            --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
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

        .stApp code, .stApp pre {
            font-family: var(--font-mono);
        }

        .stApp {
            background-color: var(--bg);
            color: var(--text);
            -webkit-font-smoothing: antialiased;
        }

        .stApp p, .stApp li, .stApp label {
            color: var(--text);
            font-size: 15px;
            line-height: 1.65;
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

        /* Sidebar open / close controls */
        [data-testid="stExpandSidebarButton"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarCollapseButton"] button {
            color: var(--text-muted);
            border-radius: var(--r-pill);
            transition: background-color var(--ease), color var(--ease);
        }

        [data-testid="stExpandSidebarButton"]:hover,
        [data-testid="stSidebarCollapseButton"] button:hover {
            background-color: var(--surface-muted);
            color: var(--text);
        }

        .block-container {
            max-width: 800px;
            padding: var(--s6) var(--s5) 8rem var(--s5);
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
            border-right: none;
        }

        [data-testid="stSidebarUserContent"] {
            padding: var(--s5) var(--s4) var(--s4) var(--s4);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: var(--s3);
            padding: 0 var(--s1);
        }

        .brand-mark {
            width: 34px;
            height: 34px;
            border-radius: var(--r-pill);
            background: var(--ai-gradient);
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .brand-name {
            color: var(--text);
            font-size: 15px;
            font-weight: 600;
            letter-spacing: -0.01em;
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
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin: var(--s5) 0 var(--s2) var(--s2);
        }

        .profile-card {
            display: flex;
            gap: var(--s3);
            align-items: flex-start;
            background: var(--surface-muted);
            border: none;
            border-radius: var(--r-md);
            padding: var(--s4);
        }

        .profile-avatar {
            width: 36px;
            height: 36px;
            border-radius: var(--r-pill);
            background: var(--surface-hover);
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
            color: var(--text-muted);
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
            padding: var(--s3) var(--s4);
            margin-top: var(--s3);
            font-size: 12.5px;
            line-height: 1.45;
        }

        .note svg { flex-shrink: 0; margin-top: 2px; }

        /* Mode selector (Tonal Pills) */
        [data-testid="stSidebar"] [role="radiogroup"] {
            gap: var(--s1);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label {
            width: 100%;
            padding: 10px var(--s4);
            border-radius: var(--r-pill);
            border: none;
            transition: background-color var(--ease), color var(--ease);
            cursor: pointer;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background: var(--surface-muted);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
            background: var(--accent-soft);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
            color: var(--accent-text);
            font-weight: 600;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label p {
            font-size: 14px;
            font-weight: 500;
            color: var(--text-muted);
        }

        /* Buttons */
        .stApp .stButton > button {
            height: 40px;
            min-height: 40px;
            padding: 0 var(--s5);
            border-radius: var(--r-pill);
            border: none;
            background: var(--surface-muted);
            color: var(--text);
            font-size: 14px;
            font-weight: 500;
            box-shadow: none;
            transition: background-color var(--ease), color var(--ease);
        }

        .stApp .stButton > button p {
            font-size: 14px;
            font-weight: 500;
            color: inherit;
        }

        .stApp .stButton > button:hover {
            background: var(--surface-hover);
            color: var(--text);
        }

        .stApp .stButton > button:active {
            background: var(--border-strong);
        }

        .stApp .stButton > button:disabled {
            background: rgba(40, 42, 44, 0.45);
            color: var(--text-subtle);
            cursor: not-allowed;
        }

        /* Status pill */
        .status {
            display: inline-flex;
            align-items: center;
            gap: var(--s2);
            border-radius: var(--r-pill);
            padding: 5px 14px 5px 12px;
            font-size: 12.5px;
            font-weight: 500;
            line-height: 1.4;
            margin-left: var(--s1);
        }

        .status .dot {
            width: 7px;
            height: 7px;
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
            padding-left: var(--s2);
        }

        /* ---------- Page header ---------- */

        .page-header {
            padding-bottom: var(--s4);
            margin-bottom: var(--s5);
            border-bottom: 1px solid var(--border);
        }

        .breadcrumb {
            color: var(--text-subtle);
            font-size: 13px;
            margin-bottom: var(--s2);
        }

        .breadcrumb .sep { margin: 0 var(--s2); color: var(--border-strong); }
        .breadcrumb .current { color: var(--accent-text); font-weight: 500; }

        .page-title {
            color: var(--text);
            font-size: 28px;
            font-weight: 600;
            letter-spacing: -0.02em;
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
            background: transparent;
            border: none;
            padding: var(--s3) 0 var(--s5) 0;
            margin-bottom: var(--s2);
        }

        .empty-title {
            background: linear-gradient(90deg, #8ab4f8 0%, #c58af9 55%, #e3e3e3 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 24px;
            font-weight: 600;
            letter-spacing: -0.015em;
            margin: 0 0 var(--s2) 0;
            display: inline-block;
        }

        .empty-text {
            color: var(--text-muted) !important;
            margin: 0;
            max-width: 580px;
        }

        .cap-card {
            background: var(--surface);
            border: none;
            border-radius: var(--r-lg);
            padding: var(--s5);
            height: 100%;
            transition: background-color var(--ease);
        }

        .cap-card:hover {
            background: var(--surface-muted);
        }

        .cap-icon {
            width: 36px;
            height: 36px;
            border-radius: var(--r-pill);
            background: var(--surface-muted);
            color: var(--accent-text);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: var(--s4);
        }

        .cap-card:hover .cap-icon {
            background: var(--surface-hover);
        }

        .cap-title {
            color: var(--text);
            font-size: 15px;
            font-weight: 600;
            margin-bottom: var(--s2);
        }

        .cap-text {
            color: var(--text-muted) !important;
            font-size: 14px !important;
            line-height: 1.55;
            margin: 0;
        }

        .hint {
            color: var(--text-subtle);
            font-size: 13px;
            margin-top: var(--s5);
        }

        /* ---------- Chat (Gemini Stream Style) ---------- */

        [data-testid="stChatMessage"] {
            background: transparent;
            border: none;
            border-radius: 0;
            padding: var(--s3) 0;
            margin-bottom: var(--s4);
            gap: var(--s4);
            align-items: flex-start;
        }

        /* User prompt: right-aligned soft pill bubble */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
            background: var(--surface-muted);
            border-radius: 24px 24px 4px 24px;
            padding: 14px 20px;
            max-width: 82%;
            margin-left: auto;
            flex-direction: row-reverse;
        }

        [data-testid="stChatMessageAvatarUser"] {
            background: var(--surface-hover);
            color: var(--text);
            border-radius: var(--r-pill);
        }

        [data-testid="stChatMessageAvatarAssistant"] {
            background: var(--ai-gradient);
            color: #ffffff;
            border-radius: var(--r-pill);
        }

        [data-testid="stChatMessage"] p {
            font-size: 15px;
            line-height: 1.7;
            color: var(--text);
        }

        [data-testid="stChatMessage"] code {
            font-size: 13px;
            background: var(--surface);
            padding: 2px 6px;
            border-radius: 6px;
        }

        [data-testid="stChatMessage"] pre {
            background: var(--surface) !important;
            border: none !important;
            border-radius: var(--r-md) !important;
            padding: var(--s4) !important;
        }

        /* Floating Pill Chat Input */
        [data-testid="stBottom"] {
            background: linear-gradient(180deg, rgba(19, 19, 20, 0) 0%, #131314 35%);
            padding-top: var(--s4);
        }

        [data-testid="stBottom"] > div {
            max-width: 800px;
            margin: 0 auto;
        }

        [data-testid="stChatInput"] {
            background: var(--surface);
            border: 1px solid transparent;
            border-radius: 28px;
            box-shadow: none;
            padding: 4px 8px;
            transition: background-color var(--ease), border-color var(--ease);
        }

        [data-testid="stChatInput"]:focus-within {
            background: var(--surface-muted);
            border-color: var(--border-strong);
            box-shadow: none;
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
            color: var(--accent-on);
            border-radius: var(--r-pill);
            transition: background-color var(--ease), transform var(--ease);
        }

        [data-testid="stChatInput"] button:hover:not(:disabled) {
            background: var(--accent-hover);
        }

        [data-testid="stChatInput"] button:disabled {
            background: transparent;
            color: var(--text-subtle);
        }

        /* ---------- Sources ---------- */

        div[data-testid="stExpander"] {
            background: var(--surface);
            border: none;
            border-radius: var(--r-md);
            margin-top: var(--s3);
            overflow: hidden;
        }

        div[data-testid="stExpander"] summary {
            padding: 10px var(--s4);
            transition: background-color var(--ease);
        }

        div[data-testid="stExpander"] summary:hover {
            background: var(--surface-muted);
        }

        div[data-testid="stExpander"] summary p {
            font-size: 13px;
            font-weight: 500;
            color: var(--accent-text);
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

        .source-index { color: var(--accent-text); margin-right: var(--s2); }

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
            background: var(--surface);
            border-radius: var(--r-md);
            border: none;
        }

        [data-testid="stSpinner"] p,
        [data-testid="stSpinner"] {
            color: var(--text-muted);
            font-size: 14px;
        }

        /* ---------- Responsive ---------- */

        @media (max-width: 900px) {
            .block-container { padding: var(--s5) var(--s4) 7.5rem var(--s4); }
            .page-title { font-size: 24px; }
        }

        @media (max-width: 640px) {
            .block-container { padding: var(--s4) var(--s3) 7.5rem var(--s3); }
            .page-title { font-size: 21px; }
            [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
                max-width: 92%;
                padding: 12px 16px;
            }
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
            <div class="brand-mark">{icon("brain", 18)}</div>
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