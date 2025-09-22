"""Project package initialization with optional Celery integration."""

from __future__ import annotations

import logging

celery_app = None

try:
    from .celery import app as celery_app
except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
    logging.getLogger(__name__).warning(
        "Celery is not installed; asynchronous task runner disabled. (%s)", exc
    )
except Exception as exc:  # pragma: no cover - defensive
    logging.getLogger(__name__).exception("Celery configuration failed: %s", exc)

__all__ = ("celery_app",)
