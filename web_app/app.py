from fastapi import FastAPI, Form, Depends, WebSocket, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from queue import Queue
import uvicorn
import sys
from pydantic import BaseModel

sys.path.append("..")
from static import global_vars
from backend import Backend
from threads.base_station_receive import BaseStation_Receive
from threads.base_station_send_ping import BaseStation_Send_Ping
from threads.base_station_send import BaseStation_Send

app = FastAPI()

# Mount the api calls
api = FastAPI(root_path="/api")
app.mount("/api", api)

# Mount the static react frontend
app.mount("/", StaticFiles(directory="./frontend_gui/dist"), name="public")

# Create the websocket router
socket_router = APIRouter(
    prefix="/ws"
)

to_GUI = Queue()
to_Backend = Queue()
out_q = to_Backend
in_q = to_GUI

try:
    global_vars.connect_to_radio(to_GUI)
    bs_r_thread = BaseStation_Receive(global_vars.radio, in_q=None, out_q=to_GUI)
    backend = Backend(global_vars.radio, to_Backend)
    bs_ping_thread = BaseStation_Send_Ping(global_vars.radio, to_GUI)
    bs_r_thread.start()
    backend.start()
    bs_ping_thread.start()
except Exception as e:
    print("Err: ", str(e))
    print("[MAIN] Base Station initialization failed. Closing...")
    sys.exit()


@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down threads...")
    bs_ping_thread.join()
    bs_r_thread.join()
    backend.join()

@socket_router.websocket("/imu_calibration_data")
async def ws_imu_calibration_data():
    return

@api.get("/imu_calibration_data")
async def get_imu_calibration_data() -> dict:
    return {
        "magnetometer": "Value from backend",
        "accelerometer": "Value from backend",
        "gyroscope": "Value from backend",
    }


@api.get("/ins_data")
async def get_ins_data() -> dict:
    return {
        "heading": "Value from backend",
        "roll": "Value from backend",
        "pitch": "Value from backend",
    }

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
    out_q.put(lambda: backend.test_motor(motor_type, speed, duration))
    # out_q.put("test_motor(" + motor_type + "," + str(speed) + "," + str(duration) + ")")
    return {
        "message": f"Test motor {motor_type} at speed {speed} for duration {duration} seconds received and processed",
        "status": "Motor test initiated",
    }

class HeadingTest(BaseModel):
    heading: str

@api.post("/heading_test")
async def heading_test(data: HeadingTest):
    # Process heading test data
    return {"status": "Heading test initiated"}


class PIDConstants(BaseModel):
    p: str
    i: str
    d: str

@api.post("/{axis}_pid_constants")
async def set_pid_constants(axis: str, data: PIDConstants):
    # Process PID constants
    return {"status": f"{axis.capitalize()} PID constants set"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6543)
