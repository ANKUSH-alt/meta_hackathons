from fastapi import FastAPI, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from openenv_core.env_server import create_fastapi_app
from .models import CloudAction, CloudObservation
from .environment import CloudAuditEnv
from typing import Any, Dict
import os

# Initialize the environment
env = CloudAuditEnv()

# Create the FastAPI app using openenv-core
# Wrap env in a lambda to satisfy HF's "must be a callable" requirement
app = create_fastapi_app(lambda: env, CloudAction, CloudObservation)

# ── Override /reset to properly pass task_id ────────────────────────────────
# openenv-core's built-in /reset handler ignores request body fields (known TODO).
# Remove the library's /reset route first so our override wins (FastAPI is first-match).
app.routes[:] = [r for r in app.routes if not (hasattr(r, "path") and r.path == "/reset")]

@app.post("/reset")
async def reset_with_task(request: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    """Reset the environment, forwarding task_id from the request body."""
    task_id = request.get("task_id", "easy")
    observation = env.reset(task_id=task_id)
    return observation.model_dump() if hasattr(observation, "model_dump") else observation.__dict__

# Add custom routes for the UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/ui", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/state")
async def get_state():
    return env.state()

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860, reload=True)

if __name__ == "__main__":
    main()
