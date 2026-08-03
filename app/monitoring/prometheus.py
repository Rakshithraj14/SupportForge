from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Histogram, generate_latest

router = APIRouter()

# Both metrics below are only ever recorded from the FastAPI/bot process (chat
# generation and its HTTP entry point both run there — ingestion/evaluation are
# offloaded to Celery, but a separate worker process has its own prometheus_client
# registry, so metrics recorded there wouldn't appear via this app's /metrics at
# all without multiprocess-mode wiring). Evaluation score trends are read
# straight from Postgres by Grafana instead of routed through Prometheus.

HTTP_REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path", "status_code"],
)

CHAT_TOKENS = Histogram(
    "chat_tokens",
    "Tokens used per chat generation call",
    ["type"],
)


@router.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
