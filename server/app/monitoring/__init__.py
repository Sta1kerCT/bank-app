"""
Monitoring Package
Metrics, logging, and observability
"""

from .metrics import (
    init_metrics,
    requests_counter,
    request_duration,
    accounts_counter,
    transactions_counter,
    accounts_balance_gauge,
    transaction_amount_gauge,
    metrics_endpoint,
    PrometheusMiddleware
)

__all__ = [
    "init_metrics",
    "requests_counter",
    "request_duration",
    "accounts_counter",
    "transactions_counter",
    "accounts_balance_gauge",
    "transaction_amount_gauge",
    "metrics_endpoint",
    "PrometheusMiddleware"
]

METRICS_PREFIX = "bank_"
HEALTH_CHECK_ENDPOINT = "/health"
METRICS_ENDPOINT = "/metrics"