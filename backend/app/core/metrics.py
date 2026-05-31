"""Prometheus metrics — request and LLM instrumentation exposed at ``/metrics``.

Production hardening (Project 3): gives operators counters/histograms to build dashboards and
alerts (request rate, error rate, latency percentiles, LLM call volume and failures). The
default process/GC collectors are also exported by ``prometheus_client``.
"""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

# --- HTTP server metrics ---------------------------------------------------------------------
http_requests_total = Counter(
    "finsight_http_requests_total",
    "Total HTTP requests.",
    labelnames=("method", "path", "status"),
)
http_request_duration_seconds = Histogram(
    "finsight_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    labelnames=("method", "path"),
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)

# --- LLM / model metrics ---------------------------------------------------------------------
llm_calls_total = Counter(
    "finsight_llm_calls_total",
    "LLM/embedding calls by operation and outcome.",
    labelnames=("operation", "outcome"),  # outcome: success | error
)
llm_retries_total = Counter(
    "finsight_llm_retries_total",
    "Number of transient-error retries performed against the model provider.",
    labelnames=("operation",),
)
guardrail_blocks_total = Counter(
    "finsight_guardrail_blocks_total",
    "Requests blocked by input guardrails, by reason.",
    labelnames=("reason",),
)
rate_limited_total = Counter(
    "finsight_rate_limited_total",
    "Requests rejected by the rate limiter.",
)


def render_metrics() -> tuple[bytes, str]:
    """Return (payload, content_type) for the Prometheus exposition endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST
