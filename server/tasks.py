from typing import Dict, List, Any

TASKS = {
    "easy": {
        "id": "easy",
        "description": "Identify all public S3 buckets in the 'prod' region. Submit their IDs as a comma-separated string.",
        "difficulty": "Easy",
        "reward_threshold": 1.0,
    },
    "medium": {
        "id": "medium",
        "description": "Find the EC2 instance with ID 'i-0abcdef1234567890' in the 'dev' environment. Close port 3389 (RDP) by updating its security group rules to only allow port 22.",
        "difficulty": "Medium",
        "reward_threshold": 1.0,
    },
    "hard": {
        "id": "hard",
        "description": "A rogue IAM role 'iam-role-01' has been performing unauthorized actions. Fetch the 'auth-logs' and identify the IP address that performed 'DeleteStorage'. Submit the IP address.",
        "difficulty": "Hard",
        "reward_threshold": 1.0,
    }
}

def get_task_info(task_id: str) -> Dict[str, Any]:
    return TASKS.get(task_id, {})

def list_tasks() -> List[Dict[str, Any]]:
    return list(TASKS.values())
