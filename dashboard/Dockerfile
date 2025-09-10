# Superior Agents Dashboard Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY dashboard/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy dashboard application
COPY dashboard/ /app/dashboard/

# Copy database and other necessary files
COPY db/ /app/db/
COPY agent/db/ /app/agent/db/

# Create necessary directories
RUN mkdir -p /app/agent/db

# Set environment variables
ENV PYTHONPATH=/app
ENV SQLITE_PATH=/app/agent/db/superior-agents.db
ENV RAG_SERVICE_URL=http://rag-api:32771
ENV ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run the dashboard
CMD ["python", "/app/dashboard/app.py"]
