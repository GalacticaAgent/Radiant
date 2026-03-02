"""
DeepSeek LLM 服务
提供与 DeepSeek API 的集成
"""

from typing import List, Dict, Any, Optional, Iterator, Tuple
from openai import OpenAI
from app.core.config import settings
import logging
from pathlib import Path
import re
import json

logger = logging.getLogger(__name__)


class LLMService:
    """DeepSeek LLM 服务类"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 LLM 服务

        Args:
            api_key: DeepSeek API Key（可选，默认使用配置中的key）
        """
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        if not self.api_key:
            raise ValueError("DeepSeek API Key 未配置")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=settings.DEEPSEEK_BASE_URL
        )
        self._review_skill_prompt: Optional[str] = None
        self._format_review_skill_prompt: Optional[str] = None

    def _load_review_skill_prompt(self) -> str:
        if self._review_skill_prompt is not None:
            return self._review_skill_prompt
        prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "review_skill.md"
        self._review_skill_prompt = prompt_path.read_text(encoding="utf-8")
        return self._review_skill_prompt

    def _load_format_review_skill_prompt(self) -> str:
        if self._format_review_skill_prompt is not None:
            return self._format_review_skill_prompt

        root = Path(__file__).resolve().parents[3]
        skill_path = root / ".trae" / "skills" / "format-review" / "SKILL.md"
        try:
            raw = skill_path.read_text(encoding="utf-8")
            raw = re.sub(r"^---\s*[\s\S]*?---\s*", "", raw).strip()
            m1 = re.search(r"^###\s*1\.", raw, re.MULTILINE)
            if m1:
                end = re.search(r"^##\s+格式审查指南\b", raw[m1.start() :], re.MULTILINE)
                if end:
                    raw = raw[m1.start() : m1.start() + end.start()].strip()
                else:
                    raw = raw[m1.start() :].strip()
            if raw:
                self._format_review_skill_prompt = raw
                return self._format_review_skill_prompt
        except Exception:
            pass

        self._format_review_skill_prompt = (
            "请按如下结构输出格式审查（Markdown），不要复述框架文本：\n"
            "## 1. 格式概况\n"
            "- 3-5 条总结\n"
            "## 2. 主要格式问题\n"
            "- 列出 3-8 条：位置、问题、修改建议\n"
            "## 3. 次要格式问题\n"
            "- 列出 0-10 条：位置、问题、修改建议\n"
            "## 4. 修改优先级\n"
            "- 高/中/低，并给出理由\n"
            "## 5. 结论\n"
            "- 给出总体评分与下一步\n"
        )
        return self._format_review_skill_prompt

    @staticmethod
    def _truncate_text_middle(text: str, max_chars: int) -> str:
        raw = (text or "").strip()
        if not raw:
            return ""
        if len(raw) <= max_chars:
            return raw
        head = max_chars // 2
        tail = max_chars - head
        return (raw[:head].rstrip() + "\n\n……（内容过长，已截断）……\n\n" + raw[-tail:].lstrip()).strip()

    @staticmethod
    def _strip_fenced_code_blocks(markdown: str) -> str:
        md = (markdown or "").strip()
        if not md:
            return ""
        md = re.sub(r"```[\s\S]*?```", "", md)
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        return md

    @staticmethod
    def _extract_json_any(response_text: str) -> Dict[str, Any]:
        text = (response_text or "").strip()
        if not text:
            return {}
        fence = re.search(r"```\s*json\s*([\s\S]*?)```", text, re.IGNORECASE)
        if fence:
            candidate = fence.group(1).strip()
            try:
                return json.loads(candidate)
            except Exception:
                pass

        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last != -1 and last > first:
            candidate = text[first : last + 1].strip()
            try:
                return json.loads(candidate)
            except Exception:
                pass

        return {}

    @staticmethod
    def _coerce_str_list(value: Any) -> List[str]:
        if isinstance(value, list):
            out: List[str] = []
            for x in value:
                s = str(x).strip()
                if s:
                    out.append(s)
            return out
        if isinstance(value, str):
            lines = [x.strip(" -*\t").strip() for x in value.splitlines()]
            return [x for x in lines if x]
        return []

    @staticmethod
    def _ensure_review_payload(data: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = dict(data or {})
        out["strengths"] = LLMService._coerce_str_list(out.get("strengths"))
        out["weaknesses"] = LLMService._coerce_str_list(out.get("weaknesses"))
        out["suggestions"] = LLMService._coerce_str_list(out.get("suggestions"))

        score_raw = out.get("overall_score") or out.get("rating")
        score: Optional[int] = None
        try:
            if isinstance(score_raw, (int, float)):
                score = int(score_raw)
            elif score_raw is not None:
                m = re.search(r"\d+", str(score_raw))
                score = int(m.group(0)) if m else None
        except Exception:
            score = None
        if score is not None:
            score = max(1, min(10, score))
        out["overall_score"] = score

        for k in ("recommendation", "confidence"):
            v = out.get(k)
            out[k] = str(v).strip() if v is not None and str(v).strip() else None
        return out

    @staticmethod
    def _render_review_markdown(payload: Dict[str, Any]) -> str:
        strengths = payload.get("strengths") if isinstance(payload.get("strengths"), list) else []
        weaknesses = payload.get("weaknesses") if isinstance(payload.get("weaknesses"), list) else []
        suggestions = payload.get("suggestions") if isinstance(payload.get("suggestions"), list) else []
        score = payload.get("overall_score")
        confidence = payload.get("confidence")
        recommendation = payload.get("recommendation")

        parts: List[str] = []
        parts.append("### 总体建议")
        if score is not None:
            parts.append(f"- Rating: {score}/10")
        if confidence:
            parts.append(f"- Confidence: {confidence}")
        if recommendation:
            parts.append(f"- Recommendation: {recommendation}")
        parts.append("")

        if strengths:
            parts.append("### 优点")
            parts.extend([f"- {x}" for x in strengths])
            parts.append("")
        if weaknesses:
            parts.append("### 缺点")
            parts.extend([f"- {x}" for x in weaknesses])
            parts.append("")
        if suggestions:
            parts.append("### 修改建议")
            parts.extend([f"- {x}" for x in suggestions])
            parts.append("")

        return "\n".join(parts).strip()

    @staticmethod
    def _coerce_issue_list(raw: Any) -> List[Dict[str, Any]]:
        if not isinstance(raw, list):
            return []
        out: List[Dict[str, Any]] = []
        for it in raw:
            if not isinstance(it, dict):
                continue
            sev = str(it.get("severity") or "").strip()
            pos = str(it.get("position") or "").strip()
            desc = str(it.get("description") or "").strip()
            sug = str(it.get("suggestion") or "").strip()
            evidence = it.get("evidence")
            row: Dict[str, Any] = {"severity": sev, "position": pos, "description": desc, "suggestion": sug}
            if isinstance(evidence, str) and evidence.strip():
                row["evidence"] = evidence.strip()
            out.append(row)
        return out

    @staticmethod
    def _coerce_rule_list(raw: Any) -> List[Dict[str, Any]]:
        if not isinstance(raw, list):
            return []
        out: List[Dict[str, Any]] = []
        for it in raw:
            if not isinstance(it, dict):
                continue
            rid = str(it.get("id") or it.get("key") or "").strip()
            sev = str(it.get("severity") or "").strip()
            desc = str(it.get("description") or it.get("requirement") or "").strip()
            check_method = str(it.get("check_method") or it.get("how_to_check") or "").strip()
            sug = str(it.get("suggestion") or "").strip()
            if not desc:
                continue
            row: Dict[str, Any] = {"severity": sev or "major", "description": desc}
            if rid:
                row["id"] = rid
            if check_method:
                row["check_method"] = check_method
            if sug:
                row["suggestion"] = sug
            for extra_key in ("scope", "rationale", "evidence", "example"):
                v = it.get(extra_key)
                if isinstance(v, str) and v.strip():
                    row[extra_key] = v.strip()
            out.append(row)
        return out

    @staticmethod
    def _coerce_exec_rule_list(raw: Any) -> List[Dict[str, Any]]:
        if not isinstance(raw, list):
            return []
        out: List[Dict[str, Any]] = []
        for it in raw:
            if not isinstance(it, dict):
                continue
            rid = str(it.get("id") or it.get("key") or "").strip()
            sev = str(it.get("severity") or "").strip()
            desc = str(it.get("description") or it.get("requirement") or "").strip()
            check_type = str(it.get("check_type") or it.get("type") or "").strip()
            params = it.get("params")
            sug = str(it.get("suggestion") or "").strip()
            if not check_type or not desc:
                continue
            row: Dict[str, Any] = {
                "severity": sev or "major",
                "check_type": check_type,
                "params": params if isinstance(params, dict) else {},
                "description": desc,
            }
            if rid:
                row["id"] = rid
            if sug:
                row["suggestion"] = sug
            for extra_key in ("scope", "rationale"):
                v = it.get(extra_key)
                if isinstance(v, str) and v.strip():
                    row[extra_key] = v.strip()
            out.append(row)
        return out

    @staticmethod
    def _ensure_format_rule_payload(data: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = dict(data or {})
        name = out.get("name") or out.get("rule_name")
        out["name"] = str(name).strip() if name is not None and str(name).strip() else None
        summary = out.get("summary")
        out["summary"] = str(summary).strip() if summary is not None and str(summary).strip() else None

        mode = str(out.get("mode") or "augment").strip().lower()
        out["mode"] = "replace" if mode == "replace" else "augment"

        exec_rules = out.get("executable_rules") or out.get("hard_rules") or []
        llm_rules = out.get("llm_rules") or out.get("soft_rules") or out.get("rules") or []

        out["executable_rules"] = LLMService._coerce_exec_rule_list(exec_rules)
        out["llm_rules"] = LLMService._coerce_rule_list(llm_rules)

        if isinstance(out.get("executable_rules"), list) and len(out["executable_rules"]) > 60:
            out["executable_rules"] = out["executable_rules"][:60]
        if isinstance(out.get("llm_rules"), list) and len(out["llm_rules"]) > 60:
            out["llm_rules"] = out["llm_rules"][:60]

        out.pop("rules", None)
        return out

    @staticmethod
    def _ensure_format_payload(data: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = dict(data or {})
        out["issues"] = LLMService._coerce_issue_list(out.get("issues"))
        grade = out.get("overall_grade")
        priority = out.get("priority")
        summary = out.get("summary")
        out["overall_grade"] = str(grade).strip() if grade is not None and str(grade).strip() else None
        out["priority"] = str(priority).strip() if priority is not None and str(priority).strip() else None
        out["summary"] = str(summary).strip() if summary is not None and str(summary).strip() else None
        return out

    @staticmethod
    def _render_format_review_markdown(payload: Dict[str, Any], llm_issues: List[Dict[str, Any]]) -> str:
        grade = payload.get("overall_grade") or "需要改进"
        priority = payload.get("priority") or "中"
        summary = payload.get("summary") or ""
        parts: List[str] = []
        parts.append("### 格式审查结论")
        parts.append(f"- 总体等级：{grade}")
        parts.append(f"- 修改优先级：{priority}")
        if summary:
            parts.append(f"- 概述：{summary}")
        parts.append("")

        if llm_issues:
            parts.append("### AI 补充问题（规则引擎无法判定部分）")
            for it in llm_issues[:60]:
                sev = str(it.get("severity") or "").strip()
                pos = str(it.get("position") or "").strip()
                desc = str(it.get("description") or "").strip()
                sug = str(it.get("suggestion") or "").strip()
                if not desc:
                    continue
                line = f"- [{sev or 'minor'}] {pos or '未标注位置'}：{desc}"
                if sug:
                    line += f"（建议：{sug}）"
                parts.append(line)
            parts.append("")

        return "\n".join(parts).strip()

    @staticmethod
    def _format_review_autocheck(paper_title: str, abstract: str, paper_content: str) -> str:
        import re

        title = (paper_title or "").strip()
        abs_text = (abstract or "").strip()
        body = (paper_content or "").strip()
        full = "\n".join([x for x in [title, abs_text, body] if x]).replace("\r\n", "\n").replace("\r", "\n")

        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", full))
        approx_words = len(re.findall(r"\b\w+\b", full))

        def has(pattern: str) -> bool:
            return bool(re.search(pattern, full, re.IGNORECASE | re.MULTILINE))

        section_flags = {
            "摘要": has(r"^\s*摘要\s*$"),
            "ABSTRACT": has(r"^\s*abstract\s*$"),
            "关键词": has(r"关键词"),
            "目录": has(r"^\s*目录\s*$"),
            "参考文献": has(r"参考文献|references"),
            "致谢": has(r"^\s*致谢\s*$"),
            "附录": has(r"^\s*附录"),
        }

        cite_markers = len(re.findall(r"\[\d+\]", full))
        years = [int(y) for y in re.findall(r"(19\d{2}|20\d{2})", full)]
        recent_years = [y for y in years if 2018 <= y <= 2035]
        ref_block = ""
        m = re.search(r"(参考文献|references)\s*([\s\S]{0,5000})$", full, re.IGNORECASE)
        if m:
            ref_block = m.group(2)
        ref_items = len(re.findall(r"^\s*\[\d+\]", ref_block, re.MULTILINE)) if ref_block else 0
        foreign_guess = 0
        if ref_block:
            for ln in ref_block.split("\n")[:300]:
                if re.search(r"^\s*\[\d+\]", ln) and re.search(r"[A-Za-z]", ln):
                    foreign_guess += 1

        abs_ch = len(re.findall(r"[\u4e00-\u9fff]", abs_text))
        title_ch = len(re.findall(r"[\u4e00-\u9fff]", title))

        rows = []
        rows.append(f"- 标题（中文字符数）：{title_ch}（学院要求≤36）")
        rows.append(f"- 摘要（中文字符数）：{abs_ch}（学院要求250–500字，若摘要非中文或为截断文本则仅供参考）")
        rows.append(f"- 估算篇幅：中文字符约 {chinese_chars}；英文/数字词约 {approx_words}（仅基于提取文本，非Word计数）")
        rows.append(f"- 引用标注形如[1]数量：{cite_markers}")
        rows.append(f"- 参考文献条目（按“[n]”估算）：{ref_items}；外文条目（按含拉丁字母估算）：{foreign_guess}")
        rows.append(f"- 近年年份（2018+）出现次数：{len(recent_years)}")
        rows.append("- 关键部分检测：" + "；".join([f"{k}={'有' if v else '无'}" for k, v in section_flags.items()]))
        return "\n".join(rows)

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Any:
        """
        调用 DeepSeek Chat API
        """
        try:
            # 优化：如果是流式输出，可以考虑减少 max_tokens 限制，或者调整 temperature 以加快首字生成
            # 但实际上主要延迟来自于网络和模型推理
            # 这里我们保持基本参数，但确保 stream=True 时能尽快返回
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            return response
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {e}")
            raise

    def simple_chat(self, user_message: str) -> str:
        """
        简单的单轮对话

        Args:
            user_message: 用户消息

        Returns:
            str: AI 回复
        """
        messages = [{"role": "user", "content": user_message}]
        response = self.chat(messages)
        return response.choices[0].message.content

    def chat_with_context(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        带上下文的对话

        Args:
            user_message: 用户消息
            system_prompt: 系统提示词（可选）
            history: 历史对话记录（可选）

        Returns:
            str: AI 回复
        """
        messages = []

        # 添加系统提示
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # 添加历史对话
        if history:
            messages.extend(history)

        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})

        response = self.chat(messages)
        return response.choices[0].message.content

    def stream_chat(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """
        流式对话

        Args:
            messages: 消息列表

        Yields:
            str: 流式返回的文本片段
        """
        response = self.chat(messages, stream=True)

        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def generate_summary(self, text: str, max_length: int = 500) -> str:
        """
        生成文本摘要

        Args:
            text: 原始文本
            max_length: 摘要最大长度

        Returns:
            str: 摘要文本
        """
        prompt = f"""请对以下内容生成一个简洁的摘要（不超过{max_length}字）：

{text}

摘要："""

        return self.simple_chat(prompt)

    def evaluate_idea(self, idea: str, related_papers: List[str]) -> Dict[str, Any]:
        """
        评估研究 Idea 的可行性

        Args:
            idea: Idea 描述
            related_papers: 相关论文列表

        Returns:
            Dict: 评估结果
        """
        papers_text = "\n".join([f"- {paper}" for paper in related_papers])

        prompt = f"""作为一位资深研究顾问，请评估以下研究想法的可行性：

研究想法：
{idea}

相关文献：
{papers_text}

请从以下几个方面进行评估，并以JSON格式返回结果：
1. 对该想法的理解（understanding）
2. 创新性评分（0-10）（innovation_score）
3. 可行性评分（0-10）（feasibility_score）
4. 优点列表（pros）
5. 缺点列表（cons）
6. 改进建议列表（suggestions）

返回格式：
{{
    "understanding": "...",
    "innovation_score": 8,
    "feasibility_score": 7,
    "pros": ["...", "..."],
    "cons": ["...", "..."],
    "suggestions": ["...", "..."]
}}
"""

        response = self.simple_chat(prompt)

        # 尝试解析 JSON 响应
        import json
        import re

        # 提取 JSON 部分
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # 如果解析失败，返回原始文本
        return {"raw_response": response}

    def generate_reviewer_profile(
        self,
        reviewer_name: str,
        papers: List[str],
        research_interests: List[str]
    ) -> str:
        """
        生成审稿人画像

        Args:
            reviewer_name: 审稿人姓名
            papers: 代表性论文列表
            research_interests: 研究方向

        Returns:
            str: 审稿人画像
        """
        papers_text = "\n".join([f"- {paper}" for paper in papers[:5]])  # 只取前5篇
        interests_text = ", ".join(research_interests)

        prompt = f"""请为以下研究者生成一个学术画像，描述其研究风格和关注点：

姓名：{reviewer_name}
研究方向：{interests_text}

代表性论文：
{papers_text}

请用2-3句话描述该研究者的研究特点、关注点和可能的审稿风格。
"""

        return self.simple_chat(prompt)

    def generate_review(
        self,
        paper_content: str,
        reviewer_profile: str,
        reviewer_name: str
    ) -> Dict[str, Any]:
        """
        基于审稿人画像生成审稿意见

        Args:
            paper_content: 论文内容
            reviewer_profile: 审稿人画像
            reviewer_name: 审稿人姓名

        Returns:
            Dict: 审稿意见
        """
        review_skill = self._load_review_skill_prompt()
        system_prompt = (
            "你是一位严格遵循学术同行评审规范的审稿人。请严格遵循下面的审稿框架输出，但不要复述框架文本本身。"
            "输出应当段落清晰、要点化，避免大段堆叠。"
            "\n\n"
            + review_skill
        )
        paper_excerpt = self._truncate_text_middle(paper_content, max_chars=18000)
        prompt = f"""审稿人姓名：{reviewer_name}

审稿人公开资料摘要（用于模拟真实审稿风格与关注点）：
{reviewer_profile}

论文正文（可能较长，请自行抓重点）：
{paper_excerpt}

输出要求：
1) 输出为 Markdown，标题从 ### 开始（避免与外层标题冲突），子标题用 ####，列表用 -。  
2) 不要输出“Paper Review”“A comprehensive framework...”等框架说明文字。  
3) 报告末尾追加一个 JSON 代码块（```json ... ```），仅用于机器解析，字段必须包含：strengths, weaknesses, suggestions, overall_score, recommendation, confidence。  
4) strengths/weaknesses/suggestions 为字符串数组；overall_score 为 1-10 整数。  
5) 除末尾 JSON 代码块外，不要输出任何其他代码块（不要出现额外的 ```），不要粘贴论文原文中的代码/大段公式推导。  
"""

        response = self.chat_with_context(user_message=prompt, system_prompt=system_prompt, history=[])
        json_block = re.search(r"```\s*json\s*([\s\S]*?)```", response, re.IGNORECASE)
        data = self._extract_json_any(response)
        data = self._ensure_review_payload(data)

        need_retry = (
            not data
            or not isinstance(data.get("strengths"), list)
            or not isinstance(data.get("weaknesses"), list)
            or not isinstance(data.get("suggestions"), list)
        )
        if need_retry:
            retry_prompt = f"""请仅输出一个 JSON 对象（不要 Markdown，不要代码块，不要额外文字），字段必须包含：
strengths（数组）, weaknesses（数组）, suggestions（数组）, overall_score（1-10整数）, recommendation（字符串）, confidence（字符串）。

审稿人姓名：{reviewer_name}
审稿人画像：{reviewer_profile}
论文正文（已截断）：{paper_excerpt}
"""
            retry_response = self.chat_with_context(user_message=retry_prompt, system_prompt=system_prompt, history=[])
            data2 = self._ensure_review_payload(self._extract_json_any(retry_response))
            if data2:
                data = data2

        review_markdown = response[: json_block.start()].strip() if json_block else response.strip()
        review_markdown = re.sub(r"^#\s*Paper Review\s*$", "", review_markdown, flags=re.IGNORECASE | re.MULTILINE).strip()
        review_markdown = re.sub(
            r"^A comprehensive framework for reviewing academic papers.*$",
            "",
            review_markdown,
            flags=re.IGNORECASE | re.MULTILINE,
        ).strip()
        review_markdown = re.sub(r"```\s*json[\s\S]*?```", "", review_markdown, flags=re.IGNORECASE).strip()
        review_markdown = re.sub(r"^##\s+", "### ", review_markdown, flags=re.MULTILINE)
        review_markdown = self._strip_fenced_code_blocks(review_markdown)
        if not review_markdown:
            review_markdown = self._render_review_markdown(data)

        data["review_markdown"] = review_markdown
        return data

    def generate_format_review(
        self,
        paper_title: str,
        abstract: str,
        paper_content: str,
        paper_language: str = "auto",
        full_text: Optional[str] = None,
        source_type: str = "text",
        docx_style_snapshot: Optional[Dict[str, Any]] = None,
        custom_rule_text: Optional[str] = None,
        custom_rule_content: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        skill = self._load_format_review_skill_prompt()
        system_prompt = (
            "你是一位严格遵循学术写作规范与格式要求的论文格式审查员。"
            "你必须且只能输出 8 个部分（### 1 到 ### 8），不得增加任何额外章节、附录、清单或说明文字。"
            "请严格遵循下面的格式审查框架输出，但不要复述框架文本本身。输出应当段落清晰、要点化，避免大段堆叠。"
            "\n\n"
            + skill
        )
        from app.services.format_rule_engine import FormatRuleEngine

        rule_result = FormatRuleEngine.analyze(
            paper_title=paper_title,
            abstract=abstract,
            paper_content=paper_content,
            full_text=full_text,
            source_type=source_type,
            docx_style_snapshot=docx_style_snapshot,
            custom_rule_content=custom_rule_content,
        )
        rule_issues = rule_result.get("rule_issues") if isinstance(rule_result, dict) else []
        auto_metrics = rule_result.get("auto_metrics") if isinstance(rule_result, dict) else {}

        rule_issues_preview = ""
        if isinstance(rule_issues, list) and rule_issues:
            preview_items = []
            for x in rule_issues[:25]:
                if not isinstance(x, dict):
                    continue
                sev = str(x.get("severity") or "").strip()
                pos = str(x.get("position") or "").strip()
                desc = str(x.get("description") or "").strip()
                sug = str(x.get("suggestion") or "").strip()
                line = f"- [{sev}] {pos}：{desc}"
                if sug:
                    line += f"（建议：{sug}）"
                preview_items.append(line)
            rule_issues_preview = "\n".join(preview_items).strip()

        custom_rule_block = ""
        custom_rule_payload = (custom_rule_text or "").strip()
        if not custom_rule_payload and isinstance(custom_rule_content, dict):
            try:
                mode = str(custom_rule_content.get("mode") or "augment").strip()
                exec_rules = custom_rule_content.get("executable_rules") if isinstance(custom_rule_content.get("executable_rules"), list) else []
                llm_rules = custom_rule_content.get("llm_rules") if isinstance(custom_rule_content.get("llm_rules"), list) else []
                lines: List[str] = []
                lines.append(f"- mode: {mode}")
                if exec_rules:
                    lines.append("- executable_rules（硬规则，已由规则引擎执行，以下仅供你避免重复输出）：")
                    for it in exec_rules[:30]:
                        if not isinstance(it, dict):
                            continue
                        desc = str(it.get("description") or "").strip()
                        ct = str(it.get("check_type") or "").strip()
                        params = it.get("params") if isinstance(it.get("params"), dict) else {}
                        if not desc or not ct:
                            continue
                        try:
                            params_s = json.dumps(params, ensure_ascii=False)
                        except Exception:
                            params_s = str(params)
                        lines.append(f"  - ({ct} {params_s}) {desc}")
                if llm_rules:
                    lines.append("- llm_rules（软规则，请优先遵循，若与通用学术规范冲突请指出冲突并给出折中建议）：")
                    for it in llm_rules[:30]:
                        if not isinstance(it, dict):
                            continue
                        desc = str(it.get("description") or "").strip()
                        cm = str(it.get("check_method") or "").strip()
                        if not desc:
                            continue
                        line = f"  - {desc}"
                        if cm:
                            line += f"（检查提示：{cm}）"
                        lines.append(line)
                custom_rule_payload = "\n".join(lines).strip()
            except Exception:
                custom_rule_payload = ""

        if custom_rule_payload:
            custom_rule_block = f"\n\n用户自定义审查规则（优先遵循，若与通用学术规范冲突请指出冲突并给出折中建议）：\n{custom_rule_payload}\n"

        prompt = f"""论文标题：
{paper_title}

摘要：
{abstract}

正文（可能较长，请自行抓重点，重点检查结构与引用格式等可从文本判断的要素）：
{paper_content}

自动检测结果（仅用于帮助你定位，不要逐条复述）：
{self._format_review_autocheck(paper_title, abstract, paper_content)}

规则引擎检测到的硬规则问题（仅用于帮助你定位，不要逐条复述）：
{rule_issues_preview or "- （无）"}
{custom_rule_block}

输出要求：
1) 输出为 Markdown，标题从 ### 开始（避免与外层标题冲突），子标题用 ####，列表用 -。
2) 不要输出框架说明文字。
3) 报告末尾追加一个 JSON 代码块（```json ... ```），仅用于机器解析，字段必须包含：issues, overall_grade, priority, summary。
4) issues 为数组，每个元素必须包含：severity, position, description, suggestion。issues 仅填写你新增的、规则引擎未覆盖/无法判定的问题，避免重复输出规则引擎已经给出的条目。
5) overall_grade 可取：优秀/良好/合格/需要改进/不合格；priority 可取：高/中/低。
6) 输出语言：{paper_language}（auto 表示跟随论文语言）。
7) 除末尾 JSON 代码块外，不要输出任何其他代码块（不要出现额外的 ```），不要粘贴论文原文代码。  
"""

        response = self.chat_with_context(user_message=prompt, system_prompt=system_prompt, history=[])
        json_block = re.search(r"```\s*json\s*([\s\S]*?)```", response, re.IGNORECASE)
        data = self._ensure_format_payload(self._extract_json_any(response))

        need_retry = (
            not data
            or not isinstance(data.get("issues"), list)
            or not data.get("overall_grade")
            or not data.get("priority")
        )
        if need_retry:
            retry_prompt = f"""请仅输出一个 JSON 对象（不要 Markdown，不要代码块，不要额外文字），字段必须包含：
issues（数组，每项含 severity/position/description/suggestion）, overall_grade（优秀/良好/合格/需要改进/不合格）, priority（高/中/低）, summary（字符串）。

论文标题：{paper_title}
摘要：{abstract}
正文（已截断）：{paper_content}

规则引擎硬规则问题（仅用于避免重复）：{rule_issues_preview or '无'}
"""
            retry_response = self.chat_with_context(user_message=retry_prompt, system_prompt=system_prompt, history=[])
            data2 = self._ensure_format_payload(self._extract_json_any(retry_response))
            if data2:
                data = data2

        review_markdown = response[: json_block.start()].strip() if json_block else response.strip()
        review_markdown = re.sub(r"```\s*json[\s\S]*?```", "", review_markdown, flags=re.IGNORECASE).strip()
        review_markdown = re.sub(r"^##\s+", "### ", review_markdown, flags=re.MULTILINE)
        review_markdown = self._strip_fenced_code_blocks(review_markdown)

        def _slice_1_8(md: str) -> str:
            s = (md or "").strip()
            if not s:
                return ""
            lines = s.splitlines()
            start = next((i for i, x in enumerate(lines) if re.match(r"^###\s*1\.", x)), -1)
            if start < 0:
                return s
            idx8 = next((i for i, x in enumerate(lines) if re.match(r"^###\s*8\.", x)), -1)
            if idx8 < 0:
                return "\n".join(lines[start:]).strip()
            end = len(lines)
            for i in range(idx8 + 1, len(lines)):
                if re.match(r"^###\s*\d+\.", lines[i]):
                    end = i
                    break
            return "\n".join(lines[start:end]).strip()

        def _dedupe(issues_a: List[Dict[str, Any]], issues_b: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            seen: set[Tuple[str, str]] = set()
            merged: List[Dict[str, Any]] = []
            for it in (issues_a or []) + (issues_b or []):
                pos = str(it.get("position") or "").strip().lower()
                desc = str(it.get("description") or "").strip().lower()
                key = (pos, desc)
                if not desc:
                    continue
                if key in seen:
                    continue
                seen.add(key)
                merged.append(it)
            return merged

        llm_issues = self._coerce_issue_list(data.get("issues"))
        merged_issues = _dedupe(self._coerce_issue_list(rule_issues), llm_issues)

        if not review_markdown:
            review_markdown = self._render_format_review_markdown(data, llm_issues)

        data["review_markdown"] = _slice_1_8(review_markdown)
        data["rule_issues"] = self._coerce_issue_list(rule_issues)
        data["llm_issues"] = llm_issues
        data["auto_metrics"] = auto_metrics if isinstance(auto_metrics, dict) else {}
        data["issues"] = merged_issues
        return data

    def generate_format_rule(
        self,
        *,
        source_filename: str,
        extracted_text: str,
        docx_style_snapshot: Optional[Dict[str, Any]] = None,
        language: str = "auto",
    ) -> Dict[str, Any]:
        system_prompt = (
            "你是一位擅长把“样例论文/模板”抽象为可执行审查规则的学术写作规范工程师。"
            "你要从用户上传的文档中总结出一套“格式审查规则”，用于后续审查同类论文。"
            "规则必须具体、可操作、可检查，避免空话。"
            "输出必须是一个 JSON 对象，不要 Markdown，不要代码块，不要额外文字。"
        )

        excerpt = self._truncate_text_middle(self._extract_rule_relevant_excerpt(extracted_text or "", max_chars=8000), max_chars=8000)
        style_json = json.dumps(docx_style_snapshot or {}, ensure_ascii=False)

        prompt = f"""输入信息：
- 文件名：{source_filename}
- 文档语言：{language}
- DOCX 样式/页眉页脚快照（可能为空）：{style_json}
- 提取文本（已截断）：{excerpt}

请输出 JSON，字段如下：
{{
  "name": "规则名称（≤30字符，中文优先）",
  "summary": "1-2 句总结该规则适用范围与风格",
  "mode": "augment 或 replace（augment=在系统默认规则基础上新增/强化；replace=仅按本规则审查）",
  "executable_rules": [
    {{
      "id": "简短英文或拼音标识（可选）",
      "severity": "critical/major/minor",
      "check_type": "检查类型标识（必须从允许列表里选一个）",
      "params": "检查参数对象（不同 check_type 结构不同）",
      "description": "明确的格式要求（必须/应当/不得）",
      "suggestion": "不符合时怎么改",
      "scope": "适用范围（如 封面/摘要/目录/正文/图表/参考文献/页眉页脚 等，可选）",
      "rationale": "为什么要这样（可选）"
    }}
  ],
  "llm_rules": [
    {{
      "id": "简短英文或拼音标识（可选）",
      "severity": "critical/major/minor",
      "description": "无法可靠程序化检查、但需要 LLM 辅助判定的要求",
      "check_method": "给 LLM 的检查提示（可选）",
      "suggestion": "不符合时怎么改",
      "scope": "适用范围（可选）"
    }}
  ]
}}

约束：
1) executable_rules 数量 6-20 条；llm_rules 数量 4-20 条。
2) executable_rules 的 check_type 只能从下列列表选择（不要自造）：
   - title_cn_max_chars, abstract_cn_range, keywords_count_range
   - require_toc, require_references_section, references_min_count, foreign_references_min_count
   - require_citation_markers
   - docx_require_header, docx_require_footer, docx_require_page_number
   - docx_normal_font_contains, docx_normal_size_pt, docx_normal_line_spacing_pt
3) params 示例：
   - title_cn_max_chars: {{"max": 36}}
   - abstract_cn_range: {{"min": 250, "max": 500}}
   - keywords_count_range: {{"min": 3, "max": 5}}
   - references_min_count: {{"min": 15}}
   - foreign_references_min_count: {{"min": 3}}
   - require_citation_markers: {{"pattern": "\\\\[\\\\d+\\\\]"}}
   - docx_normal_font_contains: {{"contains": "宋体"}}
   - docx_normal_size_pt: {{"value": 10.5, "tolerance": 0.2}}
   - docx_normal_line_spacing_pt: {{"value": 20.0, "tolerance": 0.5}}
4) 不要凭空捏造无法从文本/快照确定的具体数值；无法确定的，放进 llm_rules，用 check_method 描述如何判定。
5) 不要输出任何额外字段。"""

        response = self.chat_with_context(user_message=prompt, system_prompt=system_prompt, history=[])
        data = self._ensure_format_rule_payload(self._extract_json_any(response))
        if not data.get("name") or not data.get("rules"):
            retry_prompt = f"""请仅输出一个 JSON 对象（不要 Markdown，不要代码块，不要额外文字），字段必须包含：
name（字符串）, summary（字符串，可为空）, rules（数组，每项至少包含 severity/description/check_method/suggestion）。

文件名：{source_filename}
DOCX 快照：{style_json}
文本（已截断）：{excerpt}"""
            retry_response = self.chat_with_context(user_message=retry_prompt, system_prompt=system_prompt, history=[])
            data2 = self._ensure_format_rule_payload(self._extract_json_any(retry_response))
            if data2.get("name") and data2.get("rules"):
                data = data2
        return data

    def _extract_rule_relevant_excerpt(self, text: str, max_chars: int = 8000) -> str:
        raw = (text or "").strip()
        if not raw:
            return ""
        kws = [
            "字体",
            "字号",
            "行距",
            "段前",
            "段后",
            "缩进",
            "对齐",
            "页边距",
            "页眉",
            "页脚",
            "页码",
            "标题",
            "目录",
            "摘要",
            "关键词",
            "参考文献",
            "引用",
            "图",
            "表",
            "公式",
            "编号",
            "章节",
            "附录",
            "注释",
        ]
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        picked: List[str] = []
        total = 0
        for ln in lines:
            if any(k in ln for k in kws):
                if ln in picked:
                    continue
                picked.append(ln)
                total += len(ln) + 1
                if total >= max_chars:
                    break
        excerpt = "\n".join(picked).strip()
        if len(excerpt) < int(max_chars * 0.3):
            excerpt = raw
        return excerpt[: max_chars * 2]

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        从文本中提取关键词

        Args:
            text: 文本内容
            max_keywords: 最大关键词数量

        Returns:
            List[str]: 关键词列表
        """
        prompt = f"""请从以下文本中提取{max_keywords}个最重要的关键词，用逗号分隔：

{text}

关键词："""

        response = self.simple_chat(prompt)

        # 解析关键词
        keywords = [kw.strip() for kw in response.split(",")]
        return keywords[:max_keywords]


# 创建全局 LLM 服务实例
llm_service = LLMService()


def get_llm_service() -> LLMService:
    """
    获取 LLM 服务的依赖函数
    用于 FastAPI 的依赖注入

    Returns:
        LLMService: LLM 服务实例
    """
    return llm_service
