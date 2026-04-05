"""
CloudSecurityAuditor — OpenEnv Inference Script
================================================
Uses an LLM (via OpenAI-compatible client) to autonomously solve all 3 security tasks.
Emits structured [START], [STEP], [END] logs for automated evaluation.

Required environment variables:
  API_BASE_URL  — The API endpoint for the LLM (e.g., https://openrouter.ai/api/v1)
  MODEL_NAME    — The model identifier (e.g., openai/gpt-4o-mini)
  HF_TOKEN      — Your Hugging Face / API key
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
API_BASE_URL = os.environ.get("API_BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "openai/gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

ENV_URL = os.environ.get("ENV_URL", "http://localhost:8000")

# Initialize OpenAI-compatible client
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN,
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
def log_start(task_id: str, task_name: str):
    """Emit [START] log."""
    print(f"[START] task_id={task_id} task_name={task_name} timestamp={datetime.now(timezone.utc).isoformat()}")
    sys.stdout.flush()


def log_step(task_id: str, step_num: int, action: dict, observation: dict, reward: float, done: bool):
    """Emit [STEP] log."""
    print(
        f"[STEP] task_id={task_id} step={step_num} "
        f"action={json.dumps(action)} "
        f"observation={json.dumps(observation)} "
        f"reward={reward} done={done} "
        f"timestamp={datetime.now(timezone.utc).isoformat()}"
    )
    sys.stdout.flush()


def log_end(task_id: str, task_name: str, final_score: float, total_steps: int):
    """Emit [END] log."""
    print(
        f"[END] task_id={task_id} task_name={task_name} "
        f"score={final_score} steps={total_steps} "
        f"timestamp={datetime.now(timezone.utc).isoformat()}"
    )
    sys.stdout.flush()


# ──────────────────────────────────────────────
# Main task runner
# ──────────────────────────────────────────────
def run_task(task: dict) -> float:
    """Run a single task using the LLM agent. Returns the final reward score."""
    task_id = task["id"]
    task_name = task["name"]
    system_prompt = task["system_prompt"]

    log_start(task_id, task_name)

    # Reset environment
    reset_data = env_reset(task_id)
    obs = reset_data.get("observation", {})
    info = obs.get("info", "")

    conversation = [
        {"role": "user", "content": f"Task started. Environment says: {info}\nDecide your first action."}
    ]

    cumulative_reward = 0.0
    step_num = 0

    for step_num in range(1, MAX_STEPS_PER_TASK + 1):
        try:
            # Ask LLM for next action
            action = ask_llm(system_prompt, conversation)
        except Exception as e:
            print(f"[ERROR] LLM call failed at step {step_num}: {e}", file=sys.stderr)
            break

        # Execute the action in the environment
        try:
            result = env_step(action)
        except Exception as e:
            print(f"[ERROR] Environment step failed at step {step_num}: {e}", file=sys.stderr)
            break

        obs = result.get("observation", {})
        reward = result.get("reward", 0.0)
        done = result.get("done", False)
        cumulative_reward += reward

        # Log the step
        log_step(task_id, step_num, action, obs, reward, done)

        if done:
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

    log_end(task_id, task_name, cumulative_reward, step_num)
    return cumulative_reward


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
def main():
    print("=" * 60)
    print("CloudSecurityAuditor — OpenEnv Inference")
    print(f"Model: {MODEL_NAME}")
    print(f"API:   {API_BASE_URL}")
    print(f"Env:   {ENV_URL}")
    print("=" * 60)
    sys.stdout.flush()

    total_score = 0.0
    results = []

    for task in TASKS:
        try:
            score = run_task(task)
            results.append({"task_id": task["id"], "task_name": task["name"], "score": score})
            total_score += score
        except Exception as e:
            print(f"[ERROR] Task {task['id']} failed: {e}", file=sys.stderr)
            results.append({"task_id": task["id"], "task_name": task["name"], "score": 0.0})

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    for r in results:
        status = "✅ PASS" if r["score"] >= 1.0 else "❌ FAIL"
        print(f"  {r['task_name']:25s} → score={r['score']:.2f}  {status}")
    print(f"\n  Total Score: {total_score:.2f} / {len(TASKS)}.00")
    print("=" * 60)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
