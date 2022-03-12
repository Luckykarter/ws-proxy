import pytest
from fastapi.testclient import TestClient
from app.main import app, _error_message
from uuid import uuid4


@pytest.fixture
def message():
    return {
        "type": "test_message",
        'message': {
            "title": "Test Message",
            "content": "This is the content of test message",
            "success": True
        }
    }


@pytest.fixture
def error_message():
    return {
        "type": "test_message",
        'message': "not a json"
    }


def test_send_message(message):
    with TestClient(app) as client:
        with client.websocket_connect(f'/ws/channel/test/{uuid4()}/') as websocket:
            websocket.send_json(message)
            data = websocket.receive_json()
            assert data['content'] == message['message']['content']
            assert data['title'] == message['message']['title']
            assert data["success"]


def test_error_message(error_message):
    with TestClient(app) as client:
        with client.websocket_connect(f'/ws/channel/test/{uuid4()}/') as websocket:
            websocket.send_json(error_message)
            data = websocket.receive_json()
            assert data['content'] == f'message must be JSON. Received: "{error_message["message"]}"'


def test_get_history(message):
    client_id = str(uuid4())
    channel = 'test'
    with TestClient(app) as client:
        with client.websocket_connect(f'/ws/channel/{channel}/{client_id}/') as websocket:
            websocket.send_json(message)
            websocket.receive_json()
        history = client.get(f'/ws/history/{channel}/{client_id}/')
        history = history.json()
        lines = [x.get('content') for x in history]
        titles = [x.get('title') for x in history]

        assert message['message']['content'] in lines
        assert message['message']['title'] in titles


def test_main():
    with TestClient(app) as client:
        response = client.get('/')
        assert response.status_code == 200
