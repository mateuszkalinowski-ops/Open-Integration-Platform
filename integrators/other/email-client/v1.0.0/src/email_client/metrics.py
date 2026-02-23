"""Shared Prometheus metrics instance for the email client connector."""

from pinquark_common.monitoring.metrics import setup_metrics

metrics = setup_metrics("email_client")
