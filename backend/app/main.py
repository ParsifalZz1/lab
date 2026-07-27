import logging
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response

from app.config import Settings, get_settings
from app.logging import configure_logging, trace_id_context

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="ModelFlow API", version="0.1.0")
    app.state.settings = settings

    @app.middleware("http")
    async def add_trace_id(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        trace_id = request.headers.get("X-Request-Id") or f"trace_{uuid4().hex}"
        trace_token = trace_id_context.set(trace_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-Id"] = trace_id
            logger.info(
                "request.completed",
                extra={"trace_id": trace_id, "method": request.method, "path": request.url.path},
            )
            return response
        finally:
            trace_id_context.reset(trace_token)

    @app.get("/healthz")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
