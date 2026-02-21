# AWS Modern Datalake - Python 3.10+
FROM python:3.12-slim

# Unbuffered stdout/stderr so prints show up in docker logs
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY python/ /app/python/

# Run from src so imports (config, converter, dtos, services) resolve
WORKDIR /app/python/src

# Mount .env and temp dirs at runtime; default command runs the pipeline
CMD ["python", "main.py"]
