import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from uuid import UUID

from celery import shared_task

from app.db.postgres import SessionLocal
from app.db.redis import redis_client
from app.models.format_rule import FormatRule, FormatRuleFile, FormatRuleVersion
from app.services.llm_service import llm_service
from app.services.paper_service import PaperService
from app.utils.format_review_skill import SKILL_DESCRIPTION_FIXED, make_default_skill_name, render_skill_markdown


def _task_key(task_id: UUID) -> str:
    return f"format_rule:task:{task_id}"


@shared_task(name="format_rule_generate")
def format_rule_generate(task_id: str, file_id: str) -> Dict[str, Any]:
    tid = UUID(task_id)
    fid = UUID(file_id)
    redis_client.set_json(_task_key(tid), {"status": "running"}, ex=86400)
    with SessionLocal() as db:
        f = db.query(FormatRuleFile).filter(FormatRuleFile.id == fid).first()
        if not f:
            redis_client.set_json(_task_key(tid), {"status": "failed", "error": "file not found"}, ex=86400)
            return {"status": "failed"}

        try:
            path = Path(str(f.storage_path or "")).resolve()
            if not path.exists():
                raise FileNotFoundError("storage file not found")
            raw = path.read_bytes()

            ext = Path(f.filename).suffix.lower()
            extracted_text = ""
            docx_style_snapshot = None
            if ext == ".pdf":
                extracted_text = PaperService.extract_text_from_pdf(raw)
            elif ext == ".docx":
                extracted_text = PaperService.extract_text_from_docx(raw)
                try:
                    docx_style_snapshot = PaperService.extract_docx_style_snapshot(raw)
                except Exception:
                    docx_style_snapshot = None
            elif ext == ".doc":
                extracted_text = PaperService.extract_text_from_doc(raw)
                try:
                    docx_style_snapshot = PaperService.extract_doc_style_snapshot(raw)
                except Exception:
                    docx_style_snapshot = None
            else:
                raise ValueError("unsupported file type")

            f.status = "generating"
            f.error = None
            db.commit()

            meta = PaperService.extract_metadata(extracted_text or "")
            base_name = str((meta or {}).get("auto_extracted_title") or Path(f.filename).stem or "格式规则").strip()
            name = base_name[:30] if base_name else "格式规则"
            existing = db.query(FormatRule).filter(FormatRule.user_id == f.user_id, FormatRule.name == name).first()
            if existing:
                name = (name[:26] + "-" + task_id[:3])[:30]

            gen = llm_service.generate_format_rule(
                source_filename=f.filename,
                extracted_text=extracted_text,
                docx_style_snapshot=docx_style_snapshot,
                language="auto",
            )

            content = {
                "name": gen.get("name") or name,
                "summary": gen.get("summary"),
                "mode": gen.get("mode") or "augment",
                "source_file": f.filename,
                "generated_at": datetime.utcnow().isoformat(),
                "docx_style_snapshot": docx_style_snapshot,
                "executable_rules": gen.get("executable_rules") or [],
                "llm_rules": gen.get("llm_rules") or [],
            }

            if not content["executable_rules"] and not content["llm_rules"]:
                normal = ((docx_style_snapshot or {}).get("styles") or {}).get("Normal") if isinstance(docx_style_snapshot, dict) else None
                exec_rules = []
                if isinstance(normal, dict):
                    size = normal.get("size_pt")
                    line = normal.get("line_spacing_pt")
                    font = normal.get("font")
                    if font:
                        exec_rules.append(
                            {
                                "id": "body_font",
                                "severity": "major",
                                "check_type": "docx_normal_font_contains",
                                "params": {"contains": str(font)},
                                "description": "正文统一使用相同字体（以模板/规则文档为准）。",
                                "suggestion": "将正文样式统一为学院/模板要求的字体，并应用到全文。",
                            }
                        )
                    if size is not None:
                        exec_rules.append(
                            {
                                "id": "body_font_size",
                                "severity": "major",
                                "check_type": "docx_normal_size_pt",
                                "params": {"value": float(size), "tolerance": 0.2},
                                "description": "正文字号需统一并符合模板要求。",
                                "suggestion": "按模板将正文字号设置为指定值（如五号 10.5pt），并应用到全文。",
                            }
                        )
                    if line is not None:
                        exec_rules.append(
                            {
                                "id": "body_line_spacing",
                                "severity": "major",
                                "check_type": "docx_normal_line_spacing_pt",
                                "params": {"value": float(line), "tolerance": 0.5},
                                "description": "正文行距需统一并符合模板要求。",
                                "suggestion": "按模板将正文行距设置为指定值（如固定 20 磅），并统一段前段后。",
                            }
                        )
                llm_rules = [
                    [
                        {
                            "id": "citations",
                            "severity": "major",
                            "description": "正文引用标注需统一格式，并与参考文献编号一致。",
                            "check_method": "基于文本：检查是否存在一致的引用标注模式（如 [1]）。",
                            "suggestion": "统一引用标注格式，并核对参考文献编号与正文引用一一对应。",
                        },
                        {
                            "id": "references",
                            "severity": "major",
                            "description": "参考文献需按统一著录规则排版，并满足数量/外文比例等要求。",
                            "check_method": "基于文本：定位参考文献章节并检查条目结构与编号。",
                            "suggestion": "按模板/学校规范整理参考文献格式，补齐缺失条目并统一标点与作者格式。",
                        },
                    ]
                ][0]
                content["executable_rules"] = exec_rules[:25]
                content["llm_rules"] = llm_rules[:25]

            skill_name = make_default_skill_name(source_filename=f.filename, rule_display_name=str(content.get("name") or name))
            content["skill"] = {
                "name": skill_name,
                "description": SKILL_DESCRIPTION_FIXED,
                "markdown": render_skill_markdown(skill_name=skill_name, description=SKILL_DESCRIPTION_FIXED, rule_content=content),
            }

            rule = FormatRule(user_id=f.user_id, name=str(content.get("name") or name)[:30], pinned=False)
            db.add(rule)
            db.commit()
            db.refresh(rule)

            v = FormatRuleVersion(rule_id=rule.id, version=1, content=content)
            db.add(v)
            f.status = "done"
            db.commit()

            redis_client.set_json(_task_key(tid), {"status": "done", "rule_id": str(rule.id)}, ex=86400)
            return {"status": "success", "rule_id": str(rule.id)}
        except Exception as e:
            try:
                f.status = "failed"
                f.error = str(e)[:500]
                db.commit()
            except Exception:
                pass
            redis_client.set_json(_task_key(tid), {"status": "failed", "error": str(e)}, ex=86400)
            return {"status": "failed", "error": str(e)}
