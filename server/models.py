from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic.dataclasses import dataclass
from pydantic import ConfigDict, BaseModel

class CloudActionType(str, Enum):
    LIST = "list"
    DESCRIBE = "describe"
    MODIFY = "modify"
    LOGS = "logs"
    SUBMIT = "submit"

@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class CloudAction:
    action: CloudActionType
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    patch: Optional[Dict[str, Any]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    answer: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class CloudObservation:
    resources: Optional[List[Dict[str, Any]]] = None
    details: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    logs: Optional[List[Dict[str, Any]]] = None
    info: Optional[str] = None
    reward: float = 0.0          # Required by openenv-core 0.1.1
    done: bool = False           # Required by openenv-core 0.1.1

class CloudState(BaseModel):
    episode_id: str
    step_count: int
    task_id: str
    is_completed: bool
    score: float
