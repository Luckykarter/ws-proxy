import json
import asyncio
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from collections import defaultdict
import redis

app = FastAPI()
rds = redis.StrictRedis(os.getenv('REDIS_HOST', 'localhost'))


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
                    print(f"sent {message}")
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
    return {"websocket_proxy": "hi!"}


@app.websocket("/ws/channel/{application}/{client_id}/")
async def websocket_endpoint(websocket: WebSocket, application: str, client_id: str):
    await manager.connect(websocket, application, client_id)
    while True:
        try:
            data = await websocket.receive_json()
            if 'message' in data:
                print(f"received: {data}")
                rds.publish(
                    'channel',
                    json.dumps({
                        'application': application,
                        'client_id': client_id,
                        'message': data.get('message')
                    })
                )
        except WebSocketDisconnect:
            manager.disconnect(websocket, application, client_id)
        except RuntimeError:
            break


if __name__ == '__main__':  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8005)
