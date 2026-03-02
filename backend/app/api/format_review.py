import json
import os
import time
import threading
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.api.common.response import ok
from app.api.deps import get_current_user, get_current_user_from_query, get_db
from app.db.redis import redis_client
from app.models.format_review import DownloadToken, FormatReviewFixTask, FormatReviewHistory, FormatReviewSession, FormatReviewTask, FormatReviewUpload
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.format_review import (
    FormatReviewAutoFixRequest,
    FormatReviewAutoFixResult,
    FormatReviewFixTaskResult,
    FormatReviewHistoryList,
    FormatReviewHistorySaveRequest,
    FormatReviewHistorySaveResult,
    FormatReviewStartRequest,
    FormatReviewStartResult,
    FormatReviewTaskResult,
)
from app.tasks.format_review_tasks import format_review_run
from app.tasks.format_fix_tasks import format_review_auto_fix
from app.core.config import settings

router = APIRouter()


def _progress_key(task_id: UUID) -> str:
    return f"format_review:task:{task_id}"


def _enqueue_format_review_task(task_id: str):
    if getattr(settings, "CELERY_RUN_INLINE", False):
        try:
            threading.Thread(target=format_review_run, args=(task_id,), daemon=True).start()
        except Exception:
            pass
        return
    try:
        format_review_run.delay(task_id)
    except Exception:
        pass


@router.post("/start", response_model=ApiResponse)
def start_format_review(
    payload: FormatReviewStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.upload_id:
        upload = (
            db.query(FormatReviewUpload)
            .filter(FormatReviewUpload.id == payload.upload_id, FormatReviewUpload.user_id == current_user.id)
            .first()
        )
        if not upload:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="upload not found")
        if upload.status != "ready":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"upload not ready: {upload.status}")

    session = (
        db.query(FormatReviewSession)
        .filter(FormatReviewSession.user_id == current_user.id, FormatReviewSession.session_key == payload.session_id)
        .first()
    )
    if not session:
        session = FormatReviewSession(user_id=current_user.id, session_key=payload.session_id)
        db.add(session)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()

    task = FormatReviewTask(
        user_id=current_user.id,
        session_key=payload.session_id,
        upload_id=payload.upload_id,
        rule_id=payload.rule_id,
        status="queued",
        progress=0,
        result={
            "meta": {
                "paper_title": payload.paper_title,
                "filename": payload.filename,
            }
        },
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    background_tasks.add_task(_enqueue_format_review_task, str(task.id))

    return ok(FormatReviewStartResult(task_id=task.id).model_dump())


@router.get("/task/{task_id}", response_model=ApiResponse)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(FormatReviewTask).filter(FormatReviewTask.id == task_id, FormatReviewTask.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")

    cached = redis_client.get_json(_progress_key(task.id)) or {}
    progress = int(cached.get("progress") if cached.get("progress") is not None else task.progress or 0)
    status_text = str(cached.get("status") or task.status)

    res = FormatReviewTaskResult(
        task_id=task.id,
        session_id=task.session_key,
        status=status_text,
        progress=progress,
        started_at=task.started_at,
        ended_at=task.ended_at,
        duration_ms=task.duration_ms,
        error=task.error,
        result=task.result,
    )
    return ok(res.model_dump())


@router.get("/task/{task_id}/stream")
def stream_task(task_id: UUID, current_user: User = Depends(get_current_user_from_query), db: Session = Depends(get_db)):
    task = db.query(FormatReviewTask).filter(FormatReviewTask.id == task_id, FormatReviewTask.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")

    def gen():
        last_payload: Optional[str] = None
        start = time.time()
        while True:
            cached = redis_client.get_json(_progress_key(task.id)) or {}
            status_text = str(cached.get("status") or task.status)
            progress = int(cached.get("progress") if cached.get("progress") is not None else task.progress or 0)
            payload = json.dumps({"taskId": str(task.id), "status": status_text, "progress": progress}, ensure_ascii=False)
            if payload != last_payload:
                yield f"data: {payload}\n\n"
                last_payload = payload
            if status_text in ("done", "failed", "canceled"):
                yield "data: {\"done\": true}\n\n"
                break
            if time.time() - start > 1200:
                yield "data: {\"done\": false, \"timeout\": true}\n\n"
                break
            time.sleep(1.0)

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/history/save", response_model=ApiResponse)
def save_history(
    payload: FormatReviewHistorySaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(FormatReviewTask).filter(FormatReviewTask.id == payload.task_id, FormatReviewTask.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    if task.status != "done":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="task not completed")

    result = task.result or {}
    markdown = str(result.get("markdown") or "")
    issues = result.get("issues") if isinstance(result.get("issues"), list) else []
    meta = result.get("meta") if isinstance(result, dict) else {}
    paper_title = (meta or {}).get("paper_title") if isinstance(meta, dict) else None
    filename = (meta or {}).get("filename") if isinstance(meta, dict) else None

    history = FormatReviewHistory(
        user_id=current_user.id,
        session_key=task.session_key,
        task_id=task.id,
        paper_title=paper_title,
        filename=filename,
        status="done",
        duration_ms=task.duration_ms,
        issues_count=len(issues),
        report_markdown=markdown,
        result=result,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return ok(FormatReviewHistorySaveResult(history_id=history.id).model_dump())


@router.get("/history", response_model=ApiResponse)
def list_history(
    session_id: str = Query(..., min_length=8, max_length=64),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base = db.query(FormatReviewHistory).filter(FormatReviewHistory.user_id == current_user.id, FormatReviewHistory.session_key == session_id)
    if q:
        base = base.filter((FormatReviewHistory.paper_title.ilike(f"%{q}%")) | (FormatReviewHistory.filename.ilike(f"%{q}%")))
    total = int(base.count())
    rows = (
        base.order_by(FormatReviewHistory.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [
        {
            "history_id": r.id,
            "session_id": r.session_key,
            "paper_title": r.paper_title,
            "filename": r.filename,
            "status": r.status,
            "duration_ms": r.duration_ms,
            "issues_count": r.issues_count,
            "created_at": r.created_at,
        }
        for r in rows
    ]
    return ok(FormatReviewHistoryList(total=total, items=items).model_dump())


@router.delete("/history/{history_id}", response_model=ApiResponse)
def delete_history(history_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    row = db.query(FormatReviewHistory).filter(FormatReviewHistory.id == history_id, FormatReviewHistory.user_id == current_user.id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="history not found")
    db.delete(row)
    db.commit()
    return ok({"deleted": True})


def _enqueue_format_review_fix_task(task_id: str):
    if getattr(settings, "CELERY_RUN_INLINE", False):
        try:
            threading.Thread(target=format_review_auto_fix, args=(task_id,), daemon=True).start()
        except Exception:
            pass
        return
    try:
        format_review_auto_fix.delay(task_id)
    except Exception:
        pass


@router.post("/auto-fix", response_model=ApiResponse)
def auto_fix(
    payload: FormatReviewAutoFixRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not getattr(settings, "FORMAT_AUTOFIX_ENABLED", True):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="auto-fix disabled")
    row = db.query(FormatReviewHistory).filter(FormatReviewHistory.id == payload.history_id, FormatReviewHistory.user_id == current_user.id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="history not found")
    if not row.issues_count or int(row.issues_count) <= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="no issues to fix")

    t = FormatReviewFixTask(user_id=current_user.id, history_id=row.id, status="queued", progress=0)
    db.add(t)
    db.commit()
    db.refresh(t)
    background_tasks.add_task(_enqueue_format_review_fix_task, str(t.id))
    return ok(FormatReviewAutoFixResult(fix_task_id=t.id).model_dump())


@router.get("/auto-fix/{fix_task_id}", response_model=ApiResponse)
def get_fix_task(fix_task_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(FormatReviewFixTask).filter(FormatReviewFixTask.id == fix_task_id, FormatReviewFixTask.user_id == current_user.id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="fix task not found")

    download_url = None
    if t.status == "done" and t.result_path:
        token = (
            db.query(DownloadToken)
            .filter(DownloadToken.user_id == current_user.id, DownloadToken.path == t.result_path, DownloadToken.used == 0)
            .order_by(DownloadToken.created_at.desc())
            .first()
        )
        if token and token.expires_at > datetime.utcnow():
            download_url = f"/api/format-review/download/{token.token}"

    res = FormatReviewFixTaskResult(
        fix_task_id=t.id,
        status=t.status,
        progress=t.progress,
        download_url=download_url,
        expires_at=t.expires_at,
        error=t.error,
    )
    return ok(res.model_dump())


@router.get("/download/{token}")
def download(token: str, db: Session = Depends(get_db)):
    row = db.query(DownloadToken).filter(DownloadToken.token == token).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="download token not found")
    if row.used:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="download token already used")
    if row.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="download token expired")
    path = row.path
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="file not found")
    row.used = 1
    db.commit()
    return FileResponse(path, filename=os.path.basename(path))
