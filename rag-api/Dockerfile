FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl wget fuse gzip \
    debian-keyring debian-archive-keyring apt-transport-https \
    rclone \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY rag-api/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application
COPY rag-api/ .

EXPOSE 8080

HEALTHCHECK CMD curl --fail http://localhost:8080/health

ENTRYPOINT [ "python", "scripts/api.py" ]