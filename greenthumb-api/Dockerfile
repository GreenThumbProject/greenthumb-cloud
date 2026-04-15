# ============================================================
# GreenThumb Cloud API — Dockerfile
# ============================================================
FROM python:3.11-slim-bullseye AS base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel

# Heavy deps (cached unless requirements-base.txt changes)
COPY cloud/greenthumb-api/requirements-base.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements-base.txt

# ============================================================
FROM base AS app

WORKDIR /usr/src/app

# Install greenthumb-models (shared with Pi)
COPY rasp5/greenthumb-models/ /tmp/greenthumb-models/
RUN pip install --no-cache-dir "utils @ git+https://github.com/henriquebrnetto/utils.git" && \
    pip install --no-cache-dir /tmp/greenthumb-models

COPY cloud/greenthumb-api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY cloud/greenthumb-api/ .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
