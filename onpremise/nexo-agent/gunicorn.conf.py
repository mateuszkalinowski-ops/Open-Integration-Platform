"""Gunicorn configuration for InsERT Nexo On-Premise Agent."""

import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('NEXO_AGENT_PORT', '8000')}"
workers = 1  # Single worker — Nexo SDK is not thread-safe across connections
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("NEXO_AGENT_LOG_LEVEL", "info").lower()
