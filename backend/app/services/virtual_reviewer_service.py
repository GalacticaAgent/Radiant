import math
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.crawlers.openalex_crawler import OpenAlexCrawler
from app.crawlers.semantic_scholar_crawler import SemanticScholarCrawler
from app.core.config import settings
from app.models.paper import Paper
from app.models.reviewer import PaperReviewerCandidate, VirtualReviewer
from app.services.reviewer_service import ReviewerService


class VirtualReviewerService:
    def __init__(self, reviewer_service: ReviewerService):
        self.reviewer_service = reviewer_service
        delay = max(3.0, float(getattr(settings, "CRAWLER_DELAY", 3)) or 3.0)
        self.ss = SemanticScholarCrawler(api_key=settings.SEMANTIC_SCHOLAR_API_KEY, delay=delay)
        self.oa = OpenAlexCrawler()
        self._openalex_author_stub: Dict[str, Dict[str, Any]] = {}
        self._openalex_author_papers: Dict[str, List[Dict[str, Any]]] = {}

    def get_or_generate_candidates(
        self,
        db: Session,
        paper: Paper,
        limit: int = 5,
        refresh: bool = False,
        ttl_hours: int = 72,
    ) -> List[Dict[str, Any]]:
        self._openalex_author_stub = {}
        self._openalex_author_papers = {}
        if not refresh:
            cached = self._get_cached_candidates(db, paper.id, limit, ttl_hours)
            if cached:
                return cached

        keywords = self._extract_keywords(paper)
        queries = self._build_queries(paper.title or "", keywords, paper.abstract or "", paper.filename or "")

        author_scores: Dict[str, Tuple[int, List[str]]] = {}
        for q in queries:
            author_scores = self._discover_authors(query=q, keywords=keywords)
            if author_scores:
                break
        selected = sorted(author_scores.items(), key=lambda x: x[1][0], reverse=True)[: max(limit * 3, 10)]

        candidates: List[Tuple[VirtualReviewer, int, List[str], str]] = []
        for author_key, (score, matched) in selected:
            source, author_id = self._split_author_key(author_key)
            author, papers = self._fetch_author_profile(source, author_id)
            if not author or not author.get("name"):
                continue
            reviewer = self._upsert_virtual_reviewer(db, author, papers)
            rationale = self._build_rationale(author, matched)
            candidates.append((reviewer, score, matched, rationale))
            if len(candidates) >= limit:
                break

        if not candidates:
            return []

        self._write_candidate_cache(db, paper.id, candidates)
        return self._format_candidates(candidates)

    def _get_cached_candidates(self, db: Session, paper_id: uuid.UUID, limit: int, ttl_hours: int) -> List[Dict[str, Any]]:
        threshold = datetime.utcnow() - timedelta(hours=ttl_hours)
        rows = (
            db.query(PaperReviewerCandidate, VirtualReviewer)
            .join(VirtualReviewer, VirtualReviewer.id == PaperReviewerCandidate.reviewer_id)
            .filter(PaperReviewerCandidate.paper_id == paper_id, PaperReviewerCandidate.created_at >= threshold)
            .order_by(PaperReviewerCandidate.rank.asc())
            .limit(limit)
            .all()
        )
        if not rows:
            return []
        candidates = [(r[1], r[0].score, r[0].matched_keywords or [], r[0].rationale or "") for r in rows]
        return self._format_candidates(candidates)

    def _extract_keywords(self, paper: Paper) -> List[str]:
        text = (paper.abstract or "").strip()
        if not text:
            text = (paper.content or "")[:4000]
        title = (paper.title or "").strip()
        keywords = self.reviewer_service._extract_keywords(text, title=title)
        if keywords:
            return keywords[:8]
        tokens = re.findall(r"[A-Za-z][A-Za-z\\-]{3,}", f"{title} {text}"[:1200])
        uniq: List[str] = []
        for t in tokens:
            tl = t.lower()
            if tl in {"this", "that", "with", "from", "into", "over", "under", "between", "where", "which"}:
                continue
            if tl not in [x.lower() for x in uniq]:
                uniq.append(t)
            if len(uniq) >= 8:
                break
        return uniq

    def _build_query(self, title: str, keywords: List[str]) -> str:
        parts = [title.strip()] if title else []
        parts.extend(keywords[:5])
        return " ".join([p for p in parts if p])

    def _build_queries(self, title: str, keywords: List[str], abstract: str, filename: str) -> List[str]:
        cleaned_title = self._clean_title(title or filename or "")
        kw = [k for k in keywords if k and len(k) > 2]
        kw_phrase = " ".join(kw[:6])
        title_plus_kw = " ".join([x for x in [cleaned_title, kw_phrase] if x]).strip()

        abstract_tokens = self._extract_abstract_tokens(abstract)
        abs_phrase = " ".join(abstract_tokens[:6]) if abstract_tokens else ""
        title_plus_abs = " ".join([x for x in [cleaned_title, abs_phrase] if x]).strip()

        queries = []
        if title_plus_kw:
            queries.append(title_plus_kw)
        if cleaned_title:
            queries.append(cleaned_title)
        if kw_phrase:
            queries.append(kw_phrase)
        if title_plus_abs and title_plus_abs not in queries:
            queries.append(title_plus_abs)
        if abs_phrase and abs_phrase not in queries:
            queries.append(abs_phrase)
        return queries[:5]

    def _clean_title(self, raw: str) -> str:
        s = (raw or "").strip()
        s = re.sub(r"\.(pdf|tex|zip)$", "", s, flags=re.IGNORECASE).strip()
        s = re.sub(r"[_\-]+", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        words = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]{2,}", s)
        if not words:
            return s[:120]
        return " ".join(words[:14])

    def _extract_abstract_tokens(self, abstract: str) -> List[str]:
        if not abstract:
            return []
        tokens = re.findall(r"[A-Za-z][A-Za-z\\-]{3,}", abstract[:1500])
        stop = {"this", "that", "with", "from", "into", "over", "under", "between", "where", "which", "their", "therefore"}
        out: List[str] = []
        for t in tokens:
            tl = t.lower()
            if tl in stop:
                continue
            if tl not in [x.lower() for x in out]:
                out.append(t)
            if len(out) >= 12:
                break
        return out

    def _to_openalex_query(self, query: str, keywords: List[str]) -> str:
        q = (query or "").strip()
        if not q:
            return ""

        ascii_words = re.findall(r"[A-Za-z][A-Za-z\\-]{2,}", q)
        if len(ascii_words) >= 3:
            return q

        kw_ascii = []
        for k in keywords or []:
            kw_ascii.extend(re.findall(r"[A-Za-z][A-Za-z\\-]{2,}", str(k)))
        uniq = []
        for w in kw_ascii:
            wl = w.lower()
            if wl in [x.lower() for x in uniq]:
                continue
            uniq.append(w)
            if len(uniq) >= 8:
                break
        if uniq:
            return " ".join(uniq)

        if not re.search(r"[\\u4e00-\\u9fff]", q):
            return q

        try:
            llm = getattr(self.reviewer_service, "llm_service", None)
            if not llm:
                return q
            prompt = (
                "把下面的中文论文题目/关键词转换成 3-8 个英文检索关键词（用空格分隔），不要输出多余解释：\n\n"
                f"{q}\n\n"
                f"关键词：{', '.join([str(x) for x in (keywords or [])][:10])}\n"
            )
            translated = llm.chat_with_context(
                user_message=prompt,
                system_prompt="You are a helpful academic search assistant. Output only English search keywords separated by spaces.",
                history=[],
            )
            translated = (translated or "").strip()
            translated = re.sub(r"[^A-Za-z0-9\\-\\s]+", " ", translated)
            translated = re.sub(r"\\s+", " ", translated).strip()
            if translated:
                return translated[:180]
        except Exception:
            return q

        return q

    def _discover_authors(self, query: str, keywords: List[str]) -> Dict[str, Tuple[int, List[str]]]:
        if not query or len(query.strip()) < 3:
            return {}
        papers = []
        if getattr(settings, "SEMANTIC_SCHOLAR_API_KEY", None):
            papers = self.ss.search_papers(query, limit=30) or []
        if not papers:
            oa_query = self._to_openalex_query(query, keywords)
            papers = self.oa.search_works(oa_query, per_page=25) or []
            if not papers and oa_query != query:
                papers = self.oa.search_works(query, per_page=25) or []
        scores: Dict[str, Tuple[float, List[str]]] = {}
        for p in papers:
            title = (p.get("title") or "").lower()
            matched = [k for k in keywords if k and k.lower() in title]
            base = math.log1p(p.get("citation_count", 0) or 0) * 10.0 + (3.0 if matched else 0.0)
            for a in p.get("authors") or []:
                author_id = a.get("id")
                if not author_id:
                    continue
                source = str(p.get("source") or a.get("source") or "").strip().lower()
                if not source:
                    source = "semantic_scholar" if getattr(settings, "SEMANTIC_SCHOLAR_API_KEY", None) else "openalex"
                author_key = f"{source}:{author_id}"
                if source == "openalex":
                    stub = self._openalex_author_stub.get(author_id) or {
                        "id": author_id,
                        "name": a.get("name"),
                        "affiliations": [a.get("affiliation")] if a.get("affiliation") else [],
                        "paper_count": None,
                        "citation_count": None,
                        "h_index": None,
                        "url": f"https://openalex.org/{author_id}",
                        "source": "openalex",
                    }
                    if stub.get("name"):
                        self._openalex_author_stub[author_id] = stub

                    ap = self._openalex_author_papers.get(author_id) or []
                    work = {
                        "paper_id": p.get("paper_id") or p.get("openalex_id"),
                        "openalex_id": p.get("openalex_id"),
                        "title": p.get("title"),
                        "abstract": p.get("abstract"),
                        "year": p.get("year"),
                        "venue": p.get("venue"),
                        "citation_count": p.get("citation_count", 0),
                        "url": p.get("url"),
                        "authors": p.get("authors") or [],
                        "source": "openalex",
                    }
                    if work.get("title"):
                        ap.append(work)
                        ap = sorted(ap, key=lambda x: x.get("citation_count", 0) or 0, reverse=True)[:12]
                        self._openalex_author_papers[author_id] = ap
                prev = scores.get(author_key)
                if prev:
                    scores[author_key] = (prev[0] + base, list({*prev[1], *matched}))
                else:
                    scores[author_key] = (base, matched)
        ranked: Dict[str, Tuple[int, List[str]]] = {}
        for k, (s, m) in scores.items():
            ranked[k] = (int(min(s, 1000)), m[:8])
        return ranked

    def _split_author_key(self, key: str) -> Tuple[str, str]:
        raw = (key or "").strip()
        if ":" not in raw:
            return ("semantic_scholar", raw)
        source, author_id = raw.split(":", 1)
        source = (source or "").strip().lower()
        author_id = (author_id or "").strip()
        if not source:
            source = "semantic_scholar"
        return (source, author_id)

    def _fetch_author_profile(self, source: str, author_id: str) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        src = (source or "").strip().lower()
        if src == "openalex":
            author = self._openalex_author_stub.get(author_id) or self.oa.get_author(author_id)
            papers = self._openalex_author_papers.get(author_id) or self.oa.get_author_works(author_id, per_page=12)
            return author, papers
        author = self.ss.get_author(author_id)
        papers = self.ss.get_author_papers(author_id, limit=12)
        return author, papers

    def _upsert_virtual_reviewer(self, db: Session, author: Dict[str, Any], papers: List[Dict[str, Any]]) -> VirtualReviewer:
        source = str(author.get("source") or "semantic_scholar")
        external_id = str(author.get("id") or "")
        existing = (
            db.query(VirtualReviewer)
            .filter(VirtualReviewer.source == source, VirtualReviewer.external_id == external_id)
            .first()
        )
        affiliations = author.get("affiliations") or []
        affiliation = affiliations[0] if isinstance(affiliations, list) and affiliations else None
        profile_text = self._build_profile_text(author, papers)
        payload = {
            "source": source,
            "external_id": external_id,
            "name": author.get("name"),
            "affiliation": affiliation,
            "h_index": author.get("h_index"),
            "citation_count": author.get("citation_count"),
            "paper_count": author.get("paper_count"),
            "profile_text": profile_text,
            "top_papers": papers[:8],
            "talk_links": [],
            "raw_profile": author,
        }
        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing

        reviewer = VirtualReviewer(**payload)
        db.add(reviewer)
        db.commit()
        db.refresh(reviewer)
        return reviewer

    def _build_profile_text(self, author: Dict[str, Any], papers: List[Dict[str, Any]]) -> str:
        name = author.get("name") or "Reviewer"
        affiliation = ""
        affiliations = author.get("affiliations") or []
        if isinstance(affiliations, list) and affiliations:
            affiliation = affiliations[0]
        h_index = author.get("h_index")
        citation_count = author.get("citation_count")
        paper_count = author.get("paper_count")
        top_titles = [p.get("title") for p in sorted(papers, key=lambda x: x.get("citation_count", 0), reverse=True)[:5] if p.get("title")]
        lines = [
            f"Name: {name}",
            f"Affiliation: {affiliation}" if affiliation else "Affiliation: N/A",
            f"Metrics: h-index={h_index}, citations={citation_count}, papers={paper_count}",
        ]
        if top_titles:
            lines.append("Representative works:")
            lines.extend([f"- {t}" for t in top_titles])
        lines.append("Review style: Focus on methodology soundness, dataset validity, and reproducibility; compare to strong baselines; highlight concrete fixes.")
        return "\n".join(lines).strip()

    def _build_rationale(self, author: Dict[str, Any], matched: List[str]) -> str:
        parts = []
        if matched:
            parts.append("关键词匹配: " + ", ".join(matched[:5]))
        if author.get("h_index") is not None:
            parts.append(f"h-index {author.get('h_index')}")
        if author.get("paper_count") is not None:
            parts.append(f"papers {author.get('paper_count')}")
        return " · ".join(parts)[:780]

    def _write_candidate_cache(
        self,
        db: Session,
        paper_id: uuid.UUID,
        candidates: List[Tuple[VirtualReviewer, int, List[str], str]],
    ) -> None:
        db.query(PaperReviewerCandidate).filter(PaperReviewerCandidate.paper_id == paper_id).delete()
        for idx, (reviewer, score, matched, rationale) in enumerate(candidates):
            row = PaperReviewerCandidate(
                paper_id=paper_id,
                reviewer_id=reviewer.id,
                rank=idx,
                score=score,
                matched_keywords=matched,
                rationale=rationale,
            )
            db.add(row)
        db.commit()

    def _format_candidates(self, candidates: List[Tuple[VirtualReviewer, int, List[str], str]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for reviewer, score, matched, rationale in candidates:
            out.append(
                {
                    "id": f"vr:{reviewer.id}",
                    "name": reviewer.name,
                    "affiliation": reviewer.affiliation or "",
                    "h_index": reviewer.h_index or 0,
                    "citation_count": reviewer.citation_count or 0,
                    "paper_count": reviewer.paper_count or 0,
                    "match_score": score,
                    "matched_keywords": matched,
                    "rationale": rationale,
                    "source": reviewer.source,
                    "external_id": reviewer.external_id,
                    "top_papers": reviewer.top_papers or [],
                }
            )
        return out
