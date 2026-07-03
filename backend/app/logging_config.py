import json
import logging
import logging.config
from datetime import UTC, datetime
from typing import Any

from app.config import get_settings

_STANDARD_RECORD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Anything passed via `logger.info(..., extra={...})` lands as plain
        # attributes on the record — merge those in as structured context.
        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_ATTRS:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Routes every logger — ours and uvicorn's — through one JSON formatter,
    so log aggregation (CloudWatch, Render/Vercel logs, etc.) gets structured
    lines instead of uvicorn's default plain-text access log format."""
    settings = get_settings()
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": JsonFormatter}},
            "handlers": {
                "console": {"class": "logging.StreamHandler", "formatter": "json"},
            },
            "root": {"handlers": ["console"], "level": settings.log_level},
            "loggers": {
                "uvicorn": {
                    "handlers": ["console"],
                    "level": settings.log_level,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["console"],
                    "level": settings.log_level,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["console"],
                    "level": settings.log_level,
                    "propagate": False,
                },
            },
        }
    )
