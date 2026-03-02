from app.core.config import settings
from app.services.virtual_reviewer_service import VirtualReviewerService


class _DummyReviewerService:
    def _extract_keywords(self, content: str, title: str | None = None):
        return []


def test_split_author_key():
    svc = VirtualReviewerService(reviewer_service=_DummyReviewerService())  # type: ignore
    assert svc._split_author_key("openalex:A123") == ("openalex", "A123")
    assert svc._split_author_key("A123") == ("semantic_scholar", "A123")


def test_discover_authors_falls_back_to_openalex(monkeypatch):
    svc = VirtualReviewerService(reviewer_service=_DummyReviewerService())  # type: ignore
    monkeypatch.setattr(settings, "SEMANTIC_SCHOLAR_API_KEY", None, raising=False)

    svc.oa.search_works = lambda query, per_page=25: [
        {
            "title": "Transformer for Vision",
            "citation_count": 1000,
            "authors": [{"id": "A1", "name": "Alice", "affiliation": "Lab"}],
            "source": "openalex",
            "openalex_id": "W1",
            "year": 2021,
            "venue": "NeurIPS",
            "url": "https://openalex.org/W1",
        }
    ]

    res = svc._discover_authors("transformer", ["transformer"])
    assert any(k.startswith("openalex:") for k in res.keys())
    author, papers = svc._fetch_author_profile("openalex", "A1")
    assert author and author.get("name") == "Alice"
    assert papers and papers[0].get("title")


def test_openalex_query_translation_hook(monkeypatch):
    svc = VirtualReviewerService(reviewer_service=_DummyReviewerService())  # type: ignore
    monkeypatch.setattr(settings, "SEMANTIC_SCHOLAR_API_KEY", None, raising=False)

    called = {"q": None}

    def fake_search(q: str, per_page: int = 25):
        called["q"] = q
        if q == "computer vision transformer":
            return [
                {
                    "title": "Vision Transformer",
                    "citation_count": 100,
                    "authors": [{"id": "A9", "name": "Bob", "affiliation": "Lab"}],
                    "source": "openalex",
                }
            ]
        return []

    svc.oa.search_works = fake_search
    svc._to_openalex_query = lambda q, keywords: "computer vision transformer"
    svc._discover_authors("中文论文题目", ["视觉", "Transformer"])
    assert called["q"] == "computer vision transformer"
