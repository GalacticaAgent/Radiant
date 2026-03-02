from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from loguru import logger


class OpenAlexCrawler:
    BASE_URL = "https://api.openalex.org"
    TIMEOUT = httpx.Timeout(12.0, connect=8.0)

    @staticmethod
    def _reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> str:
        if not inverted_index:
            return ""
        positions: Dict[int, str] = {}
        for token, idxs in inverted_index.items():
            for i in idxs:
                positions[int(i)] = token
        if not positions:
            return ""
        max_i = max(positions.keys())
        words = [positions.get(i, "") for i in range(max_i + 1)]
        return " ".join([w for w in words if w]).strip()

    def search_works(self, query: str, per_page: int = 5) -> List[Dict[str, Any]]:
        try:
            url = f"{self.BASE_URL}/works"
            params = {"search": query, "per_page": min(per_page, 25)}
            with httpx.Client(timeout=self.TIMEOUT) as client:
                r = client.get(url, params=params)
            if r.status_code != 200:
                logger.warning(f"OpenAlex search works failed: {r.status_code}")
                return []
            data = r.json()
            results = data.get("results", []) or []
            parsed = []
            for w in results:
                if not isinstance(w, dict):
                    continue
                try:
                    parsed.append(self._parse_work(w))
                except Exception:
                    continue
            return parsed
        except Exception as e:
            logger.error(f"OpenAlex search works error: {str(e)}")
            return []

    def get_author(self, author_id: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.BASE_URL}/authors/{author_id}"
            with httpx.Client(timeout=self.TIMEOUT) as client:
                r = client.get(url)
            if r.status_code == 200:
                return self._parse_author(r.json())
            if r.status_code == 404:
                return None
            logger.warning(f"OpenAlex get author failed: {r.status_code}")
            return None
        except Exception as e:
            logger.error(f"OpenAlex get author error: {str(e)}")
            return None

    def get_author_works(self, author_id: str, per_page: int = 10) -> List[Dict[str, Any]]:
        try:
            url = f"{self.BASE_URL}/works"
            params = {
                "filter": f"authorships.author.id:https://openalex.org/{author_id}",
                "sort": "cited_by_count:desc",
                "per_page": min(per_page, 25),
            }
            with httpx.Client(timeout=self.TIMEOUT) as client:
                r = client.get(url, params=params)
            if r.status_code != 200:
                logger.warning(f"OpenAlex get author works failed: {r.status_code}")
                return []
            data = r.json()
            results = data.get("results", []) or []
            out: List[Dict[str, Any]] = []
            for w in results:
                if not isinstance(w, dict):
                    continue
                try:
                    out.append(self._parse_work(w))
                except Exception:
                    continue
            return out
        except Exception as e:
            logger.error(f"OpenAlex get author works error: {str(e)}")
            return []

    def _parse_work(self, w: Dict[str, Any]) -> Dict[str, Any]:
        authors = []
        for au in w.get("authorships", []) or []:
            if not isinstance(au, dict):
                continue
            a = au.get("author") or {}
            insts = au.get("institutions") or []
            if not isinstance(insts, list):
                insts = []
            aff = insts[0].get("display_name") if insts and isinstance(insts[0], dict) else None
            aid = a.get("id") or ""
            if isinstance(aid, str) and aid.startswith("https://openalex.org/"):
                aid = aid.split("https://openalex.org/", 1)[1]
            authors.append({"id": aid, "name": a.get("display_name"), "affiliation": aff})

        abstract = self._reconstruct_abstract(w.get("abstract_inverted_index"))
        wid = w.get("id") or ""
        if isinstance(wid, str) and wid.startswith("https://openalex.org/"):
            wid = wid.split("https://openalex.org/", 1)[1]

        return {
            "openalex_id": wid,
            "title": w.get("display_name") or w.get("title"),
            "abstract": abstract,
            "year": w.get("publication_year"),
            "venue": (w.get("primary_location") or {}).get("source", {}).get("display_name"),
            "citation_count": w.get("cited_by_count", 0),
            "url": (w.get("primary_location") or {}).get("landing_page_url") or w.get("id"),
            "authors": authors,
            "source": "openalex",
        }

    def _parse_author(self, a: Dict[str, Any]) -> Dict[str, Any]:
        aid = a.get("id") or ""
        if isinstance(aid, str) and aid.startswith("https://openalex.org/"):
            aid = aid.split("https://openalex.org/", 1)[1]
        inst = None
        if isinstance(a.get("last_known_institution"), dict):
            inst = a["last_known_institution"].get("display_name")
        return {
            "id": aid,
            "name": a.get("display_name"),
            "affiliations": [inst] if inst else [],
            "paper_count": a.get("works_count"),
            "citation_count": a.get("cited_by_count"),
            "h_index": (a.get("summary_stats") or {}).get("h_index"),
            "url": a.get("id"),
            "source": "openalex",
        }
