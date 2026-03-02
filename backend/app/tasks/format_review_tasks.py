import json
import os
import time
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from celery import shared_task

from app.db.postgres import SessionLocal
from app.db.redis import redis_client
from app.models.format_review import FormatReviewTask, FormatReviewUpload
from app.models.format_rule import FormatRuleVersion
from app.services.llm_service import llm_service
from app.services.paper_service import PaperService


def _progress_key(task_id: UUID) -> str:
    return f"format_review:task:{task_id}"


@shared_task(name="format_review_run")
def format_review_run(task_id: str) -> Dict[str, Any]:
    tid = UUID(task_id)
    with SessionLocal() as db:
        task = db.query(FormatReviewTask).filter(FormatReviewTask.id == tid).first()
        if not task:
            return {"status": "not_found"}

        def set_progress(p: int, status_text: str = "running", extra: Dict[str, Any] | None = None):
            task.status = status_text
            task.progress = int(p)
            db.commit()
            payload = {"status": task.status, "progress": task.progress}
            if extra:
                payload.update(extra)
            redis_client.set_json(_progress_key(tid), payload, ex=86400)

        try:
            task.status = "running"
            task.started_at = datetime.utcnow()
            task.progress = 3
            db.commit()
            redis_client.set_json(_progress_key(tid), {"status": task.status, "progress": task.progress}, ex=86400)

            meta = (task.result or {}).get("meta") if isinstance(task.result, dict) else {}
            paper_title = str((meta or {}).get("paper_title") or "").strip()
            filename = str((meta or {}).get("filename") or "").strip()

            upload = None
            if task.upload_id:
                upload = (
                    db.query(FormatReviewUpload)
                    .filter(FormatReviewUpload.id == task.upload_id, FormatReviewUpload.user_id == task.user_id)
                    .first()
                )
                if not upload or upload.status != "ready" or not upload.storage_path:
                    raise ValueError("upload not ready")

            if not upload:
                raise ValueError("missing upload")

            set_progress(10)
            path = upload.storage_path
            if not os.path.exists(path):
                raise ValueError("uploaded file not found")

            raw = open(path, "rb").read()
            ext = os.path.splitext(upload.filename or filename or "")[1].lower()
            if ext not in (".pdf", ".docx", ".doc"):
                raise ValueError("unsupported file type")

            set_progress(25)
            docx_style_snapshot = None
            source_type = "text"
            if ext == ".pdf":
                full_text = PaperService.extract_text_from_pdf(raw)
                source_type = "pdf"
            elif ext == ".docx":
                full_text = PaperService.extract_text_from_docx(raw)
                source_type = "docx"
                try:
                    docx_style_snapshot = PaperService.extract_docx_style_snapshot(raw)
                except Exception:
                    docx_style_snapshot = None
            else:
                full_text = PaperService.extract_text_from_doc(raw)
                source_type = "docx"
                try:
                    docx_style_snapshot = PaperService.extract_doc_style_snapshot(raw)
                except Exception:
                    docx_style_snapshot = None

            set_progress(40)
            md = PaperService.extract_metadata(full_text)
            abstract = str(md.get("auto_extracted_abstract") or "") if isinstance(md, dict) else ""
            if not paper_title:
                paper_title = str(md.get("auto_extracted_title") or "") if isinstance(md, dict) else ""
            if not paper_title:
                paper_title = upload.filename or filename or "Untitled"

            full_text = (full_text or "").strip()
            excerpt = full_text[:12000]
            abstract = (abstract or "").strip()[:2000]

            custom_rule_text = None
            custom_rule_content = None
            rule_meta = {"using_default_rule": True, "rule_id": None, "rule_name": None, "rule_version": None, "rule_mode": None}
            if task.rule_id:
                rule_meta["using_default_rule"] = False
                rule_meta["rule_id"] = str(task.rule_id)
                v = (
                    db.query(FormatRuleVersion)
                    .filter(FormatRuleVersion.rule_id == task.rule_id)
                    .order_by(FormatRuleVersion.version.desc())
                    .first()
                )
                if v and v.content is not None:
                    if isinstance(v.content, dict):
                        custom_rule_content = v.content
                        rule_meta["rule_version"] = int(v.version)
                        rule_meta["rule_name"] = str(custom_rule_content.get("name") or "") or None
                        rule_meta["rule_mode"] = str(custom_rule_content.get("mode") or "") or None
                    else:
                        try:
                            custom_rule_text = json.dumps(v.content, ensure_ascii=False)
                        except Exception:
                            custom_rule_text = str(v.content)

            set_progress(65)
            try:
                data = llm_service.generate_format_review(
                    paper_title=paper_title,
                    abstract=abstract,
                    paper_content=excerpt,
                    paper_language="auto",
                    full_text=full_text,
                    source_type=source_type,
                    docx_style_snapshot=docx_style_snapshot,
                    custom_rule_text=custom_rule_text,
                    custom_rule_content=custom_rule_content,
                )
            except Exception as e:
                from app.services.format_rule_engine import FormatRuleEngine

                rule_result = FormatRuleEngine.analyze(
                    paper_title=paper_title,
                    abstract=abstract,
                    paper_content=excerpt,
                    full_text=full_text,
                    source_type=source_type,
                    docx_style_snapshot=docx_style_snapshot,
                    custom_rule_content=custom_rule_content,
                )
                rule_issues = rule_result.get("rule_issues") if isinstance(rule_result, dict) else []
                auto_metrics = rule_result.get("auto_metrics") if isinstance(rule_result, dict) else {}
                data = {
                    "review_markdown": "### 格式审查结果（规则引擎）\n\n- LLM 不可用或调用失败，已返回规则引擎检测结果。\n",
                    "issues": rule_issues if isinstance(rule_issues, list) else [],
                    "rule_issues": rule_issues if isinstance(rule_issues, list) else [],
                    "llm_issues": [],
                    "auto_metrics": auto_metrics if isinstance(auto_metrics, dict) else {},
                    "overall_grade": "需要改进",
                    "priority": "中",
                    "summary": f"LLM 调用失败：{str(e)}",
                }

            review_markdown = str(data.get("review_markdown") or "")
            issues = data.get("issues") if isinstance(data.get("issues"), list) else []
            result = {
                "meta": {"paper_title": paper_title, "filename": upload.filename or filename, **rule_meta},
                "markdown": review_markdown,
                "issues": issues,
                "rule_issues": data.get("rule_issues") if isinstance(data.get("rule_issues"), list) else [],
                "llm_issues": data.get("llm_issues") if isinstance(data.get("llm_issues"), list) else [],
                "auto_metrics": data.get("auto_metrics") if isinstance(data.get("auto_metrics"), dict) else {},
                "overall_grade": data.get("overall_grade"),
                "priority": data.get("priority"),
                "summary": data.get("summary"),
                "generated_at": datetime.utcnow().isoformat(),
            }

            task.result = result
            task.ended_at = datetime.utcnow()
            task.duration_ms = int((task.ended_at - task.started_at).total_seconds() * 1000) if task.started_at else None
            set_progress(100, "done", {"duration_ms": task.duration_ms})
            task.status = "done"
            task.progress = 100
            db.commit()
            return {"status": "success", "task_id": task_id}
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.ended_at = datetime.utcnow()
            task.duration_ms = int((task.ended_at - task.started_at).total_seconds() * 1000) if task.started_at else None
            db.commit()
            redis_client.set_json(
                _progress_key(tid),
                {"status": task.status, "progress": int(task.progress or 0), "error": task.error, "duration_ms": task.duration_ms},
                ex=86400,
            )
            return {"status": "failed", "task_id": task_id, "error": task.error}
