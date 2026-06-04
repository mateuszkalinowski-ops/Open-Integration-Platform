# --- Build stage ---
FROM python:3.12-slim AS build

WORKDIR /app

COPY integrators/other/ksef/v1.0.0/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY shared/python /shared
RUN pip install --no-cache-dir --prefix=/install /shared

COPY integrators/other/ksef/v1.0.0/ .

# --- Production stage ---
FROM python:3.12-slim

LABEL maintainer="integrations@pinquark.com"
LABEL version="1.0.0"
LABEL category="other"
LABEL system="ksef"

RUN apt-get update -qq && apt-get upgrade -y --no-install-recommends && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

COPY --from=build /install /usr/local
COPY --from=build /app/src ./src
COPY --from=build /app/config ./config
COPY --from=build /app/xsd ./xsd
COPY --from=build /app/connector.yaml ./connector.yaml

RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health'); r.raise_for_status()" || exit 1

ENTRYPOINT ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
