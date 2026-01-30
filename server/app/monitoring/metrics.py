from prometheus_client import Counter, Gauge, Histogram, generate_latest, REGISTRY
from fastapi import Response
from fastapi.routing import APIRoute
import time
from typing import Callable
from fastapi import Request

requests_counter = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

accounts_counter = Counter(
    'bank_accounts_total',
    'Total accounts operations',
    ['action']
)

transactions_counter = Counter(
    'bank_transactions_total',
    'Total transactions',
    ['type', 'status']
)

accounts_balance_gauge = Gauge(
    'bank_account_balance',
    'Account balance',
    ['account_number']
)

transaction_amount_gauge = Gauge(
    'bank_transaction_amount',
    'Transaction amount',
    ['transaction_id']
)


def init_metrics():
    """Initialize metrics"""
    pass


class PrometheusMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        method = scope['method']
        endpoint = scope['path']

        async def send_wrapper(response):
            if response['type'] == 'http.response.start':
                status_code = response['status']
                duration = time.time() - start_time

                requests_counter.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status_code
                ).inc()

                request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)

            await send(response)

        await self.app(scope, receive, send_wrapper)


def metrics_endpoint(request: Request) -> Response:
    """Endpoint for Prometheus to scrape metrics"""
    return Response(content=generate_latest(REGISTRY), media_type="text/plain")