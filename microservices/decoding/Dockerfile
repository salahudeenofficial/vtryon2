FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY shared_utils /app/shared_utils
COPY ../nodes.py /app/nodes.py
COPY ../comfy /app/comfy
COPY ../custom_nodes /app/custom_nodes

COPY . /app

EXPOSE 8080

ENV MODE=rest
ENV PORT=8080

CMD ["python3", "main.py"]

