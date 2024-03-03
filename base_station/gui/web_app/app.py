from fastapi import FastAPI, Request, Form  # imports
from fastapi.responses import Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles  # Used for serving static files
import uvicorn
import os
import json

# Read Database connection variables
db_host = "localhost"
db_user = "root"
db_pass = os.environ["MYSQL_ROOT_PASSWORD"]
db_name = "TechAssignment6"

app = FastAPI()  # initialize the web app
app.mount(
    "/js", StaticFiles(directory="js"), name="js"
)  # mounts the js folder to the app


@app.get(
    "/testing", response_class=HTMLResponse
)  # returns the order HTML page when order is specified for the URL path
def get_testing() -> HTMLResponse:
    with open("testing.html") as html:
        return HTMLResponse(content=html.read())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6543)  # starts the app
