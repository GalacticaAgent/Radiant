import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict
from uuid import UUID

from celery import shared_task

from app.core.config import settings
from app.db.postgres import SessionLocal
from app.models.format_review import DownloadToken, FormatReviewFixTask, FormatReviewHistory, FormatReviewTask, FormatReviewUpload
from app.models.format_rule import FormatRuleVersion
from app.utils.doc_convert import convert_doc_bytes_to_docx_bytes
from app.utils.docx_fix import apply_docx_fixes

import json
from zipfile import ZipFile, ZIP_DEFLATED


@shared_task(name="format_review_auto_fix")
def format_review_auto_fix(fix_task_id: str) -> Dict[str, Any]:
    tid = UUID(fix_task_id)
    with SessionLocal() as db:
        task = db.query(FormatReviewFixTask).filter(FormatReviewFixTask.id == tid).first()
        if not task:
            return {"status": "not_found"}
        history = db.query(FormatReviewHistory).filter(FormatReviewHistory.id == task.history_id).first()
        if not history:
            task.status = "failed"
            task.error = "history not found"
            db.commit()
            return {"status": "failed"}

        if not getattr(settings, "FORMAT_AUTOFIX_ENABLED", True):
            task.status = "failed"
            task.error = "auto-fix disabled"
            db.commit()
            return {"status": "failed"}

        task.status = "running"
        task.progress = 10
        db.commit()

        try:
            review_task = None
            if history.task_id:
                review_task = (
                    db.query(FormatReviewTask)
                    .filter(FormatReviewTask.id == history.task_id, FormatReviewTask.user_id == task.user_id)
                    .first()
                )
            if not review_task or not review_task.upload_id:
                raise ValueError("missing review task/upload reference")
            upload = (
                db.query(FormatReviewUpload)
                .filter(FormatReviewUpload.id == review_task.upload_id, FormatReviewUpload.user_id == task.user_id)
                .first()
            )
            if not upload or upload.status != "ready" or not upload.storage_path:
                raise ValueError("upload not ready")
            path = upload.storage_path
            if not os.path.exists(path):
                raise ValueError("uploaded file not found")

            raw = open(path, "rb").read()
            orig_filename = upload.filename or history.filename or "paper"
            ext = os.path.splitext(orig_filename)[1].lower()

            rule_content = None
            if review_task.rule_id:
                v = (
                    db.query(FormatRuleVersion)
                    .filter(FormatRuleVersion.rule_id == review_task.rule_id)
                    .order_by(FormatRuleVersion.version.desc())
                    .first()
                )
                if v and isinstance(v.content, dict):
                    rule_content = v.content

            style_targets: Dict[str, Dict[str, Any]] = {
                "Normal": {"font": "宋体", "size_pt": 10.5, "line_spacing_pt": 20.0},
            }
            ensure_page_numbers = True
            if isinstance(rule_content, dict):
                exec_rules = rule_content.get("executable_rules") if isinstance(rule_content.get("executable_rules"), list) else []
                for r in exec_rules or []:
                    if not isinstance(r, dict):
                        continue
                    check_type = str(r.get("check_type") or "").strip()
                    params = r.get("params") if isinstance(r.get("params"), dict) else {}
                    if check_type == "docx_normal_font_contains":
                        contains = str(params.get("contains") or "").strip()
                        if contains:
                            style_targets.setdefault("Normal", {})["font"] = contains
                    elif check_type == "docx_normal_size_pt":
                        v = params.get("value")
                        try:
                            fv = float(v)
                            if fv > 0:
                                style_targets.setdefault("Normal", {})["size_pt"] = fv
                        except Exception:
                            pass
                    elif check_type == "docx_normal_line_spacing_pt":
                        v = params.get("value")
                        try:
                            fv = float(v)
                            if fv > 0:
                                style_targets.setdefault("Normal", {})["line_spacing_pt"] = fv
                        except Exception:
                            pass
                    elif check_type == "docx_require_page_number":
                        ensure_page_numbers = True

            root = Path(settings.UPLOAD_DIR).resolve() / "format_review_fix" / str(task.id)
            root.mkdir(parents=True, exist_ok=True)
            safe_name = str(orig_filename).replace("/", "_").replace("\\", "_")
            base = os.path.splitext(safe_name)[0] or "paper"
            out_zip = root / f"fixed_{base}.zip"

            report_md = history.report_markdown or ""
            changes: Dict[str, Any] = {"changes": [], "skipped": [], "notes": []}

            with ZipFile(out_zip, mode="w", compression=ZIP_DEFLATED) as z:
                if ext in (".docx", ".doc"):
                    task.progress = 30
                    db.commit()
                    if ext == ".doc":
                        docx_bytes = convert_doc_bytes_to_docx_bytes(raw)
                    else:
                        docx_bytes = raw
                    fixed_docx, fix_result = apply_docx_fixes(
                        docx_bytes,
                        style_targets=style_targets,
                        ensure_page_numbers=ensure_page_numbers,
                    )
                    z.writestr(f"fixed_{base}.docx", fixed_docx)
                    changes.update(fix_result if isinstance(fix_result, dict) else {})
                    changes["notes"].append("Only deterministic DOCX style fixes are applied.")
                elif ext == ".pdf":
                    changes["notes"].append("PDF cannot be edited reliably; package contains suggestions only.")
                    z.writestr(f"original_{base}.pdf", raw)
                else:
                    raise ValueError("unsupported file type")

                z.writestr("report.md", report_md.encode("utf-8"))
                z.writestr("changes.json", json.dumps(changes, ensure_ascii=False, indent=2).encode("utf-8"))

            out_path = out_zip

            token = secrets.token_urlsafe(24)[:48]
            expires = datetime.utcnow() + timedelta(days=7)
            dl = DownloadToken(user_id=task.user_id, token=token, path=str(out_path), expires_at=expires, used=0)
            db.add(dl)
            db.commit()
            db.refresh(dl)

            task.status = "done"
            task.progress = 100
            task.result_path = str(out_path)
            task.expires_at = expires
            db.commit()
            return {"status": "success", "token": token}
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.progress = 100
            db.commit()
            return {"status": "failed", "error": str(e)}
