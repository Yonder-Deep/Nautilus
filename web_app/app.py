from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
import asyncio
from contextlib import asynccontextmanager
import uvicorn
from pydantic import BaseModel

from static import global_vars

# Backend is not a thread since always driven by route handlers in this file
# Receive and ping are threads since they are driven by radio buffer
from backend import Backend
backend = Backend(global_vars.radio)

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
        print("\033[34mFRONTEND:\033[0m Message from AUV in queue: \n" + "     " + auv_message)
        await websocket.send_text(str(auv_message))

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
    custom_log("Motor Test: ")
    custom_log("     Type: " + motor_type)
    custom_log("     Speed: " + speed)
    custom_log("     Duration: " + duration)
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
    custom_log("Heading Test: ")
    custom_log("     Target Heading: " + target_heading)
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
    custom_log("PID Constants: \n \
            Axis: + ${pid_axis} \
            P: + ${p_constant} \
            I: + ${i_constant} \
            D: + ${d_constant}")
    backend.send_pid_update(pid_axis, p_constant, i_constant, d_constant)
    return {"status": f"{axis.capitalize()} PID constants set"}

def custom_log(message: str):
    queue_to_frontend.put(message)
    print("\033[34mFRONTEND:\033[0m " + message)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6543)
