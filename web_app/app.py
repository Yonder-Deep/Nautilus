from fastapi import BackgroundTasks, FastAPI, WebSocket, APIRouter
from fastapi.staticfiles import StaticFiles
import asyncio
from queue import Queue
from contextlib import asynccontextmanager
import uvicorn
from pydantic import BaseModel

import sys
sys.path.append(".")
from static import global_vars

# Backend is not a thread since always driven by route handlers in this file
# Receive and ping are threads since they are driven by radio buffer
from backend import Backend
from threads import Receive_Thread, Ping_Thread

queue_to_frontend = Queue()
backend = Backend(global_vars.radio)

print("FRONTEND: Initializing receive & ping threads")
global_vars.connect_to_radio(queue_to_frontend, verbose=False)
receive_thread = Receive_Thread(global_vars.radio, out_q=queue_to_frontend)
ping_thread = Ping_Thread(global_vars.radio, out_q=queue_to_frontend)
receive_thread.start()
ping_thread.start()

# This function is this high up the in the file because
# it must be declared before the FastAPI object
# 
# Checking the queue from receive.py for messages from AUV
async def check_queue_from_receive():
    while True:
        print("FRONTEND: Queue being checked")
        await asyncio.sleep(1)
        auv_message = queue_to_frontend.get()
        print("FRONTEND: Message from AUV in queue: \n" + "     " + auv_message)
        # Send message to frontend via websocket

# This function is this high up the in the file because
# it must be declared before the FastAPI object
# to be passed as a lifespan function
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("FRONTEND: Creating background task to check queue")
    asyncio.create_task(check_queue_from_receive())
    yield
    print("FRONTEND: Shutting down threads...")
    ping_thread.join()
    receive_thread.join()

app = FastAPI(lifespan=lifespan)

# Mount the api calls
api = FastAPI(root_path="/api")
app.mount("/api", api)

# Mount the static react frontend
app.mount("/", StaticFiles(directory="./frontend_gui/dist"), name="public")

# Create the websocket router
socket_router = APIRouter(
    prefix="/ws"
)

@socket_router.websocket("/websocket")
async def websocket_handler(websocket: WebSocket):
    await websocket.accept()
    while 

# @api.get("/imu_calibration_data")
# async def get_imu_calibration_data() -> dict:
#     return {
#         "magnetometer": "Value from backend",
#         "accelerometer": "Value from backend",
#         "gyroscope": "Value from backend",
#     }

# @api.get("/ins_data")
# async def get_ins_data() -> dict:
#     return {
#         "heading": "Value from backend",
#         "roll": "Value from backend",
#         "pitch": "Value from backend",
#     }

class MotorTest(BaseModel):
    motor: str
    speed: str
    duration: str

@api.post("/motor_test")
async def motor_test(data: MotorTest):
    # Process motor test data
    motor_type = data.motor
    speed = data.speed
    duration = data.duration
    print("FRONTEND: Motor Test: ")
    print("     Type: " + motor_type)
    print("     Speed: " + speed)
    print("     Duration: " + duration)
    backend.test_motor(motor_type, speed, duration)
    return {
        "message": f"Test motor {motor_type} at speed {speed} for duration {duration} seconds received and processed",
        "status": "Motor test initiated",
    }

class HeadingTest(BaseModel):
    heading: str

@api.post("/heading_test")
async def heading_test(data: HeadingTest):
    target_heading = data.heading
    print("FRONTEND: Heading Test: ")
    print("     Target Heading: " + target_heading)
    backend.test_heading(target_heading)
    return {"status": "Heading test initiated"}

class PIDConstants(BaseModel):
    p: str
    i: str
    d: str

@api.post("/{axis}_pid_constants")
async def set_pid_constants(axis: str, data: PIDConstants):
    pid_axis = axis
    p_constant = data.p
    i_constant = data.i
    d_constant = data.d
    print("FRONTEND: PID Constants: ")
    print("     Axis: " + pid_axis)
    print("     P: " + p_constant)
    print("     I: " + i_constant)
    print("     D: " + d_constant)
    backend.send_pid_update(pid_axis, p_constant, i_constant, d_constant)
    return {"status": f"{axis.capitalize()} PID constants set"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6543)