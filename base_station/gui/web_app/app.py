from fastapi import FastAPI, Request, Form  # imports
from fastapi.responses import Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles  # Used for serving static files
import uvicorn
import os
import json

app = FastAPI()  # initialize the web app
app.mount("/js", StaticFiles(directory="js"), name="js")


@app.get("/testing", response_class=HTMLResponse)
def get_testing() -> HTMLResponse:
    with open("testing.html") as html:
        return HTMLResponse(content=html.read())


@app.post("/test_motors")
async def test_motors(command: str = Form(...)):
    print("Received command:", command)
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
