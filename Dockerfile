FROM python:3.10-slim

WORKDIR /app

# Copy requirement files first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY server/ ./server/
COPY openenv.yaml .

# Expose the API port
EXPOSE 8000

# Start server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
