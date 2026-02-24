# --- Build stage ---
FROM python:3.12-slim AS build
WORKDIR /app
COPY platform/verification-agent/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
COPY platform/verification-agent/ .

# --- Production stage ---
FROM python:3.12-slim
LABEL maintainer="integrations@pinquark.com"
LABEL version="1.0.0"
LABEL component="verification-agent"

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
WORKDIR /app
COPY --from=build /install /usr/local
COPY --from=build /app .
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
