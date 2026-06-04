FROM python:3.12-slim AS build
WORKDIR /app
COPY platform/requirements.txt .
COPY shared/python /shared/python
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
LABEL maintainer="integrations@pinquark.com"
LABEL version="0.1.0"
LABEL component="platform"

RUN apt-get update -qq && apt-get upgrade -y --no-install-recommends && apt-get install -y --no-install-recommends curl libpq5 \
    && rm -rf /var/lib/apt/lists/*
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
WORKDIR /app
COPY --from=build /install /usr/local
COPY --from=build /app /app
COPY platform/ .
RUN chmod +x entrypoint.sh && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
