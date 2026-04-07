---
title: Cloud Security Auditor
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
---

# 🛡️ CloudSecurityAuditor OpenEnv

**CloudSecurityAuditor** is a high-fidelity, standardized AI agent environment designed to simulate real-world cloud security audit scenarios. Built upon the **OpenEnv** specification, it provides a safe, reproducible sandbox where autonomous agents can practice identifying, analyzing, and remediating critical security vulnerabilities in a mock cloud infrastructure.

This environment is specifically engineered for benchmarking LLM-based security agents, offering a structured API and deterministic evaluation metrics.

## 🌟 Key Features

- **Standardized API**: Fully compliant with the `openenv-core` specification, featuring Gymnasium-style `step()`, `reset()`, and `state()` methods.
- **Realistic Cloud Mocking**: Simulates S3 bucket configurations, EC2 security groups, and IAM audit logs with high precision.
- **Multi-Tiered Evaluation**:
    - **Easy (Audit)**: Focuses on information gathering and resource tagging.
    - **Medium (Remediation)**: Requires active patching and configuration changes.
    - **Hard (Forensics)**: Demands log analysis and pattern matching to identify rogue actors.
- **Typed Observations**: Robust Pydantic-based action and observation models ensure reliable agent-environment interactions.
- **Automated Grading**: Scalar reward functions (0.0 to 1.0) provide immediate, granular feedback on agent performance.

## 🛠 Action & Observation Space

### Actions
- `list`: Inventory resources (`s3`, `ec2`).
- `describe`: Deep-dive into resource metadata.
- `modify`: Apply security patches and rule updates.
- `logs`: Extract forensic evidence from authentication logs.
- `submit`: Finalize the task with a structured answer.

### Observations
- `resources`: Comprehensive resource records.
- `details`: Metadata for specific entities.
- `logs`: Event-based log entries.
- `status`: Execution status and helper messages.

## 📊 Available Tasks

| ID | Name | Objective | Difficulty |
|:---|:---|:---|:---|
| `easy` | **S3 Public Audit** | Identify public 'prod' buckets. | Auditing |
| `medium` | **EC2 Security Patch** | Remediate open RDP ports (3389). | Remediation |
| `hard` | **IAM Log Forensic** | Trace 'DeleteStorage' actions in logs. | Forensics |

## 🚀 Quick Start (Hugging Face)

If you are running this in a **Hugging Face Space**:

1.  **Examine the API**: The environment is hosted as a FastAPI server. Use the `/ui` endpoint for a visual dashboard.
2.  **Inference**: Run the `inference.py` script locally, pointing the `ENV_URL` to your Space's URL.
3.  **Evaluate**: The system will emit standardized logs for automated leaderboard tracking.

## 🐳 Local Deployment

```bash
# Clone and Install
pip install -r requirements.txt

# Run Server
python -m server.app

# Run Baseline
python inference.py
```

---
Built with ❤️ for the AI Security community.
