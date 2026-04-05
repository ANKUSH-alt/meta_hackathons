import requests
import json

BASE_URL = "http://localhost:8000"

def run_baseline_audit(task_id="easy"):
    print(f"--- Running Baseline for Task: {task_id} ---")
    
    # 1. Reset environment
    response = requests.post(f"{BASE_URL}/reset", json={"task_id": task_id})
    if response.status_code != 200:
        print(f"Failed to reset: {response.text}")
        return
        
    obs_data = response.json()
    obs = obs_data.get("observation", {})
    print(f"Observation Info: {obs.get('info')}")
    
    # 2. List S3 buckets
    # Note: wrapping in "action" key to avoid collision with 'action' field in CloudAction
    action_payload = {
        "action": {
            "action": "list",
            "resource_type": "s3"
        }
    }
    response = requests.post(f"{BASE_URL}/step", json=action_payload)
    if response.status_code != 200:
        print(f"Failed on step: {response.text}")
        return
        
    step_result = response.json()
    obs = step_result.get("observation", {})
    
    resources = obs.get("resources", [])
    print(f"Discovered {len(resources)} S3 buckets.")
    
    # 3. Logic to identify public prod buckets
    public_prod_buckets = []
    for r in resources:
        if r.get("public") and r.get("tags", {}).get("env") == "prod":
            public_prod_buckets.append(r["id"])
    
    print(f"Identified Public Prod Buckets: {public_prod_buckets}")
    
    # 4. Submit answer
    submit_payload = {
        "action": {
            "action": "submit",
            "answer": ",".join(public_prod_buckets)
        }
    }
    response = requests.post(f"{BASE_URL}/step", json=submit_payload)
    step_result = response.json()
    obs = step_result.get("observation", {})
    reward = step_result.get("reward", 0.0)
    done = step_result.get("done", False)
    
    print(f"Final Reward: {reward}")
    print(f"Done: {done}")
    print(f"Info: {obs.get('info')}")

if __name__ == "__main__":
    try:
        run_baseline_audit("easy")
    except Exception as e:
        print(f"Error: {e}")
