from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
import asyncio
from contextlib import asynccontextmanager
import uvicorn
from pydantic import BaseModel

# Backend is not a thread since always driven by route handlers in this file
# Receive and ping are threads since they are driven by radio buffer
from backend import Backend
backend = Backend()

from threads import Receive_Thread, Ping_Thread
from queue import Queue
queue_to_frontend = Queue()

# This function is this high up the in the file because
# it must be declared before the FastAPI object
# to be passed as a lifespan function
@asynccontextmanager
async def lifespan(app: FastAPI):
    custom_log("Initializing receive & ping threads")
    global_vars.connect_to_radio(queue_to_frontend, verbose=False)
    receive_thread = Receive_Thread(global_vars.radio, out_q=queue_to_frontend)
    ping_thread = Ping_Thread(global_vars.radio, out_q=queue_to_frontend)
    receive_thread.start()
    ping_thread.start()
    yield
    custom_log("Shutting down threads...")
    ping_thread.join()
    receive_thread.join()

app = FastAPI(lifespan=lifespan)

# Mount the api calls
api = FastAPI(root_path="/api")
app.mount("/api", api)

# Mount the static react frontend
app.mount("/", StaticFiles(directory="./frontend_gui/dist", html=True), name="public")

@api.websocket("/websocket")
async def websocket_handler(websocket: WebSocket):
    await websocket.accept()
    custom_log("Websocket created")
    await websocket.send_text("I'm alive")
    while True:
        print("\033[34mFRONTEND:\033[0m Queue being checked")
        # This sleep allows keyboard interrupts to kill the application
        await asyncio.sleep(0.01)
        auv_message = queue_to_frontend.get()
        print("\033[34mFRONTEND:\033[0m Message to frontend in queue: \n" + "     " + auv_message)
        try:
            await websocket.send_text(str(auv_message))
        except:
            custom_log("Websocket send exception, assuming GUI disconnect")
            return

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
    custom_log(f"Motor Test: \n \
         Type: {motor_type} \n \
         Speed: {speed} \n \
         Duration: {duration}")
    backend.test_motor(motor_type, speed, duration)

class HeadingTest(BaseModel):
    heading: str

@api.post("/heading_test")
async def heading_test(data: HeadingTest):
    target_heading = data.heading
    custom_log("Heading Test: ")
    custom_log("     Target Heading: " + target_heading)
    backend.test_heading(target_heading)

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
    custom_log(f"PID Constants: \n \
            Axis: {pid_axis} \n \
            P: {p_constant} \n \
            I: {i_constant} \n \
            D: {d_constant}")
    backend.send_pid_update(pid_axis, p_constant, i_constant, d_constant)

def custom_log(message: str):
    queue_to_frontend.put(message)
    print("\033[34mFRONTEND:\033[0m " + message)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6543)
