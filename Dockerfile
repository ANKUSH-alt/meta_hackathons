FROM python:3.10-slim

WORKDIR /app

# Copy requirement files first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY server/ ./server/
COPY scripts/ ./scripts/
COPY inference.py .
COPY openenv.yaml .
COPY README.md .
COPY DOCUMENTATION.md .

# Expose the API port (Hugging Face default)
EXPOSE 7860

# Start server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
