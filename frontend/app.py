"""MyLegacyMentor — Netcompany-inspired Streamlit interface (Option B).

Uses the existing backend_client contracts. Conversations and documents are
persisted only by FastAPI; Streamlit session state is ephemeral presentation state.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

import streamlit as st

from api.backend_client import (
    BackendError,
    check_health,
    get_conversation,
    list_conversations,
    send_chat,
    upload_document,
)

APP_NAME = "MyLegacyMentor"
MODES = {
    "ask": {
        "label": "Ask Senior",
        "heading": "Ask your Senior",
        "description": "Get technical answers grounded in the Senior Engineer's knowledge and experience.",
    },
    "mentor": {
        "label": "Mentor Mode",
        "heading": "Learn with your Senior",
        "description": "Explore technical challenges through mentoring, reasoning and guided next steps.",
    },
}
SECTION_LABELS = {
    "RECOMMENDATION": "Recommendation",
    "HISTORICAL PRECEDENT": "Historical precedent",
    "WHY IT APPLIES OR DIFFERS": "Why it applies or differs",
    "NEXT STEPS": "Next steps",
    "CONFIDENCE & MISSING EVIDENCE": "Confidence & missing evidence",
}
TITLE_STOPWORDS = {
    "a", "an", "the", "what", "which", "who", "why", "how", "when", "where", "is", "are",
    "was", "were", "do", "does", "did", "should", "could", "would", "can", "you", "we",
    "i", "me", "my", "our", "please", "tell", "about", "before", "after", "to", "of",
    "in", "on", "for", "with", "and", "that", "this", "it", "be", "explain",
}

# Black "</>" code icon (assets/favicon.png, next to this file) replaces the old 🧠 emoji.
_ICON_PATH = Path(__file__).parent / "assets" / "favicon.png"
st.set_page_config(
    page_title=APP_NAME,
    page_icon=str(_ICON_PATH) if _ICON_PATH.exists() else "💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styling based on the supplied Option B reference. The colors are inspired by
# Netcompany's visual identity, not an official reproduced brand template.
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root {
  color-scheme:dark;
  --background:#071b1a;
  --sidebar:#071e1c;
  --panel:#103431;
  --panel-light:#16413d;
  --panel-hover:#214b46;
  --line:#28544e;
  --coral:#ff6459;
  --coral-light:#ff8177;
  --white:#f6fcfc;
  --muted:#b7c9c7;
  --soft:#88a5a1;
}
html,body,.stApp,.stApp button,.stApp input,.stApp textarea,
.stApp p,.stApp label,.stApp li,.stApp h1,.stApp h2,.stApp h3 {
  font-family:'Plus Jakarta Sans',sans-serif;
}
.stApp {
  color:var(--white);
  background:radial-gradient(ellipse 90% 64% at 65% -20%, #10413d 0%, transparent 69%),var(--background);
}
#MainMenu,footer,[data-testid='stDecoration'],[data-testid='stToolbarActions'],
[data-testid='stAppDeployButton'] {display:none!important;}
header[data-testid='stHeader'] {background:transparent;}
.block-container {max-width:1380px;padding:1.6rem 3.2rem 8rem 3.2rem;}
[data-testid='stSidebar'] {background:var(--sidebar);border-right:1px solid #143a36;}
[data-testid='stSidebarUserContent'] {padding:1.1rem 1.05rem 1.5rem;}
.nc-logo {display:flex;align-items:center;gap:0.9rem;margin:0.5rem 0.25rem 2rem;}
.nc-logo-mark {font-size:2.9rem;font-weight:800;transform:skew(-16deg);letter-spacing:-0.35rem;
 color:var(--coral);line-height:1;white-space:nowrap;margin-right:0.5rem;}
.nc-logo-name {color:var(--white);font-size:1.2rem;font-weight:800;letter-spacing:-0.035em;white-space:nowrap;}
.nc-logo-caption {font-size:0.77rem;color:var(--muted);margin-top:0.18rem;}
.nc-rule {height:1px;background:var(--line);margin:1rem 0 1.2rem;opacity:.75;}
.nc-side-label {font-size:0.65rem;font-weight:700;letter-spacing:0.1em;color:#a1bbb7;
 text-transform:uppercase;margin:1.2rem 0 0.6rem 0.52rem;}
[data-testid='stSidebar'] .stButton>button {
 background:transparent;color:var(--white);border:1px solid transparent;border-radius:9px;
 padding:0.42rem 0.65rem;min-height:36px;height:auto;text-align:left;
 justify-content:flex-start;font-size:0.81rem;font-weight:500;line-height:1.4;
}
[data-testid='stSidebar'] .stButton>button p {font-size:0.81rem;font-weight:500;color:inherit;}
[data-testid='stSidebar'] .stButton>button:hover {background:#173e3a;border-color:#26534d;}
[data-testid='stSidebar'] .stButton>button[kind='primary'] {
 background:#24514b;border-left:3px solid var(--coral);font-weight:700;
}
.nc-profile {margin-top:1.5rem;padding:1.15rem 0.3rem 0.3rem;border-top:1px solid var(--line);
 display:flex;gap:0.7rem;align-items:flex-start;}
.nc-profile-circle {background:#24514c;border-radius:50%;width:35px;height:35px;
 display:flex;align-items:center;justify-content:center;flex-shrink:0;color:var(--white);}
.nc-profile strong {color:var(--white);font-size:0.81rem;}
.nc-profile p {font-size:0.72rem!important;line-height:1.5;color:var(--muted)!important;margin:0.2rem 0;}
.nc-backend-status {color:#9ac6b2;font-size:0.73rem;margin:0.8rem 0.45rem 0;}
.nc-backend-status.off {color:var(--coral-light);}
.nc-breadcrumb {color:var(--muted);font-size:0.81rem;margin:0 0 1.8rem;}
.nc-breadcrumb strong {color:var(--coral);font-weight:700;}
.nc-heading {display:flex;align-items:center;gap:1.5rem;margin:0.3rem 0 0.6rem;}
.nc-slash {height:46px;width:10px;background:var(--coral);transform:skew(-22deg);border-radius:1px;flex-shrink:0;}
.nc-heading h1 {color:var(--white);font-size:2.65rem;font-weight:800;letter-spacing:-0.055em;
 line-height:1.16;margin:0;}
.nc-description {color:var(--muted);font-size:0.96rem;line-height:1.6;margin:0 0 1.15rem 3.1rem;}
/* Real, clickable Streamlit radio buttons form the segmented mode selector. */
[data-testid='stMain'] [data-testid='stRadio'] {margin-left:0.1rem;margin-bottom:0.45rem;}
[data-testid='stMain'] [data-testid='stRadio'] [role='radiogroup'] {gap:0;display:flex;flex-wrap:wrap;}
[data-testid='stMain'] [data-testid='stRadio'] [role='radiogroup'] label {
 background:#0f2a28;border:1px solid #2f5853;border-radius:12px;
 padding:0.58rem 1.4rem;min-width:175px;justify-content:center;cursor:pointer;
}
[data-testid='stMain'] [data-testid='stRadio'] [role='radiogroup'] label:has(input:checked) {
 background:linear-gradient(110deg,#bc5148,var(--coral));border-color:var(--coral);
}
[data-testid='stMain'] [data-testid='stRadio'] [role='radiogroup'] label p {font-size:0.89rem;color:var(--white);font-weight:700;}
[data-testid='stMain'] [data-testid='stRadio'] [role='radiogroup'] label:has(input:checked) p {color:var(--white);}
.nc-main-rule {height:1px;background:var(--line);opacity:.85;margin:0.4rem 0 1.8rem;}
.nc-welcome {position:relative;padding:0.5rem 0 0.6rem;}
.nc-eyebrow {font-size:0.71rem;color:var(--muted);font-weight:700;letter-spacing:0.12em;}
.nc-welcome h2 {font-weight:800;font-size:2.35rem;line-height:1.18;letter-spacing:-0.045em;
 color:var(--white);margin:0.6rem 0;}
.nc-welcome h2 span {color:var(--coral);}
.nc-welcome p {font-size:0.95rem;color:var(--muted);line-height:1.65;max-width:780px;}
[data-testid='stMain'] .stButton>button {background:#1a4943;color:var(--white);
 border:1px solid #37635e;border-radius:9px;font-size:0.8rem;min-height:36px;}
[data-testid='stMain'] .stButton>button:hover {background:#285a53;border-color:var(--coral);}
.nc-conversation-label {font-size:0.75rem;font-weight:700;letter-spacing:0.08em;
 color:var(--muted);text-transform:uppercase; margin-bottom:1rem;}
[data-testid='stChatMessage'] {background:transparent;border:0;padding:0.8rem 0;}
[data-testid='stChatMessageAvatarAssistant'] {background:var(--coral);color:#17302c;border-radius:10px;}
[data-testid='stChatMessageAvatarUser'] {background:#20534d;color:var(--white);border-radius:10px;}
[data-testid='stChatMessage'] p,[data-testid='stChatMessage'] li {color:var(--white);line-height:1.65;}
[data-testid='stVerticalBlockBorderWrapper']>div {border-color:#305a55!important;border-radius:14px!important;}
.nc-answer-heading {font-size:0.86rem;font-weight:800;color:var(--coral);}
.nc-answer-sub {color:var(--muted);font-size:0.72rem;margin:0.2rem 0 0.75rem;}
.nc-answer-section {font-size:0.91rem;font-weight:800;color:var(--coral);margin:0.9rem 0 0.23rem;}
[data-testid='stExpander'] {background:#123734;border:1px solid #2a5953;border-radius:12px;}
.nc-source-name {color:var(--white);font-size:0.82rem;font-weight:700;}
.nc-source-meta {color:var(--muted);font-size:0.71rem;margin:0.2rem 0 0.65rem;}
[data-testid='stBottom'] {background:linear-gradient(0deg,#071b1a 58%,transparent);}
[data-testid='stChatInput'] {background:#103b36;border:1px solid #3a7770;border-radius:13px;}
[data-testid='stChatInput']:focus-within {border-color:var(--coral);}
[data-testid='stChatInput'] button {color:var(--coral);}
[data-testid='stAlert'] {border-radius:10px;}
[data-testid='stFileUploader'] {background:transparent;}
@media(max-width:1100px) {.block-container{padding:1.4rem 1.5rem 7.5rem;}.nc-heading h1{font-size:2.1rem;}}
@media(max-width:640px) {.block-container{padding:1rem 0.8rem 7rem;}.nc-heading h1{font-size:1.75rem;}
.nc-description{margin-left:0;}.nc-welcome h2{font-size:1.7rem;}}
</style>
""",
    unsafe_allow_html=True,
)


def html_block(markup: str) -> None:
    """Present static layout HTML (all dynamic values must be escaped)."""
    st.markdown(" ".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def title_from_question(question: str) -> str:
    """Create a short title from a question; never call another LLM or store locally."""
    words = re.findall(r"[^\W_]+(?:[-'][^\W_]+)*", question, flags=re.UNICODE)
    keywords = [word for word in words if word.casefold() not in TITLE_STOPWORDS]
    chosen = (keywords or words)[:4]
    return " ".join(chosen).capitalize() if chosen else "Previous conversation"


def split_answer(answer: str) -> tuple[str, list[tuple[str, str]]]:
    """Recognize existing RAG section headings; preserve all unmatched answer text."""
    intro: list[str] = []
    sections: list[tuple[str, str]] = []
    current_label: str | None = None
    current_lines: list[str] = []
    for line in answer.replace("\r\n", "\n").splitlines():
        normalized = re.sub(r"^#{1,6}\s*", "", line.strip()).rstrip(":").upper()
        if normalized in SECTION_LABELS:
            if current_label is not None:
                sections.append((current_label, "\n".join(current_lines).strip()))
            current_label = SECTION_LABELS[normalized]
            current_lines = []
        elif current_label is None:
            intro.append(line)
        else:
            current_lines.append(line)
    if current_label is not None:
        sections.append((current_label, "\n".join(current_lines).strip()))
    return "\n".join(intro).strip(), sections


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"Knowledge sources ({len(sources)})", expanded=False):
        for i, source in enumerate(sources, 1):
            html_block(
                f'<div class="nc-source-name">{i}. {esc(source.get("title") or "Untitled source")}</div>'
                f'<div class="nc-source-meta">{esc(source.get("type") or "Unknown")} · '
                f'Source ID: {esc(source.get("source_id") or "N/A")}</div>'
            )
            if source.get("excerpt"):
                st.caption(str(source["excerpt"]))


def render_message(message: dict) -> None:
    role = message.get("role", "assistant")
    role = role if role in ("user", "assistant") else "assistant"
    content = str(message.get("content") or "")
    with st.chat_message(role):
        if role == "user":
            st.markdown(content)
            return
        mode = message.get("mode", "ask")
        with st.container(border=True):
            html_block(
                f'<div class="nc-answer-heading">{esc("Mentor Mode" if mode == "mentor" else "Ask Senior")}</div>'
                '<div class="nc-answer-sub">MyLegacyMentor · Senior Digital Twin</div>'
            )
            intro, sections = split_answer(content)
            if intro:
                st.markdown(intro)
            for heading, body in sections:
                html_block(f'<div class="nc-answer-section">{esc(heading)}</div>')
                if body:
                    st.markdown(body)
            render_sources(message.get("sources") or [])


def new_conversation() -> None:
    st.session_state.conversation_id = None
    st.session_state.messages = []


def open_conversation(cid: str) -> None:
    # Backend is authoritative; avoid changing mode widget state after instantiation.
    data = get_conversation(cid)
    st.session_state.conversation_id = cid
    st.session_state.messages = data["messages"]


if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "mode_selector" not in st.session_state:
    st.session_state.mode_selector = "ask"


# Sidebar: backend-backed history, real uploads, compact senior profile.
with st.sidebar:
    html_block(
        '<div class="nc-logo"><div class="nc-logo-mark">╱╱</div><div>'
        '<div class="nc-logo-name">MyLegacyMentor</div>'
        '<div class="nc-logo-caption">Senior Digital Twin</div></div></div>'
    )
    if st.button("＋  New conversation", key="new_conversation", use_container_width=True):
        new_conversation()
        st.rerun()
    html_block('<div class="nc-side-label">Recent conversations</div>')
    try:
        conversations = list_conversations()
    except BackendError as exc:
        conversations = []
        st.warning("Conversation history unavailable")
        st.caption(str(exc))
    if not conversations:
        st.caption("No saved conversations yet")
    # Only a temporary per-run cache: no local persistence or additional database.
    for conversation in conversations:
        cid = conversation.get("id")
        if not cid:
            continue
        try:
            details = get_conversation(cid)
            first_question = next(
                (m.get("content", "") for m in details.get("messages", [])
                 if m.get("role") == "user" and str(m.get("content", "")).strip()),
                "",
            )
            title = title_from_question(first_question)
        except BackendError:
            title = "Previous conversation"
        if st.button(
            title,
            key=f"history_{cid}",
            use_container_width=True,
            type="primary" if cid == st.session_state.conversation_id else "secondary",
            help="Open saved conversation",
        ):
            try:
                open_conversation(cid)
            except BackendError as exc:
                st.error(f"Cannot open conversation: {exc}")
            else:
                st.rerun()

    html_block('<div class="nc-rule"></div>')
    html_block('<div class="nc-side-label">Knowledge documents</div>')
    file = st.file_uploader(
        "Upload document", type=["txt", "md", "pdf"], key="knowledge_upload",
        help="TXT, Markdown or PDF. The Backend controls allowed size and ingestion.",
    )
    if file is not None and st.button("Upload selected document", use_container_width=True):
        mime = {"txt": "text/plain", "md": "text/markdown", "pdf": "application/pdf"}
        ext = file.name.rsplit(".", 1)[-1].lower()
        try:
            with st.spinner("Uploading document..."):
                result = upload_document(file.name, file.getvalue(), mime[ext])
            st.success(f"Uploaded {result['filename']} · status: {result['status']}")
            if result["status"] != "ready":
                st.info("Upload accepted; AI retrieval availability has not been verified yet.")
        except (BackendError, KeyError) as exc:
            st.error(f"Upload failed: {exc}")

    try:
        connected = check_health().get("status") == "ok"
        html_block(
            '<div class="nc-backend-status{}">● {}</div>'.format(
                "" if connected else " off", "Backend connected" if connected else "Backend unavailable"
            )
        )
    except BackendError:
        html_block('<div class="nc-backend-status off">● Backend disconnected</div>')
    html_block(
        '<div class="nc-profile"><div class="nc-profile-circle">♙</div><div>'
        '<strong>Senior Software Engineer</strong>'
        '<p>Technical expertise, engineering decisions and mentoring.</p></div></div>'
    )


# Main area: Option B header and genuine working Ask/Mentor selector.
html_block('<div class="nc-breadcrumb">Senior Digital Twin &nbsp; › &nbsp; <strong>MyLegacyMentor</strong></div>')
mode_info = MODES[st.session_state.mode_selector]
html_block(
    f'<div class="nc-heading"><div class="nc-slash"></div><h1>{esc(mode_info["heading"])}</h1></div>'
    f'<div class="nc-description">{esc(mode_info["description"])}</div>'
)
mode = st.radio(
    "Conversation mode",
    options=["ask", "mentor"],
    format_func=lambda value: MODES[value]["label"],
    horizontal=True,
    key="mode_selector",
    label_visibility="collapsed",
)
html_block('<div class="nc-main-rule"></div>')

# Minimal welcome view: no preset questions or illustrative AI responses.
if not st.session_state.messages:
    html_block(
        '<div class="nc-welcome"><div class="nc-eyebrow">WELCOME TO MYLEGACYMENTOR</div>'
        '<h2>Your Senior Engineer is <span>available</span></h2>'
        '<p>Access technical knowledge, engineering experience and decision-making '
        'insights preserved through AI.</p></div>'
    )
else:
    html_block('<div class="nc-conversation-label">Conversation</div>')

for message in st.session_state.messages:
    render_message(message)

prompt = st.chat_input("Ask your Senior Engineer a technical question...")
if prompt:
    pending = {"role": "user", "content": prompt}
    st.session_state.messages.append(pending)
    render_message(pending)
    with st.chat_message("assistant"):
        with st.spinner("Generating response..."):
            try:
                result = send_chat(prompt, mode, st.session_state.conversation_id)
                st.session_state.conversation_id = result["conversation_id"]
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "mode": result["mode"],
                    "sources": result["sources"],
                })
            except BackendError as exc:
                # Backend only persists successful exchanges.
                st.session_state.messages.pop()
                st.error("Unable to get a response from the Senior Digital Twin.")
                st.caption(str(exc))
            else:
                st.rerun()
