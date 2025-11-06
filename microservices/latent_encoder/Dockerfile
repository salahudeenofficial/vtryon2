# Latent Encoder Dockerfile

FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy ComfyUI dependencies (shared)
COPY shared_utils /app/shared_utils
COPY ../nodes.py /app/nodes.py
COPY ../comfy /app/comfy
COPY ../custom_nodes /app/custom_nodes

# Copy service code
COPY . /app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run service
# Supports multiple modes: REST, gRPC, Kafka, File-based
ENV MODE=rest
ENV PORT=8080

CMD ["python3", "main.py"]

