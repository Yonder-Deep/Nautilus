from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
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
app.mount("/React", StaticFiles(directory="React"), name="React")

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
async def test_motors(command: str = Form(...)):
    print("Received command:", command)
    out_q.put(lambda: backend.test_motor("Forward", 50, 10))
    return {"message": f"Command '{command}' received and processed"}


@app.post("/calibrate_heading")
async def calibrate_heading(command: str = Form(...)):
    print("Received command:", command)
    return {"message": f"Command '{command}' received and processed"}


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
