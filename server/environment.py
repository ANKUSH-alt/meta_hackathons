import uuid
import datetime
from typing import Optional, Tuple, Dict, Any, List
from .models import CloudAction, CloudObservation, CloudState, CloudActionType

class CloudAuditEnv:
    def __init__(self):
        self.task_id = "easy"
        self._initialize_state()

    def _initialize_state(self):
        self.episode_id = str(uuid.uuid4())
        self.step_count = 0
        self.is_completed = False
        self.score = 0.0
        
        # Mock Infrastructure
        self.resources = {
            "s3": [
                {"id": "prod-data-001", "region": "us-east-1", "public": True, "tags": {"env": "prod"}},
                {"id": "prod-logs-002", "region": "us-east-1", "public": False, "tags": {"env": "prod"}},
                {"id": "dev-test-01", "region": "us-west-2", "public": True, "tags": {"env": "dev"}},
            ],
            "ec2": [
                {"id": "i-0abcdef1234567890", "type": "t2.micro", "state": "running", "tags": {"env": "dev"}, 
                 "security_groups": [{"id": "sg-01", "rules": [{"port": 22, "cidr": "0.0.0.0/0"}, {"port": 3389, "cidr": "0.0.0.0/0"}]}]},
                {"id": "i-0987654321fedcba0", "type": "m5.large", "state": "running", "tags": {"env": "prod"}, 
                 "security_groups": [{"id": "sg-02", "rules": [{"port": 443, "cidr": "0.0.0.0/0"}]}]},
            ],
            "logs": {
                "auth-logs": [
                    {"timestamp": "2026-04-05T10:00:00Z", "user": "admin", "action": "Login", "ip": "1.1.1.1"},
                    {"timestamp": "2026-04-05T10:15:00Z", "user": "iam-role-01", "action": "DeleteStorage", "ip": "192.168.1.50"},
                    {"timestamp": "2026-04-05T10:30:00Z", "user": "user-02", "action": "ListBuckets", "ip": "2.2.2.2"},
                ]
            }
        }

    def reset(self, task_id: str = "easy") -> CloudObservation:
        """Required by openenv-core 0.1.1: takes task_id, returns JUST the observation."""
        self.task_id = task_id
        self._initialize_state()
        return CloudObservation(info=f"Environment reset. Task: {self.task_id}", reward=0.0, done=False)

    def step(self, action: CloudAction) -> CloudObservation:
        """Required by openenv-core 0.1.1: takes action, returns JUST the observation with reward/done fields."""
        self.step_count += 1
        reward = 0.0
        terminated = False
        truncated = self.step_count >= 20  # Limit steps
        
        obs = CloudObservation()
        
        if action.action == CloudActionType.LIST:
            r_type = action.resource_type
            if r_type in self.resources:
                obs.resources = self.resources[r_type]
                obs.status = f"Listed {len(obs.resources)} {r_type} resources."
            else:
                obs.status = f"Unknown resource type: {r_type}"

        elif action.action == CloudActionType.DESCRIBE:
            res_id = action.resource_id
            found = False
            for r_type in ["s3", "ec2"]:
                for r in self.resources[r_type]:
                    if r["id"] == res_id:
                        obs.details = r
                        obs.status = f"Described resource {res_id}"
                        found = True
                        break
            if not found:
                obs.status = f"Resource not found: {res_id}"

        elif action.action == CloudActionType.MODIFY:
            res_id = action.resource_id
            patch = action.patch
            # Simple EC2 security group patching for Medium task
            if self.task_id == "medium" and res_id == "i-0abcdef1234567890":
                for sg in self.resources["ec2"][0]["security_groups"]:
                    if patch and "rules" in patch:
                        sg["rules"] = patch["rules"]
                obs.status = f"Updated security groups for {res_id}"
                # Check for reward
                rules = self.resources["ec2"][0]["security_groups"][0]["rules"]
                has_rdp = any(r["port"] == 3389 and r["cidr"] == "0.0.0.0/0" for r in rules)
                if not has_rdp:
                    reward = 1.0
                    terminated = True
            else:
                obs.status = "Action not permitted or invalid resource."

        elif action.action == CloudActionType.LOGS:
            log_name = action.resource_id
            if log_name in self.resources["logs"]:
                obs.logs = self.resources["logs"][log_name]
                obs.status = f"Fetched logs for {log_name}"
            else:
                obs.status = f"Logs not found: {log_name}"

        elif action.action == CloudActionType.SUBMIT:
            # For Easy and Hard tasks
            if self.task_id == "easy":
                # Expecting agent to list public S3 buckets in prod
                if action.answer:
                    answers = [a.strip() for a in action.answer.split(",")]
                    expected = ["prod-data-001"]
                    if set(answers) == set(expected):
                        reward = 1.0
                        terminated = True
                        obs.info = "Correct! Task completed."
                    else:
                        obs.info = f"Incorrect list of buckets. Got: {answers}"
            
            elif self.task_id == "hard":
                # Expecting rogue IP
                if action.answer == "192.168.1.50":
                    reward = 1.0
                    terminated = True
                    obs.info = "Correct Rogue IP identified!"
                else:
                    obs.info = f"Wrong IP. Got: {action.answer}"

        self.score += reward
        obs.reward = reward
        obs.done = terminated or truncated
        return obs

    def state(self) -> CloudState:
        return CloudState(
            episode_id=self.episode_id,
            step_count=self.step_count,
            task_id=self.task_id,
            is_completed=self.is_completed,
            score=self.score
        )
