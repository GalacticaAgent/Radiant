from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from celery import shared_task
from loguru import logger

from app.crawlers.semantic_scholar_crawler import SemanticScholarCrawler
from app.crawlers.openalex_crawler import OpenAlexCrawler
from app.core.config import settings
from app.db.postgres import SessionLocal
from app.db.neo4j import get_neo4j
from app.models.kb import Author, CrawlEvent, CrawlJob, Embedding, ExternalPaper, PaperAuthor, Topic, PaperTopic
from app.models.paper import Paper
from app.services.embedding_service import EmbeddingService
from app.services.graph_service import GraphService
from app.services.kb_identity import external_paper_uuid


def _create_job(db, job_type: str, target_type: str, target_id: Optional[uuid.UUID]) -> CrawlJob:
    job = CrawlJob(job_type=job_type, target_type=target_type, target_id=target_id, status="running", attempts=1)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _add_event(db, job_id: uuid.UUID, level: str, message: str, payload: Optional[Dict[str, Any]] = None) -> None:
    ev = CrawlEvent(job_id=job_id, level=level, message=message, payload=payload or None)
    db.add(ev)
    db.commit()


def _finish_job(db, job: CrawlJob, status: str, last_error: Optional[str] = None) -> None:
    job.status = status
    job.last_error = last_error
    db.add(job)
    db.commit()


def _upsert_external_paper(db, paper: Dict[str, Any]) -> Optional[ExternalPaper]:
    source = str(paper.get("source") or "semantic_scholar").strip()
    ext_id = str(
        paper.get("paper_id")
        or paper.get("semantic_scholar_id")
        or paper.get("openalex_id")
        or ""
    ).strip()
    if not ext_id:
        return None
    title = (paper.get("title") or "").strip()
    if not title:
        return None
    pid = external_paper_uuid(source, ext_id)
    existing = db.query(ExternalPaper).filter(ExternalPaper.id == pid).first()
    if not existing:
        existing = ExternalPaper(id=pid, source=source, external_id=ext_id, title=title)
    existing.title = title
    existing.abstract = paper.get("abstract")
    existing.year = paper.get("year")
    existing.venue = paper.get("venue")
    existing.url = paper.get("url")
    existing.external_ids = paper.get("external_ids") or {}
    existing.fields_of_study = paper.get("fields_of_study") or []
    existing.citation_count = paper.get("citation_count")
    existing.raw = paper
    db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing


def _embed_external_paper(db, service: EmbeddingService, ext: ExternalPaper) -> bool:
    text = f"{ext.title or ''}\n\n{ext.abstract or ''}".strip()
    if not text:
        text = (ext.title or "").strip()
    if not text:
        return False
    h = service.content_hash(text)
    existing = (
        db.query(Embedding)
        .filter(Embedding.object_type == "external_paper", Embedding.object_id == ext.id, Embedding.model == service.model)
        .first()
    )
    if existing and existing.content_hash == h and existing.vector is not None:
        return True
    vec = service.embed_text(text)
    if not existing:
        existing = Embedding(object_type="external_paper", object_id=ext.id, model=service.model, dim=len(vec))
    existing.dim = len(vec)
    existing.vector = vec
    existing.vector_jsonb = vec
    existing.content_hash = h
    db.add(existing)
    db.commit()
    return True


def _upsert_ss_author(db, external_id: str, name: str) -> Optional[Author]:
    external_id = str(external_id or "").strip()
    name = str(name or "").strip()
    if not external_id or not name:
        return None
    existing = db.query(Author).filter(Author.source == "semantic_scholar", Author.external_id == external_id).first()
    if not existing:
        existing = Author(source="semantic_scholar", external_id=external_id, name=name)
        db.add(existing)
        db.commit()
        db.refresh(existing)
    return existing


@shared_task(name="kb_ingest_paper")
def kb_ingest_paper(paper_id: str) -> Dict[str, Any]:
    with SessionLocal() as db:
        job = _create_job(db, job_type="kb_ingest_paper", target_type="paper", target_id=uuid.UUID(paper_id))
        try:
            paper = db.query(Paper).filter(Paper.id == uuid.UUID(paper_id)).first()
            if not paper:
                raise RuntimeError("paper not found")

            _add_event(db, job.id, "info", "queued enrich/embed/graph sync tasks")
            kb_enrich_paper.delay(paper_id)
            kb_embed_paper.delay(paper_id)
            kb_sync_paper_graph.delay(paper_id)

            _finish_job(db, job, "done")
            return {"status": "success", "job_id": str(job.id)}
        except Exception as e:
            _add_event(db, job.id, "error", "ingest failed", {"error": str(e)})
            _finish_job(db, job, "failed", str(e))
            return {"status": "failed", "job_id": str(job.id), "error": str(e)}


@shared_task(name="kb_enrich_paper")
def kb_enrich_paper(paper_id: str) -> Dict[str, Any]:
    ss = SemanticScholarCrawler(api_key=settings.SEMANTIC_SCHOLAR_API_KEY, delay=max(3.0, float(settings.CRAWLER_DELAY or 3)))
    oa = OpenAlexCrawler()
    with SessionLocal() as db:
        job = _create_job(db, job_type="kb_enrich_paper", target_type="paper", target_id=uuid.UUID(paper_id))
        try:
            paper = db.query(Paper).filter(Paper.id == uuid.UUID(paper_id)).first()
            if not paper:
                raise RuntimeError("paper not found")

            meta = paper.paper_metadata or {}
            ss_meta = meta.get("semantic_scholar") if isinstance(meta, dict) else None
            existing_ss_id = (ss_meta or {}).get("paper_id") if isinstance(ss_meta, dict) else None
            existing_link_count = db.query(PaperAuthor).filter(PaperAuthor.paper_id == paper.id).count()
            if existing_ss_id and existing_link_count > 0:
                _finish_job(db, job, "done")
                return {"status": "success", "job_id": str(job.id), "enriched": True, "cached": True}

            query = (paper.title or "").strip()
            if not query or query.lower().endswith(".pdf") or query.lower() == (paper.filename or "").lower():
                extracted_title = meta.get("auto_extracted_title") if isinstance(meta, dict) else None
                if extracted_title:
                    query = str(extracted_title).strip()
            if not query:
                query = (paper.filename or "").strip()
            if not query:
                _add_event(db, job.id, "warn", "empty paper title/filename, skip enrich")
                _finish_job(db, job, "done")
                return {"status": "success", "job_id": str(job.id), "enriched": False}

            hits = ss.search_papers(query, limit=5)
            if not hits:
                oa_hits = oa.search_works(query, per_page=5)
                if not oa_hits:
                    _add_event(db, job.id, "warn", "no results from semantic scholar/openalex", {"query": query})
                    _finish_job(db, job, "done")
                    return {"status": "success", "job_id": str(job.id), "enriched": False}
                hit = oa_hits[0]
                meta = paper.paper_metadata or {}
                meta.setdefault("openalex", {})
                meta["openalex"].update(
                    {
                        "work_id": hit.get("openalex_id"),
                        "url": hit.get("url"),
                        "citation_count": hit.get("citation_count", 0),
                    }
                )
                paper.paper_metadata = meta
                if not paper.abstract and hit.get("abstract"):
                    paper.abstract = hit.get("abstract")
                if not paper.title and hit.get("title"):
                    paper.title = hit.get("title")
                db.add(paper)
                db.commit()

                authors = hit.get("authors") or []
                for idx, a in enumerate(authors[:8]):
                    external_id = str(a.get("id") or "")
                    name = a.get("name") or ""
                    existing = db.query(Author).filter(Author.source == "openalex", Author.external_id == external_id).first()
                    if not existing:
                        existing = Author(source="openalex", external_id=external_id, name=name, affiliations=[a.get("affiliation")] if a.get("affiliation") else None)
                        db.add(existing)
                        db.commit()
                        db.refresh(existing)
                    link = (
                        db.query(PaperAuthor)
                        .filter(PaperAuthor.paper_id == paper.id, PaperAuthor.author_id == existing.id)
                        .first()
                    )
                    if not link:
                        db.add(PaperAuthor(paper_id=paper.id, author_id=existing.id, author_order=idx))
                        db.commit()
                    if idx < 5:
                        kb_enrich_author.delay(str(existing.id))
                        kb_embed_author.delay(str(existing.id))

                _finish_job(db, job, "done")
                return {"status": "success", "job_id": str(job.id), "enriched": True, "source": "openalex"}

            hit = hits[0]
            if hit.get("semantic_scholar_id"):
                detail = ss.get_paper(hit["semantic_scholar_id"])
                if detail:
                    hit = detail
            meta = paper.paper_metadata or {}
            meta.setdefault("semantic_scholar", {})
            meta["semantic_scholar"].update(
                {
                    "paper_id": hit.get("semantic_scholar_id"),
                    "url": hit.get("url"),
                    "citation_count": hit.get("citation_count", 0),
                    "external_ids": hit.get("external_ids") or {},
                }
            )
            paper.paper_metadata = meta
            if not paper.abstract and hit.get("abstract"):
                paper.abstract = hit.get("abstract")
            if not paper.title and hit.get("title"):
                paper.title = hit.get("title")
            db.add(paper)
            db.commit()

            if settings.PGVECTOR_ENABLED and settings.EMBEDDING_ENABLED and hit.get("semantic_scholar_id"):
                service = EmbeddingService()
                refs = ss.get_paper_references(hit["semantic_scholar_id"], limit=30)
                cits = ss.get_paper_citations(hit["semantic_scholar_id"], limit=30)
                paper_author_ids = set(
                    r[0]
                    for r in db.query(PaperAuthor.author_id).filter(PaperAuthor.paper_id == paper.id).all()
                )
                candidate_author_ids = set()
                for p in (refs or [])[:20] + (cits or [])[:20]:
                    ext = _upsert_external_paper(db, p)
                    if ext:
                        try:
                            _embed_external_paper(db, service, ext)
                        except Exception:
                            pass
                    for a in (p.get("authors") or [])[:8]:
                        aid = str(a.get("id") or "").strip()
                        aname = a.get("name") or ""
                        au = _upsert_ss_author(db, aid, aname)
                        if not au:
                            continue
                        if au.id in paper_author_ids:
                            continue
                        if au.id in candidate_author_ids:
                            continue
                        candidate_author_ids.add(au.id)
                        if len(candidate_author_ids) <= 30:
                            kb_enrich_author.delay(str(au.id))
                            kb_embed_author.delay(str(au.id))

            authors = hit.get("authors") or []
            for idx, a in enumerate(authors):
                external_id = str(a.get("id") or "")
                name = a.get("name") or ""
                if not external_id or not name:
                    continue
                existing = _upsert_ss_author(db, external_id, name)
                if not existing:
                    continue

                link = (
                    db.query(PaperAuthor)
                    .filter(PaperAuthor.paper_id == paper.id, PaperAuthor.author_id == existing.id)
                    .first()
                )
                if not link:
                    db.add(PaperAuthor(paper_id=paper.id, author_id=existing.id, author_order=idx))
                    db.commit()

                if idx < 5:
                    kb_enrich_author.delay(str(existing.id))
                    kb_embed_author.delay(str(existing.id))

            fields = hit.get("fields_of_study") or []
            for t in fields[:10]:
                name = str(t).strip()
                if not name:
                    continue
                topic = db.query(Topic).filter(Topic.name == name).first()
                if not topic:
                    topic = Topic(name=name)
                    db.add(topic)
                    db.commit()
                    db.refresh(topic)
                existing = (
                    db.query(PaperTopic)
                    .filter(PaperTopic.paper_id == paper.id, PaperTopic.topic_id == topic.id, PaperTopic.source == "semantic_scholar")
                    .first()
                )
                if not existing:
                    db.add(PaperTopic(paper_id=paper.id, topic_id=topic.id, source="semantic_scholar", confidence=None))
                    db.commit()

            _finish_job(db, job, "done")
            return {"status": "success", "job_id": str(job.id), "enriched": True}
        except Exception as e:
            _add_event(db, job.id, "error", "enrich failed", {"error": str(e)})
            _finish_job(db, job, "failed", str(e))
            return {"status": "failed", "job_id": str(job.id), "error": str(e)}


@shared_task(name="kb_embed_paper")
def kb_embed_paper(paper_id: str) -> Dict[str, Any]:
    service = EmbeddingService()
    with SessionLocal() as db:
        job = _create_job(db, job_type="kb_embed_paper", target_type="paper", target_id=uuid.UUID(paper_id))
        try:
            paper = db.query(Paper).filter(Paper.id == uuid.UUID(paper_id)).first()
            if not paper:
                raise RuntimeError("paper not found")
            text = f"{paper.title or ''}\n\n{paper.abstract or ''}".strip()
            if not text:
                _add_event(db, job.id, "warn", "empty paper text, skip embedding")
                _finish_job(db, job, "done")
                return {"status": "success", "job_id": str(job.id), "embedded": False}

            h = service.content_hash(text)
            existing = (
                db.query(Embedding)
                .filter(Embedding.object_type == "paper", Embedding.object_id == paper.id, Embedding.model == service.model)
                .first()
            )
            if existing and existing.content_hash == h and existing.vector is not None:
                _finish_job(db, job, "done")
                return {"status": "success", "job_id": str(job.id), "embedded": True, "cached": True}

            if not settings.EMBEDDING_ENABLED:
                _add_event(db, job.id, "warn", "embedding disabled, skip", {"provider": service.provider})
                _finish_job(db, job, "done")
                return {"status": "success", "job_id": str(job.id), "embedded": False}

            vec = service.embed_text(text)
            if not existing:
                existing = Embedding(object_type="paper", object_id=paper.id, model=service.model, dim=len(vec))
            existing.dim = len(vec)
            existing.vector = vec
            existing.vector_jsonb = vec
            existing.content_hash = h
            db.add(existing)
            db.commit()

            _finish_job(db, job, "done")
            return {"status": "success", "job_id": str(job.id), "embedded": True, "cached": False}
        except Exception as e:
            _add_event(db, job.id, "error", "embed failed", {"error": str(e)})
            _finish_job(db, job, "failed", str(e))
            return {"status": "failed", "job_id": str(job.id), "error": str(e)}


@shared_task(name="kb_enrich_author")
def kb_enrich_author(author_uuid: str) -> Dict[str, Any]:
    ss = SemanticScholarCrawler(api_key=settings.SEMANTIC_SCHOLAR_API_KEY, delay=max(3.0, float(settings.CRAWLER_DELAY or 3)))
    oa = OpenAlexCrawler()
    with SessionLocal() as db:
        job = _create_job(db, job_type="kb_enrich_author", target_type="author", target_id=uuid.UUID(author_uuid))
        try:
            author = db.query(Author).filter(Author.id == uuid.UUID(author_uuid)).first()
            if not author:
                raise RuntimeError("author not found")
            if not author.external_id:
                _add_event(db, job.id, "warn", "missing author external_id", {"source": author.source})
                _finish_job(db, job, "done")
                return {"status": "success", "job_id": str(job.id), "enriched": False}

            if author.raw_profile and (author.raw_profile.get("author") or {}).get("id"):
                top = author.raw_profile.get("top_papers") or []
                if top and isinstance(top, list) and isinstance(top[0], dict) and top[0].get("authors"):
                    _finish_job(db, job, "done")
                    return {"status": "success", "job_id": str(job.id), "enriched": True, "cached": True}

            if author.source == "semantic_scholar":
                a = ss.get_author(author.external_id)
                if not a:
                    _add_event(db, job.id, "warn", "author not found in semantic scholar", {"external_id": author.external_id})
                    _finish_job(db, job, "done")
                    return {"status": "success", "job_id": str(job.id), "enriched": False}
                papers = ss.get_author_papers(author.external_id, limit=20)
            elif author.source == "openalex":
                a = oa.get_author(author.external_id)
                if not a:
                    _add_event(db, job.id, "warn", "author not found in openalex", {"external_id": author.external_id})
                    _finish_job(db, job, "done")
                    return {"status": "success", "job_id": str(job.id), "enriched": False}
                papers = oa.get_author_works(author.external_id, per_page=20)
            else:
                _add_event(db, job.id, "warn", "unsupported author source for enrich", {"source": author.source})
                _finish_job(db, job, "done")
                return {"status": "success", "job_id": str(job.id), "enriched": False}

            author.name = a.get("name") or author.name
            author.affiliations = a.get("affiliations")
            author.url = a.get("url")
            author.homepage = a.get("homepage")
            author.h_index = a.get("h_index")
            author.citation_count = a.get("citation_count")
            author.paper_count = a.get("paper_count")
            author.raw_profile = {"author": a, "top_papers": papers[:10]}
            db.add(author)
            db.commit()

            if settings.PGVECTOR_ENABLED and settings.EMBEDDING_ENABLED:
                service = EmbeddingService()
                coauthor_ids = set()
                for p in papers[:8]:
                    ext = _upsert_external_paper(db, p)
                    if ext:
                        try:
                            _embed_external_paper(db, service, ext)
                        except Exception:
                            pass
                    for ca in (p.get("authors") or [])[:10]:
                        cid = str(ca.get("id") or "").strip()
                        cname = ca.get("name") or ""
                        if not cid or not cname:
                            continue
                        au = _upsert_ss_author(db, cid, cname)
                        if not au:
                            continue
                        if au.id == author.id:
                            continue
                        if au.id in coauthor_ids:
                            continue
                        coauthor_ids.add(au.id)
                        if len(coauthor_ids) <= 20:
                            kb_enrich_author.delay(str(au.id))
                            kb_embed_author.delay(str(au.id))

            _finish_job(db, job, "done")
            return {"status": "success", "job_id": str(job.id), "enriched": True, "cached": False}
        except Exception as e:
            _add_event(db, job.id, "error", "author enrich failed", {"error": str(e)})
            _finish_job(db, job, "failed", str(e))
            return {"status": "failed", "job_id": str(job.id), "error": str(e)}


@shared_task(name="kb_embed_author")
def kb_embed_author(author_uuid: str) -> Dict[str, Any]:
    service = EmbeddingService()
    with SessionLocal() as db:
        job = _create_job(db, job_type="kb_embed_author", target_type="author", target_id=uuid.UUID(author_uuid))
        try:
            author = db.query(Author).filter(Author.id == uuid.UUID(author_uuid)).first()
            if not author:
                raise RuntimeError("author not found")

            if not settings.EMBEDDING_ENABLED:
                _add_event(db, job.id, "warn", "embedding disabled, skip", {"provider": service.provider})
                _finish_job(db, job, "done")
                return {"status": "success", "job_id": str(job.id), "embedded": False}

            raw = author.raw_profile or {}
            top_papers = raw.get("top_papers") or []
            top_titles = [p.get("title") for p in top_papers if isinstance(p, dict) and p.get("title")]
            aff = ""
            if isinstance(author.affiliations, list) and author.affiliations:
                aff = str(author.affiliations[0])
            text = "\n".join(
                [
                    f"Name: {author.name}",
                    f"Affiliation: {aff}" if aff else "",
                    f"Metrics: h-index={author.h_index}, citations={author.citation_count}, papers={author.paper_count}",
                    "Representative works:",
                    *[f"- {t}" for t in top_titles[:8]],
                ]
            ).strip()
            if not text:
                _add_event(db, job.id, "warn", "empty author text, skip embedding")
                _finish_job(db, job, "done")
                return {"status": "success", "job_id": str(job.id), "embedded": False}

            h = service.content_hash(text)
            existing = (
                db.query(Embedding)
                .filter(Embedding.object_type == "author", Embedding.object_id == author.id, Embedding.model == service.model)
                .first()
            )
            if existing and existing.content_hash == h and existing.vector is not None:
                _finish_job(db, job, "done")
                return {"status": "success", "job_id": str(job.id), "embedded": True, "cached": True}

            vec = service.embed_text(text)
            if not existing:
                existing = Embedding(object_type="author", object_id=author.id, model=service.model, dim=len(vec))
            existing.dim = len(vec)
            existing.vector = vec
            existing.vector_jsonb = vec
            existing.content_hash = h
            db.add(existing)
            db.commit()

            _finish_job(db, job, "done")
            return {"status": "success", "job_id": str(job.id), "embedded": True, "cached": False}
        except Exception as e:
            _add_event(db, job.id, "error", "author embed failed", {"error": str(e)})
            _finish_job(db, job, "failed", str(e))
            return {"status": "failed", "job_id": str(job.id), "error": str(e)}


@shared_task(name="kb_seed_domain_experts")
def kb_seed_domain_experts(domain_query: str, per_page: int = 25, max_authors: int = 200) -> Dict[str, Any]:
    oa = OpenAlexCrawler()
    with SessionLocal() as db:
        job = _create_job(db, job_type="kb_seed_domain_experts", target_type="domain", target_id=None)
        try:
            query = (domain_query or "").strip()
            if len(query) < 3:
                _add_event(db, job.id, "warn", "empty domain query, skip")
                _finish_job(db, job, "done")
                return {"status": "success", "job_id": str(job.id), "seeded": 0}

            works = oa.search_works(query, per_page=min(int(per_page or 25), 25))
            if not works:
                _add_event(db, job.id, "warn", "no works found from openalex", {"query": query})
                _finish_job(db, job, "done")
                return {"status": "success", "job_id": str(job.id), "seeded": 0}

            seen = set()
            seeded = 0
            for w in works:
                for a in (w.get("authors") or [])[:50]:
                    ext = str(a.get("id") or "").strip()
                    name = (a.get("name") or "").strip()
                    if not ext or not name:
                        continue
                    if ext in seen:
                        continue
                    seen.add(ext)

                    author = db.query(Author).filter(Author.source == "openalex", Author.external_id == ext).first()
                    if not author:
                        aff = (a.get("affiliation") or "").strip()
                        author = Author(
                            source="openalex",
                            external_id=ext,
                            name=name,
                            affiliations=[aff] if aff else None,
                        )
                        db.add(author)
                        db.commit()
                        db.refresh(author)
                        seeded += 1

                    kb_enrich_author.delay(str(author.id))
                    kb_embed_author.delay(str(author.id))

                    if seeded >= int(max_authors or 200):
                        break
                if seeded >= int(max_authors or 200):
                    break

            _add_event(db, job.id, "info", "seeded domain experts", {"query": query, "seeded": seeded})
            _finish_job(db, job, "done")
            return {"status": "success", "job_id": str(job.id), "seeded": seeded}
        except Exception as e:
            _add_event(db, job.id, "error", "seed domain experts failed", {"error": str(e), "query": domain_query})
            _finish_job(db, job, "failed", str(e))
            return {"status": "failed", "job_id": str(job.id), "error": str(e)}


@shared_task(name="kb_sync_paper_graph")
def kb_sync_paper_graph(paper_id: str) -> Dict[str, Any]:
    with SessionLocal() as db:
        job = _create_job(db, job_type="kb_sync_paper_graph", target_type="paper", target_id=uuid.UUID(paper_id))
        try:
            paper = db.query(Paper).filter(Paper.id == uuid.UUID(paper_id)).first()
            if not paper:
                raise RuntimeError("paper not found")

            meta = paper.paper_metadata or {}
            ss_meta = meta.get("semantic_scholar") or {}

            neo4j = get_neo4j()
            graph = GraphService(neo4j)
            ok = graph.add_paper(
                {
                    "id": str(paper.id),
                    "title": paper.title or paper.filename,
                    "abstract": paper.abstract,
                    "year": None,
                    "venue": None,
                    "arxiv_id": (ss_meta.get("external_ids") or {}).get("ArXiv"),
                    "doi": (ss_meta.get("external_ids") or {}).get("DOI"),
                    "citations": ss_meta.get("citation_count") or 0,
                    "keywords": [],
                }
            )
            if not ok:
                _add_event(db, job.id, "warn", "graph add_paper returned false")

            _finish_job(db, job, "done")
            return {"status": "success", "job_id": str(job.id)}
        except Exception as e:
            _add_event(db, job.id, "error", "graph sync failed", {"error": str(e)})
            _finish_job(db, job, "failed", str(e))
            return {"status": "failed", "job_id": str(job.id), "error": str(e)}
