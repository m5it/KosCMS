# KosDB Docker Image

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy KosDB source
COPY *.py ./

# Create data directory
RUN mkdir -p /data

# Expose ports
EXPOSE 9999 10999

# Environment variables
ENV SERVER_ID=1
ENV ROLE=master
ENV DATA_DIR=/data

# Entry point
CMD python server.py \
    --host 0.0.0.0 \
    --port 9999 \
    --data_dir /data \
    --server-id ${SERVER_ID} \
    --role ${ROLE} \
    ${MASTER_HOST:+--master-host ${MASTER_HOST}} \
    ${REPLICATION_PORT:+--replication-port ${REPLICATION_PORT}} \
    ${PEER_HOST:+--peer-host ${PEER_HOST}}