import json
import pickle
import asyncio
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form
from starlette.responses import RedirectResponse
from collections import defaultdict
import redis
import logging
import datetime

app = FastAPI()
rds = redis.StrictRedis(os.getenv('REDIS_HOST', 'localhost'))
HISTORY_EXPIRE = int(os.getenv('HISTORY_EXPIRE', '1'))

logger = logging.getLogger()


class History:
    def __init__(self, application: str, client_id: str):
        self.application = application
        self.client_id = client_id
        if not rds.exists(self.history_key):
            self.save_content([])

    @property
    def content(self):
        return pickle.loads(rds.get(self.history_key))

    def save_content(self, content: list):
        rds.set(self.history_key, pickle.dumps(content))
        rds.expire(self.history_key, datetime.timedelta(days=HISTORY_EXPIRE))

    def add_line(self, msg: dict):
        content = self.content
        msg['timestamp'] = datetime.datetime.now().isoformat()
        content.append(msg)
        self.save_content(content)

    @property
    def history_key(self):
        return f'history-{self.application}-{self.client_id}'


class ConnectionManager:
    def __init__(self):
        self.active_connections = defaultdict(dict)

    async def connect(self, websocket: WebSocket, application: str, client_id: str):
        await websocket.accept()
        if application not in self.active_connections:
            self.active_connections[application] = defaultdict(list)

        self.active_connections[application][client_id].append(websocket)

    def disconnect(self, websocket: WebSocket, application: str, client_id: str):
        self.active_connections[application][client_id].remove(websocket)

    async def broadcast(self, message: dict, application: str, client_id: str):
        if application in self.active_connections and client_id in self.active_connections[application]:
            for connection in self.active_connections[application][client_id]:
                try:
                    await connection.send_json(message)
                    print(f"sent: {message}")
                except Exception as e:  # pragma: no cover
                    pass

    async def consume(self):
        print("started to consume")
        sub = rds.pubsub()
        sub.subscribe('channel')
        while True:
            await asyncio.sleep(0.01)
            message = sub.get_message(ignore_subscribe_messages=True)
            if message is not None and isinstance(message, dict):
                msg = json.loads(message.get('data'))
                await self.broadcast(msg['message'], msg['application'], msg['client_id'])


manager = ConnectionManager()


@app.on_event("startup")
async def subscribe():
    asyncio.create_task(manager.consume())


@app.get('/')
def read_root():
    return RedirectResponse(url='https://voitixler.ru/')


@app.get('/ws/history/{application}/{client_id}/')
def get_history(application: str, client_id: str):
    return History(application, client_id).content


@app.post('/post/')
async def echo_post(request: Request):
    print(request.method)
    print(request.headers.raw)
    try:
        r = await request.json()
        print(r)
        return r
    except Exception as e:
        print(e)
        print("----body----:")
        body = b''
        async for chunk in request.stream():
            body += chunk
        print(body)
        body = body.decode(encoding='utf-8')
        return body


def _error_message(error):
    return {
        'title': 'ERROR',
        'content': error,
        'success': False
    }


@app.websocket("/ws/channel/{application}/{client_id}/")
async def websocket_endpoint(websocket: WebSocket, application: str, client_id: str):
    await manager.connect(websocket, application, client_id)
    while True:
        try:
            data = await websocket.receive_json()
            if 'message' in data:
                print(f"received: {data}")
                msg = data.get('message')
                if not isinstance(msg, dict):
                    msg = _error_message(f'message must be JSON. Received: "{msg}"')
                history = History(application, client_id)
                history.add_line(msg)
                rds.publish(
                    'channel',
                    json.dumps({
                        'application': application,
                        'client_id': client_id,
                        'message': msg
                    })
                )
        except WebSocketDisconnect:
            manager.disconnect(websocket, application, client_id)
        except RuntimeError:
            break


if __name__ == '__main__':  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8080)
