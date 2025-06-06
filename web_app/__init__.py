from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

import cv2

from contextlib import asynccontextmanager
import asyncio
from queue import Queue, Empty
import threading
import json
from typing import Optional
from pathlib import Path
from time import sleep

from backend import socket_thread 

from pydantic_yaml import parse_yaml_file_as
from ruamel.yaml import YAML
yaml = YAML(typ='safe')

class ConfigSchema(BaseModel):
    auv_url: str
    ping_interval: int
    video: bool

def load_config() -> ConfigSchema:
    default_config = parse_yaml_file_as(ConfigSchema, 'data/config.yaml').model_dump()
    local_path = Path('data/local/config.yaml')
    if local_path.exists():
        local_file = open(local_path, 'r')
        local_config = yaml.load(local_file)
        local_file.close()
        if local_config:
            local_filtered = {k:v for (k,v) in local_config.items() if v}
            default_config.update(local_filtered)
    return ConfigSchema(**default_config)

queue_to_frontend = Queue()
queue_to_auv = Queue()
meta_from_frontend = Queue()
meta_to_frontend = Queue()

def log(message: str):
    queue_to_frontend.put("MAIN: \n" + message)
    print("\033[44mMAIN:\033[0m " + message)

config = load_config()

log("STARTUP WITH CONFIGURATION: \n" + str(config.model_dump()))
log("Initializing remote websocket")

stop_event = threading.Event()
restart_event = threading.Event()
shutdown_event = threading.Event()
connected_event = threading.Event()
backend_thread = threading.Thread(
    target=socket_thread,
    args=[
        stop_event,
        config.auv_url,
        config.ping_interval,
        queue_to_frontend,
        queue_to_auv,
        meta_from_frontend,
        restart_event,
        shutdown_event,
        connected_event,
    ]
)

def start_backend():
    """ If the backend websocket thread is not alive, start it.
        If it is alive, do nothing. 
    """
    if backend_thread.is_alive() == False:
        backend_thread.start()

def kill_backend():
    """ If the backend websocket thread is alive, tell it to stop
        and join until it does.
    """
    if backend_thread.is_alive() == True:
        stop_event.set()
        shutdown_event.set()
        backend_thread.join()

start_backend()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    log("Waiting for websocket thread to join")
    kill_backend()

app = FastAPI(lifespan=lifespan)

# Mount the api calls (to not clash with the static frontend below)
api = FastAPI(root_path="/api")
app.mount("/api", api)

# Mount the static react frontend
app.mount("/", StaticFiles(directory="./frontend_gui/dist", html=True), name="public")

async def eatSocket(websocket:WebSocket, socket_status_queue:asyncio.Queue):
    frontend_message = await websocket.receive_json()
    await websocket.send_text(json.dumps(frontend_message))
    await socket_status_queue.put(True)
    if frontend_message["command"] == "websocket":
        if frontend_message["content"] == "ping":
            if backend_thread.is_alive() == False or connected_event.is_set() == False:
                log("Cannot ping, no active websocket connection")
            meta_from_frontend.put(frontend_message)
        elif frontend_message["content"] == "restart":
            stop_event.set()
            restart_event.set()

    else:
        queue_to_auv.put(frontend_message)

@api.websocket("/websocket")
async def frontend_websocket(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Local websocket live")
    log("Setup Done")
    socket_status_queue = asyncio.Queue()
    await socket_status_queue.put(True)
    while True:
        # Sleep so that the async function yields to event loop
        await asyncio.sleep(0.001)
        # Check queue_to_frontend & send to frontend
        try:
            message_to_frontend = queue_to_frontend.get_nowait()
            if message_to_frontend:
                print("\033[45mTO FRONT:\033[0m " + message_to_frontend)
                await websocket.send_text(message_to_frontend)
        except Empty:
            pass
        # Check websocket & send to queue_to_auv
        try:
            socket_available = socket_status_queue.get_nowait()
            if socket_available:
                asyncio.create_task(eatSocket(websocket=websocket,
                                              socket_status_queue=socket_status_queue))
        except asyncio.queues.QueueEmpty:
            pass
        continue

layout_data_path = "./data/gui_layouts.json"

class LayoutsModel(BaseModel):
    class Config:
        extra = "allow"

@api.post("/layouts")
def save_layouts(layouts: LayoutsModel) -> LayoutsModel:
    log("Saving layout to: " + layout_data_path)
    layout_data = layouts.model_dump_json()
    log(layout_data)
    with open(layout_data_path, 'w') as file:
        file.write(layout_data)
    return layouts

@api.get("/layouts")
def get_layouts():
    log("Received get request for layouts")
    try:
        with open(layout_data_path) as file:
            layout_data = json.load(file)
            log("Layouts found")
            return layout_data
    except FileNotFoundError:
        log("Error: The gui grid layout json file at " + layout_data_path + " is missing")
        return None
    except json.JSONDecodeError:
        log("Error: The gui grid layout json file at " + layout_data_path + " is invalid json")

if config.video:
    from video import VideoThread
    video_q = Queue()
    video_thread = VideoThread(video_q)

async def generate_frames():
    if not config.video:
        return
    while True:
        try:
            img = video_q.get()
            ret, jpeg = cv2.imencode('.jpg', img)
            if not ret:
                log(f"Error: Could not encode image to JPEG")
                continue

            yield b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n'

        except Exception as e:
            log(f"An error occurred while processing: {str(e)}")

@api.get('/video_feed')
async def video_feed():
    if config.video:
        return StreamingResponse(
                generate_frames(),
                media_type='multipart/x-mixed-replace; boundary=frame',
        )
    else:
        raise HTTPException(status_code=404, detail="Video disabled in config")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6543)
