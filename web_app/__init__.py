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
yaml = YAML()

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
        local_filtered = {k:v for (k,v) in local_config.items() if v}
        default_config.update(local_filtered)
    return ConfigSchema(**default_config)

config = load_config()
print("STARTUP WITH CONFIGURATION:")
print(config.model_dump())

queue_to_frontend = Queue()
queue_to_auv = Queue()

@asynccontextmanager
async def lifespan(app: FastAPI):
    custom_log("Initializing auv socket handler")
    stop_event = threading.Event()
    backend_thread = threading.Thread(target=auv_socket_handler, args=[stop_event, config.auv_url, config.ping_interval, queue_to_frontend, queue_to_auv])
    backend_thread.start()
    yield
    custom_log("Waiting for websocket thread to join")
    stop_event.set()
    backend_thread.join()

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
    custom_log("Websocket created")
    await websocket.send_text("I'm alive")
    socket_status_queue = asyncio.Queue()
    await socket_status_queue.put(True)
    while True:
        # Sleep so that the async function yields to event loop
        await asyncio.sleep(0.001)
        # Check queue_to_frontend & send to frontend
        try:
            message_to_frontend = queue_to_frontend.get(block=False)
            if message_to_frontend:
                print("Message to frontend: " + message_to_frontend)
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
    custom_log("Saving layout to: " + layout_data_path)
    layout_data = layouts.model_dump_json()
    custom_log(layout_data)
    with open(layout_data_path, 'w') as file:
        file.write(layout_data)
    return layouts

@api.get("/layouts")
def get_layouts():
    custom_log("Received get request for layouts")
    try:
        with open(layout_data_path) as file:
            layout_data = json.load(file)
            custom_log("Layouts: " + json.dumps(layout_data))
            return layout_data
    except FileNotFoundError:
        custom_log("Error: The gui grid layout json file at " + layout_data_path + " is missing")
        return None
    except json.JSONDecodeError:
        custom_log("Error: The gui grid layout json file at " + layout_data_path + " is invalid json")

def custom_log(message: str):
    queue_to_frontend.put(message)
    print("\033[34mMAIN:\033[0m " + message)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6543)
