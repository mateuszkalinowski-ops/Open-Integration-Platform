"""Prometheus metrics setup for integrators."""

from prometheus_client import Counter, Histogram, Gauge


def setup_metrics(service_name: str) -> dict:
    return {
        "requests_total": Counter(
            "integrator_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
        ),
        "request_duration": Histogram(
            "integrator_request_duration_seconds",
            "HTTP request latency",
            ["method", "endpoint"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        ),
        "external_api_calls_total": Counter(
            "integrator_external_api_calls_total",
            "Total external API calls",
            ["system", "operation", "status"],
        ),
        "external_api_duration": Histogram(
            "integrator_external_api_duration_seconds",
            "External API call latency",
            ["system", "operation"],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
        ),
        "errors_total": Counter(
            "integrator_errors_total",
            "Total errors",
            ["type"],
        ),
        "kafka_messages_total": Counter(
            "integrator_kafka_messages_processed_total",
            "Kafka messages processed",
            ["topic", "status"],
        ),
        "active_accounts": Gauge(
            "integrator_active_accounts",
            "Number of active accounts",
            ["system"],
        ),
    }
