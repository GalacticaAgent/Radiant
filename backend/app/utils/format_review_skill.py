import re
from typing import Any, Dict, List, Optional
from uuid import uuid4


SKILL_DESCRIPTION_FIXED = (
    "按学术写作规范与格式要求对论文进行格式审核，查找格式错误并提供具体修改意见。"
    "用户在选择审查规则窗口选定后请求格式审查、格式检查或格式优化时调用。"
)


_SKILL_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{2,63}$")


def is_valid_skill_name(name: str) -> bool:
    return bool(_SKILL_NAME_RE.match((name or "").strip()))


def _slugify_ascii(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", (text or "").strip()).strip("-").lower()
    s = re.sub(r"-{2,}", "-", s)
    return s


def make_default_skill_name(*, source_filename: str, rule_display_name: Optional[str] = None) -> str:
    base = _slugify_ascii(rule_display_name or "")
    if not base:
        base = _slugify_ascii(source_filename)
    if base:
        base = base[:40].strip("-")
    if not base or not re.match(r"^[a-z]", base):
        base = "rule"
    candidate = f"{base}-{uuid4().hex[:8]}"
    candidate = candidate[:63]
    if is_valid_skill_name(candidate):
        return candidate
    return f"rule-{uuid4().hex[:8]}"


def render_skill_markdown(*, skill_name: str, description: str, rule_content: Dict[str, Any]) -> str:
    name = (skill_name or "").strip()
    if not is_valid_skill_name(name):
        name = make_default_skill_name(
            source_filename=str((rule_content or {}).get("source_file") or ""),
            rule_display_name=str((rule_content or {}).get("name") or ""),
        )

    desc = (description or "").strip() or SKILL_DESCRIPTION_FIXED
    summary = str((rule_content or {}).get("summary") or "").strip()
    exec_rules = (rule_content or {}).get("executable_rules")
    llm_rules = (rule_content or {}).get("llm_rules")
    exec_rules = exec_rules if isinstance(exec_rules, list) else []
    llm_rules = llm_rules if isinstance(llm_rules, list) else []

    def fmt_exec(items: List[Dict[str, Any]]) -> str:
        out: List[str] = []
        for it in items[:30]:
            if not isinstance(it, dict):
                continue
            ct = str(it.get("check_type") or "").strip()
            desc2 = str(it.get("description") or "").strip()
            sug = str(it.get("suggestion") or "").strip()
            if not ct or not desc2:
                continue
            line = f"- [{ct}] {desc2}"
            if sug:
                line += f"（建议：{sug}）"
            out.append(line)
        return "\n".join(out) if out else "- （无）"

    def fmt_llm(items: List[Dict[str, Any]]) -> str:
        out: List[str] = []
        for it in items[:30]:
            if not isinstance(it, dict):
                continue
            desc2 = str(it.get("description") or "").strip()
            cm = str(it.get("check_method") or "").strip()
            sug = str(it.get("suggestion") or "").strip()
            if not desc2:
                continue
            line = f"- {desc2}"
            if cm:
                line += f"（检查提示：{cm}）"
            if sug:
                line += f"（建议：{sug}）"
            out.append(line)
        return "\n".join(out) if out else "- （无）"

    blocks: List[str] = []
    blocks.append("---")
    blocks.append(f'name: \"{name}\"')
    blocks.append(f'description: \"{desc}\"')
    blocks.append("---")
    blocks.append("")
    blocks.append("# 论文格式审查技能")
    if summary:
        blocks.append("")
        blocks.append("## 规则概况")
        blocks.append(summary)
    blocks.append("")
    blocks.append("## 使用时机")
    blocks.append("- 审查学术论文格式规范")
    blocks.append("- 检查论文格式错误")
    blocks.append("- 提供格式优化建议")
    blocks.append("")
    blocks.append("## 输出结构（固定 8 部分）")
    blocks.append("### 1. 论文基本信息")
    blocks.append("### 2. 格式优点")
    blocks.append("### 3. 格式问题")
    blocks.append("### 4. 详细格式审查")
    blocks.append("### 5. 技术格式正确性")
    blocks.append("### 6. 一致性与规范性")
    blocks.append("### 7. 具体修改建议")
    blocks.append("### 8. 格式审查结论")
    blocks.append("")
    blocks.append("## 自动化检查（硬规则）")
    blocks.append(fmt_exec(exec_rules))
    blocks.append("")
    blocks.append("## LLM 辅助检查（软规则）")
    blocks.append(fmt_llm(llm_rules))
    blocks.append("")
    blocks.append("## 备注")
    blocks.append("- 本技能由用户上传规则文档生成，供后续格式审查任务选用。")
    return "\n".join(blocks).strip() + "\n"

