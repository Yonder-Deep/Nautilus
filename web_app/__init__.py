from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from contextlib import asynccontextmanager
import asyncio
from queue import Queue, Empty
import threading
import json
from typing import Optional
from pathlib import Path

from backend import auv_socket_handler
from pydantic_yaml import parse_yaml_file_as
from ruamel.yaml import YAML
yaml = YAML(typ='safe')

class ConfigSchema(BaseModel):
    auv_url: str
    ping_interval: int

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

def log(message: str):
    queue_to_frontend.put(message)
    print("\033[44mMAIN:\033[0m " + message)

config = load_config()
log("STARTUP WITH CONFIGURATION:")
log(str(config.model_dump()))

log("Initializing remote websocket")
stop_event = threading.Event()
backend_thread = threading.Thread(target=auv_socket_handler, args=[stop_event, config.auv_url, config.ping_interval, queue_to_frontend, queue_to_auv])

def start_backend():
    """ If the backend websocket thread is not alive, start it.
        If it is alive, do nothing. 
    """
    if not backend_thread.is_alive():
        backend_thread.start()

def kill_backend():
    """ If the backend websocket thread is alive, tell it to stop
        and join until it does.
    """
    if backend_thread.is_alive():
        stop_event.set()
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
    queue_to_auv.put(frontend_message)

@api.websocket("/websocket")
async def frontend_websocket(websocket: WebSocket):
    await websocket.accept()
    log("Websocket created")
    await websocket.send_text("Local websocket live")
    await websocket.send_text("STARTUP WITH CONFIGURATION\n" + str(config.model_dump()))
    socket_status_queue = asyncio.Queue()
    await socket_status_queue.put(True)
    while True:
        # Sleep so that the async function yields to event loop
        await asyncio.sleep(0.001)
        # Check queue_to_frontend & send to frontend
        try:
            message_to_frontend = queue_to_frontend.get(block=False)
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6543)
