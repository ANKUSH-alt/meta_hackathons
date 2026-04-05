# CloudSecurityAuditor OpenEnv

A standardized AI agent environment for simulating real-world cloud security audits. Built using the **OpenEnv** specification, it allows agents to interact with a mock cloud infrastructure to identify and remediate vulnerabilities.

## 🌟 Key Features
- **Typed Models**: Full Pydantic support for actions and observations.
- **Three Task Tiers**: Includes Easy (Information Gathering), Medium (Remediation), and Hard (Forensic Analysis).
- **Gymnasium-Compatible API**: Implements `step()`, `reset()`, and `state()` methods.
- **Reward-Driven**: Scalar rewards from 0.0 to 1.0 based on task completion.

## 🛠 Action Space
The agent can perform the following actions via the `step()` method:

- **`list`**: Lists resources of a specific type (`s3`, `ec2`).
- **`describe`**: Fetches detailed configuration for a specific resource ID.
- **`modify`**: Updates resource configurations (e.g., security groups).
- **`logs`**: Retrieves logs for a specific resource or service.
- **`submit`**: Submits the final answer for the evaluation tasks.

## 📊 Observation Space
Each step returns a `CloudObservation` containing:
- `resources`: A list of discovered resource records.
- `details`: Metadata for a specific resource.
- `logs`: Relevant log entries.
- `status`: Human-readable status message.
- `info`: Additional environment metadata.

## 📋 Tasks

1. **Easy (S3 Public Audit)**: Identify all public S3 buckets in the 'prod' region.
2. **Medium (EC2 Security Patch)**: Find an EC2 instance with RDP port open to the internet and close it.
3. **Hard (IAM Log Forensic)**: Trace unauthorized actions in `auth-logs` to identify a rogue IP address.

## 🚀 Setup & Installation

### Local Installation
```bash
pip install -r requirements.txt
```

### Running the Server
```bash
python -m server.app
```
The server will start on `http://localhost:8000`.

### Running the Baseline Agent
```bash
python scripts/baseline_inference.py
```

## 🐳 Docker Deployment
To build and run the containerized environment:
```bash
docker build -t cloud-security-auditor-env .
docker run -p 8000:8000 cloud-security-auditor-env
```

## 🤗 Hugging Face Spaces
This environment is designed to be deployed as an **OpenEnv Space**.
1. Create a new Space on Hugging Face.
2. Select **Docker** as the SDK.
3. Upload the repository contents (including `openenv.yaml` and `Dockerfile`).
4. Set the `entrypoint` to match the `uvicorn` command in `openenv.yaml`.
