# ☁️🛡️ CloudSecurityAuditor — OpenEnv Environment

## Complete Application Documentation

---

## 1. What Is This Application?

**CloudSecurityAuditor** is a standardized AI agent environment that simulates real-world cloud security auditing scenarios. It is built using the [OpenEnv](https://github.com/openenv) specification — an open standard for creating reproducible, programmable environments where AI agents can be trained, tested, and benchmarked.

Think of it as a **virtual cybersecurity lab**: instead of risking real cloud infrastructure, an AI agent (or a human) can interact with a mock cloud environment that contains intentional security vulnerabilities. The agent must discover, analyze, and remediate those vulnerabilities to earn a reward.

### Who Is This For?

| Audience | Use Case |
|---|---|
| **AI Researchers** | Benchmark LLM-based security agents on structured tasks |
| **Security Engineers** | Practice cloud audit workflows in a safe sandbox |
| **Students** | Learn about S3 public buckets, EC2 security groups, and IAM log analysis |
| **Hackathon Participants** | Demonstrate agent-environment interaction for Meta/OpenEnv challenges |

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   BROWSER (UI)                      │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Sidebar  │  │ Resource Grid│  │ Execution Log│  │
│  │ (Tasks)  │  │ (S3 / EC2)  │  │ (Terminal)   │  │
│  └──────────┘  └──────────────┘  └──────────────┘  │
└───────────────────────┬─────────────────────────────┘
                        │  HTTP (REST)
                        ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Server (app.py)                 │
│  ┌─────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ /reset  │  │  /step   │  │  /state  /  /docs │  │
│  └────┬────┘  └────┬─────┘  └───────────────────┘  │
│       │            │                                │
│       ▼            ▼                                │
│  ┌─────────────────────────────────────────────┐    │
│  │         CloudAuditEnv (environment.py)      │    │
│  │  ┌─────────┐  ┌────────┐  ┌──────────────┐ │    │
│  │  │ S3 Data │  │EC2 Data│  │ Auth Logs    │ │    │
│  │  └─────────┘  └────────┘  └──────────────┘ │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## 3. File Structure

```
scaler/
├── server/
│   ├── app.py              # FastAPI entry point, static file serving
│   ├── environment.py      # Core environment logic (reset, step, state)
│   ├── models.py           # Pydantic/dataclass models (Action, Observation, State)
│   ├── tasks.py            # Task definitions (Easy, Medium, Hard)
│   └── static/
│       ├── index.html      # Dashboard UI layout
│       ├── index.css       # Dark-mode cybersecurity theme
│       └── app.js          # Frontend logic & API interaction
├── scripts/
│   └── baseline_inference.py   # Example agent that solves the Easy task
├── openenv.yaml            # OpenEnv specification file
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker deployment configuration
└── README.md               # Quick-start guide
```

---

## 4. The Environment Engine (`environment.py`)

The heart of the application is the `CloudAuditEnv` class. It implements three methods required by the OpenEnv spec:

### `reset(task_id) → Observation`
- Reinitializes the mock infrastructure (S3 buckets, EC2 instances, auth logs).
- Sets the active task (easy, medium, or hard).
- Returns an initial observation with status info.

### `step(action) → Observation`
- Accepts a `CloudAction` and executes it against the mock infrastructure.
- Returns an updated `CloudObservation` containing discovered resources, details, logs, and a reward signal.
- Automatically terminates the episode after 20 steps (truncation).

### `state() → CloudState`
- Returns internal metadata: episode ID, step count, task ID, completion status, and cumulative score.

---

## 5. Mock Infrastructure

The environment simulates the following cloud resources:

### S3 Buckets (3 total)

| ID | Region | Public? | Environment |
|---|---|---|---|
| `prod-data-001` | us-east-1 | ✅ Yes | prod |
| `prod-logs-002` | us-east-1 | ❌ No | prod |
| `dev-test-01` | us-west-2 | ✅ Yes | dev |

### EC2 Instances (2 total)

| ID | Type | State | Environment | Open Ports |
|---|---|---|---|---|
| `i-0abcdef1234567890` | t2.micro | running | dev | 22 (SSH), **3389 (RDP)** ⚠️ |
| `i-0987654321fedcba0` | m5.large | running | prod | 443 (HTTPS) |

### Auth Logs (`auth-logs`)

| Timestamp | User | Action | IP |
|---|---|---|---|
| 2026-04-05T10:00:00Z | admin | Login | 1.1.1.1 |
| 2026-04-05T10:15:00Z | iam-role-01 | **DeleteStorage** ⚠️ | **192.168.1.50** |
| 2026-04-05T10:30:00Z | user-02 | ListBuckets | 2.2.2.2 |

---

## 6. Action Space

The agent interacts with the environment using a `CloudAction` object. Available action types:

| Action | Parameters | Description |
|---|---|---|
| `list` | `resource_type` (s3, ec2) | Lists all resources of a given type |
| `describe` | `resource_id` | Returns full details for a specific resource |
| `modify` | `resource_id`, `patch` | Updates resource configuration (e.g., security group rules) |
| `logs` | `resource_id` (e.g., auth-logs) | Fetches log entries for a service |
| `submit` | `answer` | Submits the final answer for grading |

### Example Actions (via Dashboard or API)

```bash
# List all S3 buckets
list s3

# Describe an EC2 instance
describe i-0abcdef1234567890

# Fetch authentication logs
logs auth-logs

# Submit an answer for Easy task
submit prod-data-001

# Submit an answer for Hard task
submit 192.168.1.50
```

---

## 7. Observation Space

Every `step()` and `reset()` returns a `CloudObservation`:

| Field | Type | Description |
|---|---|---|
| `resources` | `List[Dict]` | List of discovered resource records |
| `details` | `Dict` | Full metadata for a single described resource |
| `logs` | `List[Dict]` | Log entries (timestamp, user, action, IP) |
| `status` | `str` | Human-readable status message |
| `info` | `str` | Additional context (e.g., grading feedback) |
| `reward` | `float` | Scalar reward (0.0 to 1.0) |
| `done` | `bool` | Whether the episode has ended |

---

## 8. Tasks & Grading

### Task 1: Easy — S3 Public Audit
**Goal:** Identify all S3 buckets that are both `public: true` AND tagged `env: prod`.

| Step | Action | Expected Result |
|---|---|---|
| 1 | `list s3` | Returns 3 buckets |
| 2 | Filter for public + prod | `prod-data-001` |
| 3 | `submit prod-data-001` | Reward: **1.0** ✅ |

---

### Task 2: Medium — EC2 Security Patch
**Goal:** Find EC2 instance `i-0abcdef1234567890` which has port 3389 (RDP) open to `0.0.0.0/0`, and close it by modifying the security group to only allow port 22.

| Step | Action | Expected Result |
|---|---|---|
| 1 | `list ec2` | Returns 2 instances |
| 2 | `describe i-0abcdef1234567890` | Shows RDP port open |
| 3 | `modify i-0abcdef1234567890` with patch `{"rules": [{"port": 22, "cidr": "0.0.0.0/0"}]}` | Reward: **1.0** ✅ |

---

### Task 3: Hard — IAM Log Forensic
**Goal:** A rogue IAM role (`iam-role-01`) has performed unauthorized actions. Analyze the `auth-logs` to identify the IP address that performed `DeleteStorage`.

| Step | Action | Expected Result |
|---|---|---|
| 1 | `logs auth-logs` | Returns 3 log entries |
| 2 | Find `DeleteStorage` action | IP: `192.168.1.50` |
| 3 | `submit 192.168.1.50` | Reward: **1.0** ✅ |

---

## 9. API Reference

Base URL: `http://localhost:8000`

### `POST /reset`
Reset the environment to a specific task.

**Request:**
```json
{ "task_id": "easy" }
```

**Response:**
```json
{
    "observation": {
        "resources": null,
        "details": null,
        "status": null,
        "logs": null,
        "info": "Environment reset. Task: easy"
    },
    "reward": 0.0,
    "done": false
}
```

### `POST /step`
Execute an action in the environment.

**Request:**
```json
{
    "action": {
        "action": "list",
        "resource_type": "s3"
    }
}
```

**Response:**
```json
{
    "observation": {
        "resources": [
            { "id": "prod-data-001", "region": "us-east-1", "public": true, "tags": { "env": "prod" } },
            { "id": "prod-logs-002", "region": "us-east-1", "public": false, "tags": { "env": "prod" } },
            { "id": "dev-test-01", "region": "us-west-2", "public": true, "tags": { "env": "dev" } }
        ],
        "status": "Listed 3 s3 resources."
    },
    "reward": 0.0,
    "done": false
}
```

### `GET /state`
Get internal environment state.

**Response:**
```json
{
    "episode_id": "a1b2c3d4-...",
    "step_count": 3,
    "task_id": "easy",
    "is_completed": false,
    "score": 0.0
}
```

### `GET /docs`
Interactive Swagger UI for API exploration.

### `GET /`
Dashboard UI (the web interface).

---

## 10. Dashboard UI

The application includes a premium dark-mode cybersecurity dashboard accessible at `http://localhost:8000`.

### Features
- **Sidebar Task Selector** — Switch between Easy, Medium, and Hard challenges with one click.
- **Infrastructure Overview** — Visual resource cards for S3 buckets and EC2 instances. Vulnerable resources are highlighted with red borders and blinking status dots.
- **Execution Log** — Terminal-style console showing timestamped action logs with color-coded entries (blue for actions, green for system, yellow for rewards, red for errors).
- **Manual Command Input** — Type commands like `list s3`, `describe i-0abcdef1234567890`, `logs auth-logs`, or `submit prod-data-001` directly in the dashboard.
- **Live Stats HUD** — Displays current task name, cumulative reward, and environment status (Active/Completed).

### Design
- **Theme:** Cyber-noir dark mode with deep navy background (#0a0e14)
- **Accents:** Neon cyan (#00f5ff) for primary elements
- **Typography:** Inter (body), Outfit (headings), JetBrains Mono (code/logs)
- **Effects:** Glassmorphism panels, fade-in card animations, pulsing vulnerability indicators

---

## 11. Running the Application

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python -m server.app

# Open in browser
open http://localhost:8000
```

### Running the Baseline Agent
```bash
# Solves the Easy task automatically
python scripts/baseline_inference.py
```

### Docker Deployment
```bash
# Build the image
docker build -t cloud-security-auditor .

# Run the container
docker run -p 8000:8000 cloud-security-auditor
```

### Hugging Face Spaces Deployment
1. Create a new Space on Hugging Face.
2. Select **Docker** as the SDK.
3. Upload the repository contents (including `openenv.yaml` and `Dockerfile`).
4. The entrypoint is automatically set via `openenv.yaml`.

---

## 12. Technology Stack

| Component | Technology |
|---|---|
| Backend | Python 3.10, FastAPI, Uvicorn |
| Environment | openenv-core ≥ 0.1.1 |
| Data Models | Python dataclasses |
| Frontend | Vanilla HTML/CSS/JS |
| Fonts | Google Fonts (Inter, Outfit, JetBrains Mono) |
| Deployment | Docker, Hugging Face Spaces |

---

## 13. OpenEnv Specification (`openenv.yaml`)

```yaml
name: cloud-security-auditor
version: "0.1.0"
description: "A real-world cloud security audit environment for AI agents."
hardware:
  tier: "cpu-small"
  vCPU: 2
  RAM: 4Gi
port: 8000
entrypoint: "uvicorn server.app:app --host 0.0.0.0 --port 8000"
tags:
  - security
  - cloud
  - task-based
evaluation:
  tasks:
    - id: "easy"
      name: "S3 Public Audit"
      difficulty: "easy"
    - id: "medium"
      name: "EC2 Security Patch"
      difficulty: "medium"
    - id: "hard"
      name: "IAM Log Forensic"
      difficulty: "hard"
```

---

## 14. Extending the Environment

### Adding a New Task
1. Add the task definition to `server/tasks.py`.
2. Add the corresponding mock data to `_initialize_state()` in `environment.py`.
3. Add the grading logic to the `step()` method under `CloudActionType.SUBMIT`.
4. Add a new task button to `index.html` in the sidebar.

### Adding a New Resource Type
1. Add the resource data to `self.resources` in `environment.py`.
2. Add a handler for `CloudActionType.LIST` and `CloudActionType.DESCRIBE` for the new type.
3. Update `detectResourceType()` in `app.js` to render the correct card icon/label.

---

*Built for the Meta Hackathon / OpenEnv Challenge • April 2026*
