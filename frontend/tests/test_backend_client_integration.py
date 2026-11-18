"""Frontend HTTP client against real FastAPI endpoints, with only AI mocked."""
import os
import socket
import sys
import threading
from pathlib import Path

import pytest
import uvicorn

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'frontend'))
sys.path.insert(0, str(ROOT / 'backend'))

from app import database
from app.main import app
from app.schemas import ChatResponse, Source
from app.services import ai_service
from api import backend_client as api


@pytest.fixture
def live_api(monkeypatch, tmp_path):
    monkeypatch.setattr(database, 'get_database_path', lambda: tmp_path / 'test.db')
    monkeypatch.setenv('UPLOAD_DIR', str(tmp_path / 'uploads'))
    database.init_db()

    def fake_answer(request):
        return ChatResponse(
            answer=f'Explanation: {request.question}', mode=request.mode,
            sources=[Source(source_id='ADR-001', title='Architecture Record', type='adr')],
        )

    monkeypatch.setattr(ai_service, 'generate_answer', fake_answer)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    config = uvicorn.Config(app, host='127.0.0.1', port=port, log_level='error', lifespan='off')
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    import time
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    assert server.started
    monkeypatch.setattr(api, 'BACKEND_URL', f'http://127.0.0.1:{port}')
    try:
        yield
    finally:
        server.should_exit = True
        thread.join(timeout=5)


def test_chat_history_continue_and_switch_mode(live_api):
    assert api.check_health()['status'] == 'ok'
    assert api.list_conversations() == []
    first = api.send_chat('First question', 'ask')
    cid = first['conversation_id']
    assert first['sources'][0]['source_id'] == 'ADR-001'
    assert api.list_conversations()[0]['id'] == cid
    second = api.send_chat('Followup', 'mentor', cid)
    assert second['conversation_id'] == cid
    history = api.get_conversation(cid)['messages']
    assert [m['role'] for m in history] == ['user', 'assistant', 'user', 'assistant']
    assert history[-1]['mode'] == 'mentor'
    assert history[-1]['sources'][0]['type'] == 'adr'
    new_chat = api.send_chat('New session', 'ask')
    assert new_chat['conversation_id'] != cid
    assert len(api.list_conversations()) == 2


def test_invalid_conversation_does_not_create_history(live_api):
    with pytest.raises(api.BackendError, match='Conversation not found'):
        api.send_chat('Question', 'ask', 'missing-id')
    assert api.list_conversations() == []


def test_document_upload_status_and_validation(live_api):
    result = api.upload_document('new-knowledge.md', b'# A new decision\n', 'text/markdown')
    assert result['filename'] == 'new-knowledge.md'
    assert result['status'] == 'uploaded'
    assert result['id']
    with pytest.raises(api.BackendError, match='Unsupported file type'):
        api.upload_document('invalid.exe', b'junk', 'application/octet-stream')
    with pytest.raises(api.BackendError, match='Empty files'):
        api.upload_document('empty.txt', b'', 'text/plain')
