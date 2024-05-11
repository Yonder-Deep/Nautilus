from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from queue import Queue
import uvicorn
import sys

sys.path.append("..")
from static import global_vars
from backend import Backend
from threads.base_station_receive import BaseStation_Receive
from threads.base_station_send_ping import BaseStation_Send_Ping

app = FastAPI()  # initialize the web app
# app.mount("/js", StaticFiles(directory="js"), name="js")
# app.mount("/css", StaticFiles(directory="css"), name="css")


# defines origin for react app
origins = ["http://localhost:3000", "localhost:3000"]

# Adds middleware to handle cross-origin requests (different protocol, IP address, domain name, or port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

to_GUI = Queue()
to_Backend = Queue()
out_q = to_Backend
in_q = to_GUI

try:
    bs_r_thread = BaseStation_Receive(global_vars.radio, to_Backend, to_GUI)
    backend = Backend(global_vars.radio, to_Backend)
    bs_ping_thread = BaseStation_Send_Ping(global_vars.radio, to_GUI)
    bs_r_thread.start()
    backend.start()
    bs_ping_thread.start()
except Exception as e:
    print("Err: ", str(e))
    print("[MAIN] Base Station initialization failed. Closing...")
    sys.exit()


# Testing Lines start
@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "This is the root path"}


tests = [{"id": "1", "item": "Cordinates: "}, {"id": "2", "item": "Heading:"}]


@app.get("/test", tags=["tests"])
async def get_tests() -> dict:
    return {"data": tests}


@app.post("/test", tags=["tests"])
async def add_test(test: dict) -> dict:
    tests.append(test)
    return {"data": {"test added."}}


# Testing Lines End
@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down threads...")
    bs_ping_thread.join()
    bs_r_thread.join()
    backend.join()


@app.get("/testing", response_class=HTMLResponse)
def get_testing() -> HTMLResponse:
    with open("testing.html") as html:
        return HTMLResponse(content=html.read())


@app.post("/test_motors")
async def test_motors(motor_params: dict):
    motor_type = motor_params["motor_type"]
    speed = motor_params["speed"]
    duration = motor_params["duration"]
    out_q.put(lambda: backend.test_motor(motor_type, speed, duration))
    return {
        "message": f"Test motor {motor_type} at speed {speed} for duration {duration} seconds received and processed"
    }


@app.post("/test_heading")
async def test_heading():
    out_q.put(lambda: backend.test_heading())
    return {"message": f"Test heading received and processed"}


@app.post("/calibrate_depth")
async def calibrate_depth(command: str = Form(...)):
    print("Received command:", command)
    return {"message": f"Command '{command}' received and processed"}


@app.post("/tune_turn_pid")
async def tune_turn_pid(command: str = Form(...)):
    print("Received command:", command)
    return {"message": f"Command '{command}' received and processed"}


@app.post("/tune_dive_pid")
async def tune_dive_pid(command: str = Form(...)):
    print("Received command:", command)
    return {"message": f"Command '{command}' received and processed"}


@app.post("/commence_auto_nav")
async def commence_auto_nav(command: str = Form(...)):
    print("Received command:", command)
    return {"message": f"Command '{command}' received and processed"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6543)  # starts the app



