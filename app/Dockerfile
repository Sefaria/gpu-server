FROM nvidia/cuda:12.2.2-cudnn8-devel-ubuntu22.04

# Set environment variables for non-interactive installations
ENV DEBIAN_FRONTEND=noninteractive

# Install common dependencies and Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    git \
    wget && \
    rm -rf /var/lib/apt/lists/*

# Set up venv for Python 3.11
RUN /usr/bin/python3.11 -m venv /opt/py311 \
 && /opt/py311/bin/python -m ensurepip --upgrade \
 && /opt/py311/bin/python -m pip install --upgrade pip setuptools wheel
ENV PATH="/opt/py311/bin:${PATH}"

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt
RUN python -m pip install --no-cache-dir gunicorn cupy-cuda12x spacy[cuda122]~=3.7.0

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "1", "--worker-class", "sync", "app:create_app()"]
