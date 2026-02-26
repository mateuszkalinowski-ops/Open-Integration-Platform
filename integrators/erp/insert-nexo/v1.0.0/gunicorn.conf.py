"""Gunicorn configuration for InsERT Nexo Cloud Connector."""

import os

bind = f"0.0.0.0:{os.getenv('NEXO_CONNECTOR_PORT', '8000')}"
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("NEXO_CONNECTOR_LOG_LEVEL", "info").lower()
