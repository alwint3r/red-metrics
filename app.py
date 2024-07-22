from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import (
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
import time

app = FastAPI()

http_request_dur_hist = Histogram(
    "request_duration_seconds",
    "The latency of the HTTP requests",
    labelnames=["method", "service", "code", "handler"],
    subsystem="http",
)

http_response_size_hist = Histogram(
    "response_size_bytes",
    "The size of the HTTP responses",
    labelnames=["method", "service", "code", "handler"],
    subsystem="http",
)

http_requests_inflights_gauge = Gauge(
    "requests_inflight",
    "The number of inflight requests being handled at the same time.",
    labelnames=["method", "service", "handler"],
    subsystem="http",
)


@app.middleware("http")
async def add_metrics_middleware(request: Request, call_next):
    method = request.method
    endpoint = request.url.path
    start_time = time.time()

    if endpoint == "/metrics":
        return await call_next(request)

    http_requests_inflights_gauge.labels(method, "fastapi-service", endpoint).inc()
    response_length = 0
    try:
        response = await call_next(request)
        response_length = (
            response.headers["content-length"]
            if "content-length" in response.headers
            else 0
        )
        response_length = int(response_length)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        response = JSONResponse(status_code=status_code, content={"detail": str(e)})
    duration = time.time() - start_time
    http_response_size_hist.labels(
        method, "fastapi-service", status_code, endpoint
    ).observe(response_length)
    http_request_dur_hist.labels(
        method, "fastapi-service", status_code, endpoint
    ).observe(duration)
    http_requests_inflights_gauge.labels(method, "fastapi-service", endpoint).dec()

    return response


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/example")
async def example_endpoint():
    return {"message": "This is an example endpoint"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
