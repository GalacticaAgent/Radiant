import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.common.response import ok
from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.format_review import FormatReviewSession, FormatReviewUpload
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.upload import UploadCompleteResult, UploadInitRequest, UploadInitResult, UploadStatusResult

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


def _detect_ext(head: bytes) -> str:
    if head.startswith(b"%PDF-"):
        return ".pdf"
    if head.startswith(b"PK\x03\x04"):
        return ".docx"
    if head.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return ".doc"
    return ""


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


def _upload_root(upload_id: UUID) -> Path:
    return Path(settings.UPLOAD_DIR).resolve() / "format_review" / str(upload_id)


def _parts_dir(upload_id: UUID) -> Path:
    return _upload_root(upload_id) / "parts"


def _existing_part_numbers(upload_id: UUID) -> List[int]:
    d = _parts_dir(upload_id)
    if not d.exists():
        return []
    out: List[int] = []
    for p in d.glob("part_*.bin"):
        m = re.match(r"part_(\d+)\.bin$", p.name)
        if not m:
            continue
        try:
            out.append(int(m.group(1)))
        except Exception:
            continue
    return sorted(set(out))


@router.post("/init", response_model=ApiResponse)
def init_upload(payload: UploadInitRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    filename = _safe_filename(payload.filename)
    ext = _ext(filename)
    if not ext:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported file type")
    if payload.size > int(getattr(settings, "MAX_UPLOAD_SIZE", 50 * 1024 * 1024)):
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="file too large")

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
            session = (
                db.query(FormatReviewSession)
                .filter(FormatReviewSession.user_id == current_user.id, FormatReviewSession.session_key == payload.session_id)
                .first()
            )

    chunk_size = 5 * 1024 * 1024
    expected_parts = (int(payload.size) + chunk_size - 1) // chunk_size
    upload = FormatReviewUpload(
        user_id=current_user.id,
        session_key=payload.session_id,
        filename=filename,
        mime_type=payload.mime_type,
        size=payload.size,
        chunk_size=chunk_size,
        status="uploading",
        uploaded_parts=[],
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    _parts_dir(upload.id).mkdir(parents=True, exist_ok=True)
    return ok(UploadInitResult(upload_id=upload.id, chunk_size=chunk_size, expected_parts=int(expected_parts)).model_dump())


@router.get("/{upload_id}/status", response_model=ApiResponse)
def get_upload_status(upload_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    upload = db.query(FormatReviewUpload).filter(FormatReviewUpload.id == upload_id, FormatReviewUpload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="upload not found")
    parts = upload.uploaded_parts if isinstance(upload.uploaded_parts, list) else []
    parts_int = sorted({int(x) for x in parts if isinstance(x, (int, float, str)) and str(x).isdigit()})
    total_size = int(upload.size or 0)
    chunk_size = int(upload.chunk_size or 0)
    expected_parts = (total_size + chunk_size - 1) // chunk_size if total_size > 0 and chunk_size > 0 else 0
    file_parts = _existing_part_numbers(upload.id)
    received = set(parts_int) | set(file_parts)
    parts_int = sorted(received)
    missing = [i for i in range(1, expected_parts + 1) if i not in received]
    return ok(
        UploadStatusResult(
            upload_id=upload.id,
            status=upload.status,
            uploaded_parts=parts_int,
            chunk_size=chunk_size,
            size=total_size,
            expected_parts=int(expected_parts),
            missing_parts=missing[:200],
        ).model_dump()
    )


@router.put("/{upload_id}/part", response_model=ApiResponse)
async def upload_part(
    upload_id: UUID,
    request: Request,
    part_number: int = Query(..., ge=1, le=10000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = db.query(FormatReviewUpload).filter(FormatReviewUpload.id == upload_id, FormatReviewUpload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="upload not found")
    if upload.status not in ("uploading", "uploaded"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="upload not writable")

    body = await request.body()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty part")
    if len(body) > int(upload.chunk_size):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="part too large")

    part_path = _parts_dir(upload.id) / f"part_{part_number:06d}.bin"
    part_path.parent.mkdir(parents=True, exist_ok=True)
    part_path.write_bytes(body)

    parts = upload.uploaded_parts if isinstance(upload.uploaded_parts, list) else []
    if part_number not in parts:
        parts.append(part_number)
    upload.uploaded_parts = parts
    total_size = int(upload.size or 0)
    chunk_size = int(upload.chunk_size or 0)
    expected_parts = (total_size + chunk_size - 1) // chunk_size if total_size > 0 and chunk_size > 0 else 0
    file_parts = _existing_part_numbers(upload.id)
    upload.status = "uploaded" if expected_parts and len(file_parts) >= expected_parts else "uploading"
    db.commit()
    return ok({"received": True, "part_number": part_number})


@router.post("/{upload_id}/complete", response_model=ApiResponse)
def complete_upload(upload_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    upload = db.query(FormatReviewUpload).filter(FormatReviewUpload.id == upload_id, FormatReviewUpload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="upload not found")

    filename = upload.filename
    ext = _ext(filename)
    if not ext:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported file type")

    total_size = int(upload.size)
    chunk_size = int(upload.chunk_size)
    expected_parts = (total_size + chunk_size - 1) // chunk_size
    file_parts = _existing_part_numbers(upload.id)
    parts = upload.uploaded_parts if isinstance(upload.uploaded_parts, list) else []
    parts_int = sorted({int(x) for x in parts if isinstance(x, (int, float, str)) and str(x).isdigit()})
    parts_int = sorted(set(parts_int) | set(file_parts))
    if len(parts_int) < expected_parts:
        received = set(parts_int)
        missing = [i for i in range(1, expected_parts + 1) if i not in received]
        hint = f"missing parts ({len(parts_int)}/{expected_parts})"
        if missing:
            hint += f": {missing[:20]}"
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=hint)

    root = _upload_root(upload.id)
    root.mkdir(parents=True, exist_ok=True)
    final_filename = filename
    part1_path = _parts_dir(upload.id) / "part_000001.bin"
    if part1_path.exists():
        try:
            head_from_part = part1_path.read_bytes()[:16]
            detected = _detect_ext(head_from_part)
            if detected and detected != ext:
                base = os.path.splitext(filename)[0] or filename
                final_filename = _safe_filename(f"{base}{detected}")
                ext = detected
        except Exception:
            pass
    final_path = root / final_filename

    h = hashlib.sha256()
    written = 0
    head = b""
    with final_path.open("wb") as out:
        for i in range(1, expected_parts + 1):
            part_path = _parts_dir(upload.id) / f"part_{i:06d}.bin"
            if not part_path.exists():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"missing part file: {i}")
            data = part_path.read_bytes()
            if i == 1:
                head = data[:16]
            out.write(data)
            h.update(data)
            written += len(data)

    if written != total_size:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="size mismatch")
    if not _magic_ok(ext, head):
        detected = _detect_ext(head)
        if detected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"file header mismatch (expected {ext}, detected {detected})",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"file header mismatch (expected {ext})")

    sniff = final_path.read_bytes()[:512 * 1024]
    sensitive_reason = _scan_sensitive(sniff)
    if sensitive_reason:
        upload.status = "blocked"
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"sensitive content: {sensitive_reason}")

    virus_reason = _virus_scan(final_path)
    if virus_reason:
        upload.status = "blocked"
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"virus scan failed: {virus_reason}")

    upload.sha256 = h.hexdigest()
    upload.storage_path = str(final_path)
    if final_filename != upload.filename:
        upload.filename = final_filename
    upload.status = "ready"
    upload.uploaded_parts = list(range(1, expected_parts + 1))
    db.commit()

    return ok(UploadCompleteResult(upload_id=upload.id, status=upload.status).model_dump())
