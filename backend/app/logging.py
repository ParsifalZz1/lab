import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

trace_id_context: ContextVar[str | None] = ContextVar("trace_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        trace_id = getattr(record, "trace_id", None) or trace_id_context.get()
        if trace_id:
            payload["trace_id"] = trace_id
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(log_level: str) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    for handler in root_logger.handlers:
        if getattr(handler, "_modelflow_handler", False):
            return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler._modelflow_handler = True  # type: ignore[attr-defined]
    root_logger.addHandler(handler)
