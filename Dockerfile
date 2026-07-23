FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860 \
    GRADIO_ANALYTICS_ENABLED=False \
    HF_HUB_DISABLE_TELEMETRY=1 \
    HF_HOME=/home/user/.cache/huggingface \
    XDG_CACHE_HOME=/home/user/.cache \
    DOCLING_ARTIFACTS_PATH=/home/user/.cache/docling/models \
    DOCLING_DEVICE=cpu \
    DOCLING_NUM_THREADS=2 \
    OMP_NUM_THREADS=2 \
    MKL_NUM_THREADS=2

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 user

WORKDIR /home/user/app

COPY requirements.txt /tmp/requirements.txt

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch torchvision \
    && python -m pip install --no-cache-dir \
        -r /tmp/requirements.txt

USER user

# Descarga los modelos durante la construcción del Space.
# Así la primera conversión no tiene que descargarlos.
RUN mkdir -p /home/user/.cache/docling/models \
    && docling-tools models download

COPY --chown=user:user . /home/user/app

EXPOSE 7860

CMD ["python", "app.py"]
