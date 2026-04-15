# --- Build stage ---
FROM python:3.12-slim AS build
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
COPY . .

# --- Production stage ---
FROM python:3.12-slim
LABEL maintainer="integrations@pinquark.com"
LABEL version="2.0.0"
LABEL category="courier"
LABEL system="inpost"


RUN apt-get update -qq && apt-get upgrade -y --no-install-recommends && rm -rf /var/lib/apt/lists/*
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
WORKDIR /app
COPY --from=build /install /usr/local
COPY --from=build /app .
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
