from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from collections import defaultdict

app = FastAPI()


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
        for connection in self.active_connections[application][client_id]:
            try:
                await connection.send_json(message)
                print(f"sent {message}")
            except Exception as e:  # pragma: no cover
                pass


manager = ConnectionManager()


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
                await manager.broadcast(data.get('message'), application, client_id)
        except WebSocketDisconnect:
            manager.disconnect(websocket, application, client_id)
        except RuntimeError:
            break


if __name__ == '__main__':  # pragma: no cover
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)
