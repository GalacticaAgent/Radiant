from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
import re


@dataclass(frozen=True)
class FormatIssueItem:
    severity: str
    position: str
    description: str
    suggestion: str
    evidence: Optional[str] = None

    def to_public_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if d.get("evidence") is None:
            d.pop("evidence", None)
        return d


class FormatRuleEngine:
    @staticmethod
    def _dedupe_issue_dicts(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: set[Tuple[str, str]] = set()
        out: List[Dict[str, Any]] = []
        for it in items or []:
            if not isinstance(it, dict):
                continue
            pos = str(it.get("position") or "").strip().lower()
            desc = str(it.get("description") or "").strip().lower()
            if not desc:
                continue
            key = (pos, desc)
            if key in seen:
                continue
            seen.add(key)
            out.append(it)
        return out

    @staticmethod
    def _safe_int(v: Any) -> Optional[int]:
        try:
            if v is None:
                return None
            if isinstance(v, bool):
                return None
            if isinstance(v, (int, float)):
                return int(v)
            s = str(v).strip()
            if not s:
                return None
            m = re.search(r"-?\d+", s)
            return int(m.group(0)) if m else None
        except Exception:
            return None

    @staticmethod
    def _safe_float(v: Any) -> Optional[float]:
        try:
            if v is None:
                return None
            if isinstance(v, bool):
                return None
            if isinstance(v, (int, float)):
                return float(v)
            s = str(v).strip()
            if not s:
                return None
            m = re.search(r"-?\d+(\.\d+)?", s)
            return float(m.group(0)) if m else None
        except Exception:
            return None

    @staticmethod
    def _apply_exec_rules(
        *,
        executable_rules: List[Dict[str, Any]],
        title: str,
        abs_text: str,
        full_text: str,
        main_text: str,
        ref_items: List[str],
        foreign_refs: int,
        section_flags: Dict[str, bool],
        keywords: Optional[List[str]],
        docx_style_snapshot: Optional[Dict[str, Any]],
        source_type: str,
    ) -> Tuple[List[FormatIssueItem], List[str]]:
        issues: List[FormatIssueItem] = []
        skipped: List[str] = []
        for r in executable_rules or []:
            if not isinstance(r, dict):
                continue
            check_type = str(r.get("check_type") or "").strip()
            sev = str(r.get("severity") or "major").strip() or "major"
            desc = str(r.get("description") or "").strip()
            sug = str(r.get("suggestion") or "").strip() or "请按规则要求修改。"
            params = r.get("params") if isinstance(r.get("params"), dict) else {}
            scope = str(r.get("scope") or "").strip()

            def add(position: str, detail: str, evidence: Optional[str] = None):
                issues.append(
                    FormatIssueItem(
                        severity=sev,
                        position=position,
                        description=detail,
                        suggestion=sug,
                        evidence=evidence,
                    )
                )

            if check_type == "title_cn_max_chars":
                mx = FormatRuleEngine._safe_int(params.get("max"))
                if mx is None:
                    skipped.append(check_type)
                    continue
                title_cn = FormatRuleEngine._count_cn(title)
                if title_cn > mx:
                    add("封面/标题", f"{desc}（当前约 {title_cn} 个中文字符，要求 ≤ {mx}）", title[:120])
                continue

            if check_type == "abstract_cn_range":
                mn = FormatRuleEngine._safe_int(params.get("min"))
                mx = FormatRuleEngine._safe_int(params.get("max"))
                abs_cn = FormatRuleEngine._count_cn(abs_text)
                if abs_cn <= 0 or mn is None or mx is None:
                    skipped.append(check_type)
                    continue
                if abs_cn < mn or abs_cn > mx:
                    add("中文摘要", f"{desc}（当前约 {abs_cn} 个中文字符，要求 {mn}–{mx}）")
                continue

            if check_type == "keywords_count_range":
                mn = FormatRuleEngine._safe_int(params.get("min"))
                mx = FormatRuleEngine._safe_int(params.get("max"))
                if mn is None or mx is None:
                    skipped.append(check_type)
                    continue
                if keywords is None:
                    add("中文摘要/关键词", f"{desc}（未识别到关键词）")
                    continue
                if len(keywords) < mn or len(keywords) > mx:
                    add("中文摘要/关键词", f"{desc}（当前 {len(keywords)} 个，要求 {mn}–{mx}）", "; ".join(keywords[:10]))
                continue

            if check_type == "require_toc":
                if not section_flags.get("目录", False):
                    add("目录", desc)
                continue

            if check_type == "require_references_section":
                if not section_flags.get("参考文献", False):
                    add("参考文献", desc)
                continue

            if check_type == "references_min_count":
                mn = FormatRuleEngine._safe_int(params.get("min"))
                if mn is None:
                    skipped.append(check_type)
                    continue
                if section_flags.get("参考文献", False) and len(ref_items) < mn:
                    add("参考文献", f"{desc}（当前估算 {len(ref_items)} 条，要求 ≥ {mn}）")
                continue

            if check_type == "foreign_references_min_count":
                mn = FormatRuleEngine._safe_int(params.get("min"))
                if mn is None:
                    skipped.append(check_type)
                    continue
                if section_flags.get("参考文献", False) and foreign_refs < mn:
                    add("参考文献", f"{desc}（当前估算 {foreign_refs} 条外文，要求 ≥ {mn}）")
                continue

            if check_type == "require_citation_markers":
                pattern = str(params.get("pattern") or r"\[\d+\]").strip() or r"\[\d+\]"
                try:
                    if not re.search(pattern, main_text, re.MULTILINE):
                        add("正文引用", desc)
                except Exception:
                    skipped.append(check_type)
                continue

            if check_type in ("docx_require_header", "docx_require_footer", "docx_require_page_number", "docx_normal_font_contains", "docx_normal_size_pt", "docx_normal_line_spacing_pt"):
                if source_type.lower() != "docx" or not isinstance(docx_style_snapshot, dict):
                    skipped.append(check_type)
                    continue
                hdr = docx_style_snapshot.get("has_header")
                ftr = docx_style_snapshot.get("has_footer")
                page_num = docx_style_snapshot.get("has_page_number")
                styles = docx_style_snapshot.get("styles") if isinstance(docx_style_snapshot, dict) else None
                normal = styles.get("Normal") if isinstance(styles, dict) else None

                if check_type == "docx_require_header":
                    if hdr is False:
                        add("页眉", desc)
                    continue
                if check_type == "docx_require_footer":
                    if ftr is False:
                        add("页脚", desc)
                    continue
                if check_type == "docx_require_page_number":
                    if ftr is True and page_num is False:
                        add("页脚/页码", desc)
                    continue
                if not isinstance(normal, dict):
                    skipped.append(check_type)
                    continue
                if check_type == "docx_normal_font_contains":
                    contains = str(params.get("contains") or "").strip()
                    font = str(normal.get("font") or "").strip()
                    if contains and (contains not in font):
                        add("正文/字体", desc, f"Normal.font={font}")
                    continue
                if check_type == "docx_normal_size_pt":
                    expected = FormatRuleEngine._safe_float(params.get("value"))
                    tol = FormatRuleEngine._safe_float(params.get("tolerance")) or 0.2
                    size = FormatRuleEngine._safe_float(normal.get("size_pt"))
                    if expected is None or size is None:
                        skipped.append(check_type)
                        continue
                    if abs(size - expected) > tol:
                        add("正文/字体字号", desc, f"Normal.size_pt={size}")
                    continue
                if check_type == "docx_normal_line_spacing_pt":
                    expected = FormatRuleEngine._safe_float(params.get("value"))
                    tol = FormatRuleEngine._safe_float(params.get("tolerance")) or 0.5
                    line = FormatRuleEngine._safe_float(normal.get("line_spacing_pt"))
                    if expected is None or line is None:
                        skipped.append(check_type)
                        continue
                    if abs(line - expected) > tol:
                        add("正文/行距", desc, f"Normal.line_spacing_pt={line}")
                    continue

            skipped.append(check_type or "unknown")
        return issues, skipped
    @staticmethod
    def _count_cn(text: str) -> int:
        return len(re.findall(r"[\u4e00-\u9fff]", text or ""))

    @staticmethod
    def _count_words(text: str) -> int:
        return len(re.findall(r"\b\w+\b", text or ""))

    @staticmethod
    def _split_reference_block(full_text: str) -> Tuple[str, str]:
        t = (full_text or "").replace("\r\n", "\n").replace("\r", "\n")
        m = re.search(r"(?im)^\s*(参考文献|references)\s*$", t)
        if not m:
            return t, ""
        return t[: m.start()].strip(), t[m.end() :].strip()

    @staticmethod
    def _parse_keywords(full_text: str) -> Optional[List[str]]:
        t = (full_text or "").replace("\r\n", "\n").replace("\r", "\n")
        for line in t.split("\n")[:200]:
            if "关键词" not in line and "Key words" not in line and "Keywords" not in line:
                continue
            parts = re.split(r"[:：]", line, maxsplit=1)
            if len(parts) < 2:
                continue
            raw = parts[1].strip()
            raw = raw.replace("；", ";").replace("，", ",").replace("、", ",")
            items = [x.strip() for x in re.split(r"[;,]", raw) if x.strip()]
            if items:
                return items[:20]
        return None

    @staticmethod
    def _reference_items(ref_block: str) -> List[str]:
        t = (ref_block or "").replace("\r\n", "\n").replace("\r", "\n")
        items: List[str] = []
        for ln in t.split("\n"):
            if re.search(r"^\s*\[\d+\]\s*", ln):
                items.append(ln.strip())
        if items:
            return items
        for ln in t.split("\n"):
            if re.search(r"^\s*\d+\.\s+", ln):
                items.append(ln.strip())
        return items

    @staticmethod
    def _foreign_ref_count(items: List[str]) -> int:
        n = 0
        for it in items:
            if re.search(r"[A-Za-z]", it):
                n += 1
        return n

    @staticmethod
    def _recent_year_ratio(items: List[str]) -> Tuple[int, int]:
        years = []
        for it in items:
            years.extend([int(y) for y in re.findall(r"(19\d{2}|20\d{2})", it)])
        recent = [y for y in years if 2021 <= y <= 2035]
        return len(recent), len(years)

    @staticmethod
    def _collect_section_flags(full_text: str) -> Dict[str, bool]:
        t = (full_text or "").replace("\r\n", "\n").replace("\r", "\n")
        return {
            "摘要": bool(re.search(r"(?im)^\s*摘要\s*$", t)),
            "中文关键词": bool(re.search(r"关键词", t)),
            "英文摘要": bool(re.search(r"(?im)^\s*abstract\s*$", t)),
            "英文关键词": bool(re.search(r"(?i)\bkey\s*words\b|\bkeywords\b", t)),
            "目录": bool(re.search(r"(?im)^\s*目录\s*$", t)),
            "参考文献": bool(re.search(r"(?im)^\s*(参考文献|references)\s*$", t)),
            "致谢": bool(re.search(r"(?im)^\s*致谢\s*$", t)),
            "注释": bool(re.search(r"(?im)^\s*注释\s*$", t)),
            "附录": bool(re.search(r"(?im)^\s*附录", t)),
        }

    @staticmethod
    def analyze(
        *,
        paper_title: str,
        abstract: str,
        paper_content: str,
        full_text: Optional[str] = None,
        source_type: str = "text",
        docx_style_snapshot: Optional[Dict[str, Any]] = None,
        custom_rule_content: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        title = (paper_title or "").strip()
        abs_text = (abstract or "").strip()
        body = (paper_content or "").strip()
        full = (full_text or "\n\n".join([x for x in [title, abs_text, body] if x])).strip()
        full = full.replace("\r\n", "\n").replace("\r", "\n")

        main_text, ref_block = FormatRuleEngine._split_reference_block(full)
        ref_items = FormatRuleEngine._reference_items(ref_block)
        foreign_refs = FormatRuleEngine._foreign_ref_count(ref_items)
        recent_cnt, year_cnt = FormatRuleEngine._recent_year_ratio(ref_items)

        chinese_chars = FormatRuleEngine._count_cn(full)
        approx_words = FormatRuleEngine._count_words(full)
        abs_cn = FormatRuleEngine._count_cn(abs_text)
        title_cn = FormatRuleEngine._count_cn(title)
        cite_markers = len(re.findall(r"\[\d+\]", main_text))
        section_flags = FormatRuleEngine._collect_section_flags(full)
        keywords = FormatRuleEngine._parse_keywords(full)

        issues: List[FormatIssueItem] = []

        if title_cn > 36:
            issues.append(
                FormatIssueItem(
                    severity="major",
                    position="封面/标题",
                    description=f"论文题目中文字符数为 {title_cn}，超过学院要求的 36 个汉字上限。",
                    suggestion="缩短标题表达，保留核心研究对象与方法，删除冗余修饰语。",
                    evidence=title[:120],
                )
            )

        if abs_cn > 0 and (abs_cn < 250 or abs_cn > 500):
            issues.append(
                FormatIssueItem(
                    severity="major",
                    position="中文摘要",
                    description=f"摘要中文字符数约为 {abs_cn}，不满足学院要求的 250–500 字范围（仅基于提取文本估算）。",
                    suggestion="将摘要压缩或补充到 250–500 字，并覆盖目的意义、方法、结果与结论四要素。",
                )
            )

        if keywords is None:
            issues.append(
                FormatIssueItem(
                    severity="major",
                    position="中文摘要/关键词",
                    description="未在文本中识别到“关键词：…”行，或关键词无法解析。",
                    suggestion="在中文摘要后新增“关键词：”行，列出 3–5 个关键词，关键词之间用分号分隔，最后一个不加标点。",
                )
            )
        else:
            if len(keywords) < 3 or len(keywords) > 5:
                issues.append(
                    FormatIssueItem(
                        severity="major",
                        position="中文摘要/关键词",
                        description=f"关键词数量为 {len(keywords)}，不符合学院要求的 3–5 个。",
                        suggestion="将关键词调整为 3–5 个，尽量使用规范主题词；关键词之间用分号分隔。",
                        evidence="; ".join(keywords[:8]),
                    )
                )

        if not section_flags.get("目录", False):
            issues.append(
                FormatIssueItem(
                    severity="minor",
                    position="目录",
                    description="未识别到“目录”标题，可能缺少目录或提取文本中未包含目录。",
                    suggestion="确认已生成目录，并按学院要求列到三级标题且注明页码；目录字体为五号宋体且不加粗不斜体。",
                )
            )

        if not section_flags.get("参考文献", False):
            issues.append(
                FormatIssueItem(
                    severity="critical",
                    position="参考文献",
                    description="未识别到“参考文献/References”标题，可能缺少参考文献章节。",
                    suggestion="在正文末尾新增“参考文献”章节，按文中引用顺序以 [1][2]… 列出。",
                )
            )
        else:
            if len(ref_items) and len(ref_items) < 15:
                issues.append(
                    FormatIssueItem(
                        severity="major",
                        position="参考文献",
                        description=f"参考文献条目估算为 {len(ref_items)} 条，未满足学院要求的 ≥15 条（按“[n]”或“n.”开头估算）。",
                        suggestion="补充参考文献到 15 条以上，并确保与正文引用一一对应且按引用出现顺序排列。",
                    )
                )
            if len(ref_items) and foreign_refs < 3:
                issues.append(
                    FormatIssueItem(
                        severity="major",
                        position="参考文献",
                        description=f"外文参考文献条目估算为 {foreign_refs} 条，未满足学院要求的 ≥3 条（按条目含拉丁字母粗略估算）。",
                        suggestion="补充至少 3 条外文期刊/会议论文，并按学院给定著录格式整理。",
                    )
                )
            if len(ref_items) and year_cnt > 0:
                ratio = recent_cnt / max(1, year_cnt)
                if ratio < 0.4:
                    issues.append(
                        FormatIssueItem(
                            severity="minor",
                            position="参考文献",
                            description="参考文献中近 5 年（约 2021+）文献占比偏低（仅基于年份识别估算）。",
                            suggestion="优先补充近 5 年内的高质量期刊/会议论文，提升文献时效性。",
                        )
                    )

        if cite_markers == 0:
            issues.append(
                FormatIssueItem(
                    severity="minor",
                    position="正文引用",
                    description="未检测到形如 [1] 的引用标注，可能存在引用未标注或格式不一致。",
                    suggestion="正文引用统一使用 [n] 形式，并与参考文献列表编号对应。",
                )
            )

        fig_mentions = len(re.findall(r"图\s*\d+", full))
        fig_numbers = len(re.findall(r"图\s*\d+\s*[-—]\s*\d+", full))
        if fig_mentions and fig_numbers == 0:
            issues.append(
                FormatIssueItem(
                    severity="major",
                    position="图",
                    description="文本中出现“图1/图2”等引用，但未检测到按章编号的图号格式（如 图3-2）。",
                    suggestion="按学院要求使用“图<章>-<序号>”编号，并在图下方标注图号与图名；引用图需注明来源。",
                )
            )

        tab_mentions = len(re.findall(r"表\s*\d+", full))
        tab_numbers = len(re.findall(r"表\s*\d+\s*[-—]\s*\d+", full))
        if tab_mentions and tab_numbers == 0:
            issues.append(
                FormatIssueItem(
                    severity="major",
                    position="表格",
                    description="文本中出现“表1/表2”等引用，但未检测到按章编号的表号格式（如 表5-4）。",
                    suggestion="按学院要求使用“表<章>-<序号>”编号，表题置于表上方，并在表左下方注明数据来源。",
                )
            )

        formula_mentions = len(re.findall(r"\(\s*\d+\s*[-—]\s*\d+\s*\)", full))
        if "公式" in full and formula_mentions == 0:
            issues.append(
                FormatIssueItem(
                    severity="minor",
                    position="公式",
                    description="提到“公式”但未检测到按章编号的公式序号格式（如（3-1））。",
                    suggestion="公式应另起一行，并按章编号标注（3-1）（3-2）等。",
                )
            )

        code_blocks = len(re.findall(r"```", full))
        long_symbol_lines = 0
        for ln in full.split("\n"):
            s = ln.strip()
            if not s:
                continue
            if len(s) >= 60 and (len(re.findall(r"[{}();=<>/\\\[\]]", s)) >= 18):
                long_symbol_lines += 1
        if code_blocks >= 2 or long_symbol_lines >= 30:
            issues.append(
                FormatIssueItem(
                    severity="major",
                    position="正文/代码",
                    description="检测到较多疑似代码片段，可能违反学院“正文不允许出现大段程序代码、总量不超过3页”的要求（仅基于文本启发式判断）。",
                    suggestion="将大段代码移入附录；正文以流程/算法描述为主，并控制单个功能代码不超过半页。",
                    evidence=f"code_blocks={code_blocks}, dense_symbol_lines={long_symbol_lines}",
                )
            )

        if chinese_chars and chinese_chars < 12000:
            issues.append(
                FormatIssueItem(
                    severity="major",
                    position="全文篇幅",
                    description=f"提取到的中文字符数约为 {chinese_chars}，可能低于学院要求的 1.5 万字（仅基于提取文本估算，PDF/DOCX提取可能不完整）。",
                    suggestion="在Word中核对真实字数；若确实不足，请补充正文内容（尤其是方法、实验、结果与讨论）。",
                )
            )

        if docx_style_snapshot and source_type.lower() == "docx":
            styles = docx_style_snapshot.get("styles") if isinstance(docx_style_snapshot, dict) else None
            hdr = docx_style_snapshot.get("has_header") if isinstance(docx_style_snapshot, dict) else None
            ftr = docx_style_snapshot.get("has_footer") if isinstance(docx_style_snapshot, dict) else None
            page_num = docx_style_snapshot.get("has_page_number") if isinstance(docx_style_snapshot, dict) else None

            if hdr is False:
                issues.append(
                    FormatIssueItem(
                        severity="major",
                        position="页眉",
                        description="DOCX 未检测到页眉部件，可能缺少学院要求的页眉（正文开始）。",
                        suggestion="为正文添加页眉：左侧“上海杉达学院毕业论文”，右侧论文题目，字体小五号宋体。",
                    )
                )
            if ftr is False:
                issues.append(
                    FormatIssueItem(
                        severity="major",
                        position="页脚",
                        description="DOCX 未检测到页脚部件，可能缺少页脚页码。",
                        suggestion="在页脚中间插入页码（正文开始连续编码）。",
                    )
                )
            if ftr is True and page_num is False:
                issues.append(
                    FormatIssueItem(
                        severity="major",
                        position="页脚/页码",
                        description="检测到页脚但未检测到页码字段（PAGE），可能未按要求插入自动页码。",
                        suggestion="在页脚中插入自动页码字段（而非手工输入），并从正文开始连续编号。",
                    )
                )
            if isinstance(styles, dict):
                normal = styles.get("Normal") or {}
                if isinstance(normal, dict):
                    font = (normal.get("font") or "").strip()
                    size = normal.get("size_pt")
                    line = normal.get("line_spacing_pt")
                    if size is not None and isinstance(size, (int, float)) and abs(float(size) - 10.5) > 0.2:
                        issues.append(
                            FormatIssueItem(
                                severity="major",
                                position="正文/字体字号",
                                description="DOCX 样式检测显示正文字号可能不是五号（10.5pt）。",
                                suggestion="将正文统一为五号宋体（10.5pt），并确保全文字体字号一致。",
                                evidence=f"Normal.size_pt={size}",
                            )
                        )
                    if line is not None and isinstance(line, (int, float)) and abs(float(line) - 20.0) > 0.5:
                        issues.append(
                            FormatIssueItem(
                                severity="major",
                                position="正文/行距",
                                description="DOCX 样式检测显示正文行距可能不是固定 20 磅。",
                                suggestion="将正文行距设置为固定值 20 磅，并统一段前段后。",
                                evidence=f"Normal.line_spacing_pt={line}",
                            )
                        )
                    if font and ("宋体" not in font):
                        issues.append(
                            FormatIssueItem(
                                severity="minor",
                                position="正文/字体",
                                description="DOCX 样式检测显示正文字体可能不是宋体。",
                                suggestion="将正文统一为五号宋体，并检查标题、摘要、关键词等是否符合学院字体要求。",
                                evidence=f"Normal.font={font}",
                            )
                        )

        custom_exec_issues: List[FormatIssueItem] = []
        skipped_custom: List[str] = []
        mode = "augment"
        if isinstance(custom_rule_content, dict):
            mode_raw = str(custom_rule_content.get("mode") or "augment").strip().lower()
            mode = "replace" if mode_raw == "replace" else "augment"
            exec_rules = custom_rule_content.get("executable_rules")
            if isinstance(exec_rules, list) and exec_rules:
                custom_exec_issues, skipped_custom = FormatRuleEngine._apply_exec_rules(
                    executable_rules=exec_rules,
                    title=title,
                    abs_text=abs_text,
                    full_text=full,
                    main_text=main_text,
                    ref_items=ref_items,
                    foreign_refs=foreign_refs,
                    section_flags=section_flags,
                    keywords=keywords,
                    docx_style_snapshot=docx_style_snapshot,
                    source_type=source_type,
                )

        final_issues: List[Dict[str, Any]] = []
        if mode == "replace":
            final_issues = [x.to_public_dict() for x in custom_exec_issues]
        else:
            final_issues = [x.to_public_dict() for x in issues] + [x.to_public_dict() for x in custom_exec_issues]
        final_issues = FormatRuleEngine._dedupe_issue_dicts(final_issues)

        auto_metrics: Dict[str, Any] = {
            "source_type": source_type,
            "title_cn_chars": title_cn,
            "abstract_cn_chars": abs_cn,
            "chinese_chars_est": chinese_chars,
            "words_est": approx_words,
            "keywords_count": len(keywords) if keywords else 0,
            "citation_markers_count": cite_markers,
            "references_count_est": len(ref_items),
            "foreign_references_count_est": foreign_refs,
            "recent_year_count_est": recent_cnt,
            "year_count_est": year_cnt,
            "section_flags": section_flags,
        }
        if isinstance(custom_rule_content, dict):
            auto_metrics["custom_rule_mode"] = mode
            auto_metrics["custom_exec_rules_count"] = len(custom_rule_content.get("executable_rules") or []) if isinstance(custom_rule_content.get("executable_rules"), list) else 0
            auto_metrics["custom_exec_rules_skipped"] = skipped_custom[:50]

        return {
            "rule_issues": final_issues,
            "auto_metrics": auto_metrics,
        }
