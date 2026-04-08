from fastapi import FastAPI, Body, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from openenv_core.env_server import create_fastapi_app
from .models import CloudAction, CloudObservation
from .environment import CloudAuditEnv
from typing import Any, Dict
from dataclasses import asdict
import os
import sys

# Initialize the environment
env = CloudAuditEnv()

# Create the FastAPI app using openenv-core
app = create_fastapi_app(env, CloudAction, CloudObservation)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"CRITICAL ERROR: {str(exc)}", file=sys.stderr)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}", "type": "critical_error"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"VALIDATION ERROR: {exc.errors()}", file=sys.stderr)
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "type": "validation_error"}
    )

# ── Override /reset to properly pass task_id ────────────────────────────────
# openenv-core's built-in /reset handler ignores request body fields (known TODO).
# Remove the library's /reset route first so our override wins (FastAPI is first-match).
app.routes[:] = [r for r in app.routes if not (hasattr(r, "path") and r.path == "/reset")]

@app.post("/reset")
async def reset_with_task(request: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    """Reset the environment, forwarding task_id from the request body."""
    task_id = request.get("task_id", "easy")
    observation = env.reset(task_id=task_id)
    return asdict(observation)

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
