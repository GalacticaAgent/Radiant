from typing import Any, Dict

from fastapi import APIRouter
from redis import Redis

from app.core.celery_app import celery_app
from app.core.config import settings
from app.utils.doc_convert import find_soffice


router = APIRouter()


@router.get("/health")
def system_health() -> Dict[str, Any]:
    broker_ok = False
    backend_ok = False
    workers = 0
    worker_ok = False
    errors: list[str] = []

    try:
        Redis.from_url(settings.CELERY_BROKER_URL).ping()
        broker_ok = True
    except Exception as e:
        errors.append(f"broker: {str(e)}")

    try:
        Redis.from_url(settings.CELERY_RESULT_BACKEND).ping()
        backend_ok = True
    except Exception as e:
        errors.append(f"backend: {str(e)}")

    if not getattr(settings, "CELERY_RUN_INLINE", False):
        try:
            insp = celery_app.control.inspect(timeout=1.0)
            pong = insp.ping() or {}
            workers = len(pong.keys())
            worker_ok = workers > 0
        except Exception as e:
            errors.append(f"worker: {str(e)}")

    status = "ok"
    if getattr(settings, "CELERY_RUN_INLINE", False):
        status = "degraded" if (not broker_ok and not backend_ok) else "ok"
    else:
        if not broker_ok or not backend_ok or not worker_ok:
            status = "degraded"

    soffice_path = None
    try:
        soffice_path = find_soffice()
    except Exception:
        soffice_path = None

    return {
        "status": status,
        "celery_run_inline": bool(getattr(settings, "CELERY_RUN_INLINE", False)),
        "broker_ok": broker_ok,
        "backend_ok": backend_ok,
        "worker_ok": worker_ok if not getattr(settings, "CELERY_RUN_INLINE", False) else None,
        "workers": workers if not getattr(settings, "CELERY_RUN_INLINE", False) else None,
        "soffice_path": soffice_path,
        "errors": errors,
    }
