"""
CloudSecurityAuditor — OpenEnv Inference Script
================================================
Uses an LLM (via OpenAI-compatible client) to autonomously solve all 3 security tasks.
Emits structured [START], [STEP], [END] logs for automated evaluation.

Required environment variables:
  API_BASE_URL  — The API endpoint for the LLM (e.g., https://api.openai.com/v1)
  MODEL_NAME    — The model identifier (e.g., gpt-4o-mini)
  API_KEY       — Your API key for the LLM proxy
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timezone
from openai import OpenAI

# ──────────────────────────────────────────────
# Configuration from environment variables
# ──────────────────────────────────────────────
API_BASE_URL = os.environ["API_BASE_URL"]
API_KEY = os.environ["API_KEY"]
MODEL_NAME = os.environ["MODEL_NAME"]

LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME", "")

ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")
BENCHMARK_NAME = "cloud-security-auditor"

# Initialize OpenAI-compatible client
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY,
)

# ──────────────────────────────────────────────
# Task definitions with prompts
# ──────────────────────────────────────────────
TASKS = [
    {
        "id": "easy",
        "name": "S3 Public Audit",
        "system_prompt": (
            "You are a cloud security auditor AI agent. You interact with a simulated cloud environment "
            "via structured JSON actions. Your goal is to identify all S3 buckets that are BOTH public "
            "AND tagged with env=prod. You must submit their IDs as a comma-separated string.\n\n"
            "Available actions:\n"
            "- {\"action\": \"list\", \"resource_type\": \"s3\"} — List all S3 buckets\n"
            "- {\"action\": \"describe\", \"resource_id\": \"<id>\"} — Get details of a resource\n"
            "- {\"action\": \"submit\", \"answer\": \"<answer>\"} — Submit your final answer\n\n"
            "Respond with ONLY a valid JSON action object. No explanation."
        ),
    },
    {
        "id": "medium",
        "name": "EC2 Security Patch",
        "system_prompt": (
            "You are a cloud security auditor AI agent. Your goal is to find EC2 instance "
            "'i-0abcdef1234567890' which has port 3389 (RDP) open to the internet (0.0.0.0/0), "
            "and close it by modifying the security group to only allow port 22 (SSH).\n\n"
            "Available actions:\n"
            "- {\"action\": \"list\", \"resource_type\": \"ec2\"} — List all EC2 instances\n"
            "- {\"action\": \"describe\", \"resource_id\": \"<id>\"} — Get details of a resource\n"
            "- {\"action\": \"modify\", \"resource_id\": \"<id>\", \"patch\": {\"rules\": [...]}} — Modify security group rules\n\n"
            "Respond with ONLY a valid JSON action object. No explanation."
        ),
    },
    {
        "id": "hard",
        "name": "IAM Log Forensic",
        "system_prompt": (
            "You are a cloud security forensic analyst AI agent. A rogue IAM role 'iam-role-01' "
            "has been performing unauthorized actions. You must fetch the 'auth-logs' and identify "
            "the IP address that performed the 'DeleteStorage' action. Submit that IP address.\n\n"
            "Available actions:\n"
            "- {\"action\": \"logs\", \"resource_id\": \"auth-logs\"} — Fetch authentication logs\n"
            "- {\"action\": \"submit\", \"answer\": \"<ip_address>\"} — Submit the rogue IP\n\n"
            "Respond with ONLY a valid JSON action object. No explanation."
        ),
    },
]

MAX_STEPS_PER_TASK = 10


# ──────────────────────────────────────────────
# Environment interaction helpers
# ──────────────────────────────────────────────
def env_reset(task_id: str) -> dict:
    """Reset environment to a specific task."""
    resp = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def env_step(action: dict) -> dict:
    """Execute an action in the environment."""
    resp = requests.post(f"{ENV_URL}/step", json={"action": action}, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ──────────────────────────────────────────────
# LLM interaction
# ──────────────────────────────────────────────
def ask_llm(system_prompt: str, conversation: list) -> dict:
    """Ask the LLM to decide the next action. Returns parsed JSON action."""
    messages = [{"role": "system", "content": system_prompt}] + conversation

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.0,
        max_tokens=512,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        # Handle cases where the JSON block is the only content
        if "{" in raw:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            raw = raw[start:end]
        else:
            raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from the response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
        raise ValueError(f"LLM returned non-JSON response: {raw}")


# ──────────────────────────────────────────────
# Structured logging helpers
# ──────────────────────────────────────────────
def log_start(task_name: str):
    """
    [START] task=<task_name> env=<benchmark> model=<model_name>
    """
    print(f"[START] task={task_name} env={BENCHMARK_NAME} model={MODEL_NAME}")
    sys.stdout.flush()


def log_step(step_num: int, action: dict, reward: float, done: bool, error: str = None):
    """
    [STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    """
    error_str = "null" if not error else error
    # Remove newlines from action for single-line requirement
    action_str = json.dumps(action).replace("\n", " ")
    done_str = "true" if done else "false"
    print(f"[STEP]  step={step_num} action={action_str} reward={reward:.2f} done={done_str} error={error_str}")
    sys.stdout.flush()


def log_end(success: bool, total_steps: int, score: float, rewards: list):
    """
    [END] success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
    """
    success_str = "true" if success else "false"
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])
    print(f"[END]   success={success_str} steps={total_steps} score={score:.2f} rewards={rewards_str}")
    sys.stdout.flush()


# ──────────────────────────────────────────────
# Main task runner
# ──────────────────────────────────────────────
def run_task(task: dict):
    """Run a single task using the LLM agent."""
    task_id = task["id"]
    task_name = task["name"]
    system_prompt = task["system_prompt"]

    log_start(task_id)

    # Reset environment
    try:
        reset_data = env_reset(task_id)
        obs = reset_data.get("observation", {})
        info = obs.get("info", "")
    except Exception as e:
        log_end(success=False, total_steps=0, score=0.0, rewards=[])
        return

    conversation = [
        {"role": "user", "content": f"Task started. Environment says: {info}\nDecide your first action."}
    ]

    rewards = []
    step_num = 0
    success = False
    last_error = None

    for step_num in range(1, MAX_STEPS_PER_TASK + 1):
        try:
            # Ask LLM for next action
            action = ask_llm(system_prompt, conversation)
        except Exception as e:
            last_error = f"LLM error: {str(e)}"
            log_step(step_num, {"error": "LLM failed"}, 0.0, True, error=last_error)
            break

        # Execute the action in the environment
        try:
            result = env_step(action)
            obs = result.get("observation", {})
            reward = result.get("reward", 0.0)
            done = result.get("done", False)
            last_error = obs.get("last_action_error")
        except Exception as e:
            last_error = f"Env error: {str(e)}"
            log_step(step_num, action, 0.0, True, error=last_error)
            break

        rewards.append(reward)
        log_step(step_num, action, reward, done, error=last_error)

        if done:
            success = (reward >= 1.0)  # Assume 1.0 is full success
            break

        # Build observation summary for the LLM
        obs_summary_parts = []
        if obs.get("resources"):
            obs_summary_parts.append(f"Resources: {json.dumps(obs['resources'])}")
        if obs.get("details"):
            obs_summary_parts.append(f"Details: {json.dumps(obs['details'])}")
        if obs.get("logs"):
            obs_summary_parts.append(f"Logs: {json.dumps(obs['logs'])}")
        if obs.get("status"):
            obs_summary_parts.append(f"Status: {obs['status']}")
        if obs.get("info"):
            obs_summary_parts.append(f"Info: {obs['info']}")

        obs_text = "\n".join(obs_summary_parts) if obs_summary_parts else "No data returned."

        # Add to conversation
        conversation.append({"role": "assistant", "content": json.dumps(action)})
        conversation.append({"role": "user", "content": f"Observation from environment:\n{obs_text}\n\nDecide your next action."})

    # Calculate final score (normalized to [0, 1])
    final_score = max(0.0, min(1.0, sum(rewards)))
    
    log_end(success=success, total_steps=step_num, score=final_score, rewards=rewards)


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
def main():
    for task in TASKS:
        try:
            run_task(task)
        except Exception:
            pass


if __name__ == "__main__":
    main()
