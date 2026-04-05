from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from openenv_core.env_server import create_fastapi_app
from .models import CloudAction, CloudObservation
from .environment import CloudAuditEnv
import os

# Initialize the environment
env = CloudAuditEnv()

# Create the FastAPI app using openenv-core
app = create_fastapi_app(env, CloudAction, CloudObservation)

# Add custom routes for the UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/ui", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/state")
async def get_state():
    return env.state()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
