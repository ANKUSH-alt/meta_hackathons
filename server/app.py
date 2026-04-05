from openenv_core.env_server import create_fastapi_app
from .models import CloudAction, CloudObservation
from .environment import CloudAuditEnv

# Initialize the environment
env = CloudAuditEnv()

# Create the FastAPI app
# Note: create_fastapi_app expects the environment instance, 
# and the Action/Observation models for typing.
app = create_fastapi_app(env, CloudAction, CloudObservation)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
