import hashlib
import os
import subprocess
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

import json
import threading
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.common.response import ok
from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.db.redis import redis_client
from app.models.format_review import FormatReviewTask
from app.models.format_rule import FormatRule, FormatRuleFile, FormatRuleVersion
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.rule import (
    RuleGenerateRequest,
    RuleGenerateResult,
    RuleItem,
    RuleListResult,
    RulePinRequest,
    RuleRenameRequest,
    RuleSkillRenameRequest,
    RuleRollbackRequest,
    RuleRollbackResult,
    RuleTaskResult,
    RuleUploadResult,
    RuleVersionListResult,
)
from app.tasks.rule_tasks import format_rule_generate
from app.utils.format_review_skill import SKILL_DESCRIPTION_FIXED, is_valid_skill_name, render_skill_markdown

router = APIRouter()


def _safe_filename(name: str) -> str:
    base = os.path.basename(name or "").strip()
    return base[:240] or "file"


def _ext(name: str) -> str:
    n = (name or "").lower()
    for e in (".pdf", ".docx", ".doc"):
        if n.endswith(e):
            return e
    return ""


def _magic_ok(ext: str, head: bytes) -> bool:
    if ext == ".pdf":
        return head.startswith(b"%PDF-")
    if ext == ".docx":
        return head.startswith(b"PK\x03\x04")
    if ext == ".doc":
        return head.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
    return False


def _scan_sensitive(raw: bytes) -> Optional[str]:
    upper = raw.upper()
    if b"BEGIN PRIVATE KEY" in upper:
        return "detected private key material"
    if b"AKIA" in upper and b"AWS" in upper:
        return "detected aws key pattern"
    return None


def _virus_scan(path: Path) -> Optional[str]:
    if not bool(getattr(settings, "VIRUS_SCAN_ENABLED", False)):
        return None
    cmd = str(getattr(settings, "CLAMAV_COMMAND", "clamscan") or "clamscan")
    try:
        p = subprocess.run([cmd, "--no-summary", str(path)], capture_output=True, text=True, timeout=120)
        if p.returncode == 0:
            return None
        if p.returncode == 1:
            return (p.stdout or p.stderr or "virus detected").strip()
        return (p.stderr or p.stdout or "virus scan error").strip()
    except Exception as e:
        return str(e)


def _task_key(task_id: UUID) -> str:
    return f"format_rule:task:{task_id}"


@router.post("/upload", response_model=ApiResponse)
async def upload_rule_file(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    filename = _safe_filename(file.filename or "")
    ext = _ext(filename)
    if not ext:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported file type")

    max_size = 20 * 1024 * 1024
    root = Path(settings.UPLOAD_DIR).resolve() / "format_rules"
    root.mkdir(parents=True, exist_ok=True)
    rid = uuid4()
    dest = root / str(rid)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / filename

    h = hashlib.sha256()
    written = 0
    head = b""
    with path.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            if written == 0:
                head = chunk[:16]
            written += len(chunk)
            if written > max_size:
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="file too large")
            out.write(chunk)
            h.update(chunk)

    if not _magic_ok(ext, head):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file header mismatch")

    sniff = path.read_bytes()[:512 * 1024]
    sensitive_reason = _scan_sensitive(sniff)
    if sensitive_reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"sensitive content: {sensitive_reason}")
    virus_reason = _virus_scan(path)
    if virus_reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"virus scan failed: {virus_reason}")

    rf = FormatRuleFile(
        id=rid,
        user_id=current_user.id,
        filename=filename,
        size=written,
        mime_type=file.content_type,
        sha256=h.hexdigest(),
        storage_path=str(path),
        status="uploaded",
    )
    db.add(rf)
    db.commit()
    return ok(RuleUploadResult(file_id=rf.id).model_dump())


def _enqueue_generate_rule_task(task_id: str, file_id: str):
    if getattr(settings, "CELERY_RUN_INLINE", False):
        try:
            threading.Thread(target=format_rule_generate, args=(task_id, file_id), daemon=True).start()
        except Exception as e:
            try:
                redis_client.set_json(_task_key(UUID(task_id)), {"status": "failed", "error": str(e)}, ex=86400)
            except Exception:
                pass
        return

    try:
        format_rule_generate.delay(task_id, file_id)
    except Exception as e:
        try:
            redis_client.set_json(_task_key(UUID(task_id)), {"status": "failed", "error": str(e)}, ex=86400)
        except Exception:
            pass


@router.post("/generate", response_model=ApiResponse)
def generate_rule(
    payload: RuleGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    f = db.query(FormatRuleFile).filter(FormatRuleFile.id == payload.file_id, FormatRuleFile.user_id == current_user.id).first()
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="file not found")
    task_id = uuid4()
    redis_client.set_json(_task_key(task_id), {"status": "queued"}, ex=86400)
    background_tasks.add_task(_enqueue_generate_rule_task, str(task_id), str(f.id))
    return ok(RuleGenerateResult(task_id=task_id).model_dump())


@router.get("/task/{task_id}", response_model=ApiResponse)
def get_rule_task(task_id: UUID, current_user: User = Depends(get_current_user)):
    data = redis_client.get_json(_task_key(task_id)) or {"status": "unknown"}
    return ok(RuleTaskResult(task_id=task_id, status=str(data.get("status") or "unknown"), rule_id=data.get("rule_id"), error=data.get("error")).model_dump())


@router.get("/my", response_model=ApiResponse)
def list_my_rules(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(FormatRule)
        .filter(FormatRule.user_id == current_user.id)
        .order_by(FormatRule.pinned.desc(), FormatRule.updated_at.desc())
        .all()
    )
    items = []
    for r in rows:
        v = (
            db.query(FormatRuleVersion)
            .filter(FormatRuleVersion.rule_id == r.id)
            .order_by(FormatRuleVersion.version.desc())
            .first()
        )
        items.append(RuleItem(rule_id=r.id, name=r.name, pinned=bool(r.pinned), version=int(v.version if v else 1), created_at=r.created_at))
    return ok(RuleListResult(items=items).model_dump())


@router.get("/{rule_id}", response_model=ApiResponse)
def get_rule(rule_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rule = db.query(FormatRule).filter(FormatRule.id == rule_id, FormatRule.user_id == current_user.id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")
    v = (
        db.query(FormatRuleVersion)
        .filter(FormatRuleVersion.rule_id == rule_id)
        .order_by(FormatRuleVersion.version.desc())
        .first()
    )
    return ok(
        {
            "rule_id": str(rule.id),
            "name": rule.name,
            "pinned": bool(rule.pinned),
            "version": int(v.version if v else 1),
            "content": v.content if v else None,
            "created_at": rule.created_at,
            "updated_at": rule.updated_at,
        }
    )


@router.get("/{rule_id}/version/{version}", response_model=ApiResponse)
def get_rule_version(rule_id: UUID, version: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rule = db.query(FormatRule).filter(FormatRule.id == rule_id, FormatRule.user_id == current_user.id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")
    v = db.query(FormatRuleVersion).filter(FormatRuleVersion.rule_id == rule_id, FormatRuleVersion.version == version).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="version not found")
    return ok({"rule_id": str(rule.id), "name": rule.name, "version": v.version, "content": v.content, "created_at": v.created_at})


@router.get("/{rule_id}/export")
def export_rule(
    rule_id: UUID,
    fmt: str = Query("json", pattern="^(json|skill_md)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = db.query(FormatRule).filter(FormatRule.id == rule_id, FormatRule.user_id == current_user.id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")
    v = (
        db.query(FormatRuleVersion)
        .filter(FormatRuleVersion.rule_id == rule_id)
        .order_by(FormatRuleVersion.version.desc())
        .first()
    )
    payload = {
        "rule_id": str(rule.id),
        "name": rule.name,
        "pinned": bool(rule.pinned),
        "version": int(v.version if v else 1),
        "content": v.content if v else None,
    }
    if fmt == "skill_md":
        content = payload.get("content") if isinstance(payload.get("content"), dict) else {}
        skill = content.get("skill") if isinstance(content, dict) else None
        skill_name = str((skill or {}).get("name") or "").strip()
        if not is_valid_skill_name(skill_name):
            skill_name = f"rule-{str(rule.id).replace('-', '')[:8]}"
        md = str((skill or {}).get("markdown") or "").strip()
        if not md:
            md = render_skill_markdown(skill_name=skill_name, description=SKILL_DESCRIPTION_FIXED, rule_content=content if isinstance(content, dict) else {})
        raw = (md.strip() + "\n").encode("utf-8")
        filename = f"{skill_name}.md"
        return Response(content=raw, media_type="text/markdown", headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    filename = f"format_rule_{rule.id}_v{payload['version']}.json"
    return Response(content=raw, media_type="application/json", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.put("/skill/rename", response_model=ApiResponse)
def rename_rule_skill(payload: RuleSkillRenameRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    skill_name = str(payload.skill_name or "").strip()
    if not is_valid_skill_name(skill_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid skill name")

    rule = db.query(FormatRule).filter(FormatRule.id == payload.rule_id, FormatRule.user_id == current_user.id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")

    latest = (
        db.query(FormatRuleVersion)
        .filter(FormatRuleVersion.rule_id == payload.rule_id)
        .order_by(FormatRuleVersion.version.desc())
        .first()
    )
    if not latest or not isinstance(latest.content, dict):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="rule content not found")

    content = dict(latest.content or {})
    cur_skill = content.get("skill") if isinstance(content.get("skill"), dict) else {}
    new_skill = dict(cur_skill or {})
    new_skill["name"] = skill_name
    new_skill["description"] = SKILL_DESCRIPTION_FIXED
    new_skill["markdown"] = render_skill_markdown(skill_name=skill_name, description=SKILL_DESCRIPTION_FIXED, rule_content=content)
    content["skill"] = new_skill

    next_ver = int(latest.version + 1)
    v = FormatRuleVersion(rule_id=payload.rule_id, version=next_ver, content=content)
    db.add(v)
    db.commit()

    extra_rows = (
        db.query(FormatRuleVersion.id)
        .filter(FormatRuleVersion.rule_id == payload.rule_id)
        .order_by(FormatRuleVersion.version.desc())
        .offset(5)
        .all()
    )
    extra_ids = [x[0] for x in extra_rows]
    if extra_ids:
        db.query(FormatRuleVersion).filter(FormatRuleVersion.id.in_(extra_ids)).delete(synchronize_session=False)
        db.commit()

    return ok({"rule_id": str(rule.id), "version": next_ver, "skill_name": skill_name})


@router.put("/rename", response_model=ApiResponse)
def rename_rule(payload: RuleRenameRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rule = db.query(FormatRule).filter(FormatRule.id == payload.rule_id, FormatRule.user_id == current_user.id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")
    exists = db.query(FormatRule).filter(FormatRule.user_id == current_user.id, FormatRule.name == payload.name, FormatRule.id != rule.id).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="rule name already exists")
    rule.name = payload.name
    db.commit()
    return ok({"renamed": True})


@router.put("/pin", response_model=ApiResponse)
def pin_rule(payload: RulePinRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rule = db.query(FormatRule).filter(FormatRule.id == payload.rule_id, FormatRule.user_id == current_user.id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")
    rule.pinned = bool(payload.pinned)
    db.commit()
    return ok({"pinned": rule.pinned})


@router.delete("/{rule_id}", response_model=ApiResponse)
def delete_rule(
    rule_id: UUID,
    force: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = db.query(FormatRule).filter(FormatRule.id == rule_id, FormatRule.user_id == current_user.id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")
    ref = db.query(FormatReviewTask).filter(FormatReviewTask.user_id == current_user.id, FormatReviewTask.rule_id == rule_id).count()
    if ref and not force:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="rule is referenced; use force=true to delete")
    db.query(FormatRuleVersion).filter(FormatRuleVersion.rule_id == rule_id).delete()
    db.delete(rule)
    db.commit()
    return ok({"deleted": True})


@router.get("/{rule_id}/versions", response_model=ApiResponse)
def list_versions(rule_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rule = db.query(FormatRule).filter(FormatRule.id == rule_id, FormatRule.user_id == current_user.id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")
    rows = (
        db.query(FormatRuleVersion)
        .filter(FormatRuleVersion.rule_id == rule_id)
        .order_by(FormatRuleVersion.version.desc())
        .limit(5)
        .all()
    )
    versions = [{"version": r.version, "created_at": r.created_at} for r in rows]
    return ok(RuleVersionListResult(rule_id=rule_id, versions=versions).model_dump())


@router.post("/{rule_id}/rollback", response_model=ApiResponse)
def rollback_rule(rule_id: UUID, payload: RuleRollbackRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rule = db.query(FormatRule).filter(FormatRule.id == rule_id, FormatRule.user_id == current_user.id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")
    target = db.query(FormatRuleVersion).filter(FormatRuleVersion.rule_id == rule_id, FormatRuleVersion.version == payload.version).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="version not found")
    latest = (
        db.query(FormatRuleVersion)
        .filter(FormatRuleVersion.rule_id == rule_id)
        .order_by(FormatRuleVersion.version.desc())
        .first()
    )
    next_ver = int(latest.version + 1 if latest else 1)
    v = FormatRuleVersion(rule_id=rule_id, version=next_ver, content=target.content)
    db.add(v)
    db.commit()
    extra_rows = (
        db.query(FormatRuleVersion.id)
        .filter(FormatRuleVersion.rule_id == rule_id)
        .order_by(FormatRuleVersion.version.desc())
        .offset(5)
        .all()
    )
    extra_ids = [x[0] for x in extra_rows]
    if extra_ids:
        db.query(FormatRuleVersion).filter(FormatRuleVersion.id.in_(extra_ids)).delete(synchronize_session=False)
        db.commit()
    return ok(RuleRollbackResult(rule_id=rule_id, version=next_ver).model_dump())
