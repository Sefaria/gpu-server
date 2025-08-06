FROM nvidia/cuda:12.2.2-cudnn8-devel-ubuntu22.04

# Set environment variables for non-interactive installations
ENV DEBIAN_FRONTEND=noninteractive

# Install common dependencies and Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3.11 \
    python3.11-dev \
    python3-pip \
    git \
    wget && \
    rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as the default python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "1", "--worker-class", "sync", "app:create_app()"]
