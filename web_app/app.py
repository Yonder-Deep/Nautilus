from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
import asyncio
from contextlib import asynccontextmanager
import uvicorn
from queue import Queue
import threading

from config import AUV_IP_ADDRESS, AUV_PING_INTERVAL # The AUV ip address, ping interval, etc.
from backend import auv_socket_handler

queue_to_frontend = Queue()
queue_to_auv = Queue()

@asynccontextmanager
async def lifespan(app: FastAPI):
    custom_log("Initializing backend routine")
    backend_thread = threading.Thread(target=auv_socket_handler, args=[AUV_IP_ADDRESS, AUV_PING_INTERVAL, queue_to_frontend, queue_to_auv])
    yield
    backend_thread.join()
    custom_log("Shutting down backend websocket thread")

app = FastAPI(lifespan=lifespan)

# Mount the api calls
api = FastAPI(root_path="/api")
app.mount("/api", api)

# Mount the static react frontend
app.mount("/", StaticFiles(directory="./frontend_gui/dist", html=True), name="public")

@api.websocket("/websocket")
async def frontend_websocket(websocket: WebSocket):
    await websocket.accept()
    custom_log("Websocket created")
    await websocket.send_text("I'm alive")
    while True:
        # Sleep so that the async function yields to event loop
        await asyncio.sleep(0.1)
        # Check queue_to_frontend & send to frontend
        try:
            message_to_frontend = queue_to_frontend.get(block=False)
            if message_to_frontend:
                await websocket.send_text(str(message_to_frontend))
        finally:
            # Check websocket & send to queue_to_auv
            frontend_message = await websocket.receive_text()
            queue_to_auv.put(frontend_message)

def custom_log(message: str):
    queue_to_frontend.put(message)
    print("\033[34mMAIN:\033[0m " + message)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6543)