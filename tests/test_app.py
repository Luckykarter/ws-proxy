import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

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


def test_send_message(message):
    with client.websocket_connect('/ws/channel/test/1/') as websocket:
        websocket.send_json(message)
        data = websocket.receive_json()
        assert data == message['message']
        assert data["success"]


def test_main():
    response = client.get('/')
    assert response.status_code == 200
