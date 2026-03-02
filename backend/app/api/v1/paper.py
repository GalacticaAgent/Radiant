"""
论文管理 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, BackgroundTasks, Form
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
import os

from app.db.postgres import SessionLocal, get_db
from app.models.user import User
from app.api.deps import get_current_user, get_llm_service, get_graph_service
from app.services.paper_service import PaperService
from app.services.reviewer_service import ReviewerService
from app.services.virtual_reviewer_service import VirtualReviewerService
from app.services.llm_service import LLMService
from app.services.graph_service import GraphService
from app.models.reviewer import VirtualReviewer
from app.models.paper import Paper, PaperReview
from app.models.kb import CrawlJob, Embedding, Author, PaperAuthor, ExternalPaper
from app.schemas.kb import JobStatusResponse, CrawlJobResponse, SimilarPapersResponse
from app.tasks.kb_tasks import kb_ingest_paper, kb_enrich_author, kb_embed_author, kb_seed_domain_experts
from app.core.config import settings
import threading
from app.core.config import settings
from app.schemas.paper import (
    PaperUploadResponse,
    PaperResponse,
    PaperListResponse,
    ReviewerRecommendationResponse,
    ReviewerRecommendation,
    ReviewerCandidateResponse,
    ReviewerCandidate,
    ReviewerCandidatePaper,
    GenerateReviewRequest,
    ReviewResponse,
    ReviewListResponse,
    SuggestionsResponse,
    ModificationSuggestion,
    VersionListResponse,
    VersionResponse,
    PaperPolishRequest,
    PaperPolishResponse,
    PaperReviewReportResponse,
    FormatReviewRequest,
    PaperFormatReviewResponse,
    AdhocFormatReviewResponse,
    SeedDomainExpertsRequest,
    SeedDomainExpertsResponse,
)

router = APIRouter(tags=["papers"])


def get_reviewer_service(
    llm_service: LLMService = Depends(get_llm_service),
    graph_service: GraphService = Depends(get_graph_service)
) -> ReviewerService:
    """获取审稿人服务"""
    return ReviewerService(llm_service, graph_service)


def get_virtual_reviewer_service(
    reviewer_service: ReviewerService = Depends(get_reviewer_service),
) -> VirtualReviewerService:
    return VirtualReviewerService(reviewer_service)


@router.post("/upload", response_model=PaperUploadResponse, status_code=201)
async def upload_paper(
    file: UploadFile = File(..., description="论文文件（PDF/DOCX/DOC）"),
    title: Optional[str] = Query(None, description="论文标题"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传论文

    - **file**: PDF论文文件
    - **title**: 论文标题（可选，默认为文件名）
    """
    # 验证文件类型
    lower = (file.filename or "").lower()
    if not (lower.endswith('.pdf') or lower.endswith('.docx') or lower.endswith('.doc')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 PDF/DOCX/DOC 文件格式"
        )

    # 验证文件大小（最大50MB）
    from app.core.config import settings
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件过大，最大允许 {settings.MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB"
        )

    try:
        # 读取文件内容
        file_content = await file.read()

        paper = await run_in_threadpool(
            PaperService.save_paper,
            db=db,
            user_id=str(current_user.id),
            filename=file.filename,
            file_content=file_content,
            title=title
        )

        return PaperUploadResponse(
            id=str(paper.id),
            filename=paper.filename,
            title=paper.title,
            file_size=paper.file_size,
            version=paper.version,
            created_at=paper.created_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败: {str(e)}"
        )


@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(
    paper_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取论文详细信息

    - **paper_id**: 论文ID
    """
    paper = PaperService.get_paper(db, paper_id, str(current_user.id))

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在"
        )

    return PaperResponse.from_orm(paper)


@router.get("", response_model=PaperListResponse)
def list_papers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的论文列表

    - **skip**: 跳过数量
    - **limit**: 返回数量限制
    """
    papers = PaperService.get_user_papers(
        db=db,
        user_id=str(current_user.id),
        skip=skip,
        limit=limit
    )

    return PaperListResponse(
        papers=[PaperResponse.from_orm(p) for p in papers],
        total=len(papers)
    )


@router.get("/{paper_id}/reviewers", response_model=ReviewerRecommendationResponse)
def recommend_reviewers(
    paper_id: str,
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    reviewer_service: ReviewerService = Depends(get_reviewer_service)
):
    """
    推荐审稿人

    - **paper_id**: 论文ID
    - **limit**: 推荐数量

    基于论文内容自动推荐相关领域的审稿人
    """
    # 获取论文
    paper = PaperService.get_paper(db, paper_id, str(current_user.id))
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在"
        )

    # 推荐审稿人
    recommendations = reviewer_service.recommend_reviewers(
        paper_content=paper.content,
        paper_title=paper.title,
        limit=limit
    )

    return ReviewerRecommendationResponse(
        reviewers=[
            ReviewerRecommendation(
                id=r["id"],
                name=r.get("name", "Unknown"),
                affiliation=r.get("affiliation", ""),
                research_interests=r.get("research_interests", []),
                h_index=r.get("h_index", 0),
                match_count=r.get("match_count", 0),
                matched_keywords=r.get("matched_keywords", [])
            )
            for r in recommendations
        ],
        total=len(recommendations)
    )


@router.get("/{paper_id}/reviewer-candidates", response_model=ReviewerCandidateResponse)
def get_reviewer_candidates(
    paper_id: str,
    background_tasks: BackgroundTasks,
    limit: int = Query(default=5, ge=1, le=10),
    refresh: bool = Query(default=False),
    fallback_to_llm: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    virtual_reviewer_service: VirtualReviewerService = Depends(get_virtual_reviewer_service),
):
    paper = PaperService.get_paper(db, paper_id, str(current_user.id))
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="论文不存在")

    paper_uuid = uuid.UUID(paper_id)
    if not refresh:
        cached = virtual_reviewer_service._get_cached_candidates(db, paper_uuid, limit, ttl_hours=72)
        if cached:
            return ReviewerCandidateResponse(
                candidates=[
                    ReviewerCandidate(
                        id=c["id"],
                        name=c.get("name", ""),
                        affiliation=c.get("affiliation", ""),
                        h_index=c.get("h_index", 0),
                        citation_count=c.get("citation_count", 0),
                        paper_count=c.get("paper_count", 0),
                        match_score=c.get("match_score", 0),
                        matched_keywords=c.get("matched_keywords", []) or [],
                        rationale=c.get("rationale"),
                        source=c.get("source", ""),
                        external_id=c.get("external_id", ""),
                        top_papers=[
                            ReviewerCandidatePaper(
                                paper_id=p.get("paper_id"),
                                title=p.get("title"),
                                abstract=p.get("abstract"),
                                year=p.get("year"),
                                venue=p.get("venue"),
                                citation_count=p.get("citation_count", 0),
                                url=p.get("url"),
                            )
                            for p in (c.get("top_papers") or [])
                        ],
                    )
                    for c in cached
                ],
                total=len(cached),
            )
        if settings.PGVECTOR_ENABLED:
            paper_emb = (
                db.query(Embedding)
                .filter(Embedding.object_type == "paper", Embedding.object_id == paper_uuid, Embedding.vector.isnot(None))
                .order_by(Embedding.updated_at.desc())
                .first()
            )
            if not paper_emb or paper_emb.vector is None:
                running = (
                    db.query(CrawlJob)
                    .filter(
                        CrawlJob.target_type == "paper",
                        CrawlJob.target_id == paper_uuid,
                        CrawlJob.status.in_(["queued", "running"]),
                    )
                    .count()
                    > 0
                )
                if not running:
                    try:
                        if background_tasks is not None:
                            background_tasks.add_task(kb_ingest_paper.delay, paper_id)
                    except Exception:
                        pass
                if not fallback_to_llm and background_tasks is not None:
                    def _bg_generate():
                        with SessionLocal() as db2:
                            p2 = PaperService.get_paper(db2, paper_id, str(current_user.id))
                            if p2:
                                virtual_reviewer_service.get_or_generate_candidates(db=db2, paper=p2, limit=limit, refresh=True)

                    background_tasks.add_task(_bg_generate)
                    candidates = []
                else:
                    candidates = virtual_reviewer_service.get_or_generate_candidates(db=db, paper=paper, limit=limit, refresh=refresh)
            else:
                distance = Embedding.vector.cosine_distance(paper_emb.vector).label("distance")
                author_rows = (
                    db.query(Author, distance)
                    .join(Embedding, Embedding.object_id == Author.id)
                    .filter(
                        Embedding.object_type == "author",
                        Embedding.vector.isnot(None),
                        Author.source.in_(["semantic_scholar", "openalex"]),
                        ~db.query(PaperAuthor)
                        .filter(PaperAuthor.paper_id == paper_uuid, PaperAuthor.author_id == Author.id)
                        .exists(),
                    )
                    .order_by(distance.asc())
                    .limit(limit)
                    .all()
                )
                if author_rows:
                    author_ids = [a.id for a, _ in author_rows]
                    running_ids = set(
                        r[0]
                        for r in db.query(CrawlJob.target_id)
                        .filter(
                            CrawlJob.target_type == "author",
                            CrawlJob.target_id.in_(author_ids),
                            CrawlJob.status.in_(["queued", "running"]),
                        )
                        .all()
                    )
                    kb_candidates = []
                    for a, d in author_rows:
                        if not a.raw_profile and a.id not in running_ids:
                            if background_tasks is not None:
                                background_tasks.add_task(kb_enrich_author.delay, str(a.id))
                                background_tasks.add_task(kb_embed_author.delay, str(a.id))
                        try:
                            score = max(0.0, 1.0 - float(d))
                        except Exception:
                            score = 0.0
                        affiliations = a.affiliations or []
                        aff = ""
                        if isinstance(affiliations, list) and affiliations:
                            aff = str(affiliations[0])
                        raw = a.raw_profile or {}
                        top_papers = raw.get("top_papers") or []
                        kb_candidates.append(
                            {
                                "id": f"kb:author:{a.id}",
                                "name": a.name,
                                "affiliation": aff,
                                "h_index": a.h_index or 0,
                                "citation_count": a.citation_count or 0,
                                "paper_count": a.paper_count or 0,
                                "match_score": int(score * 1000),
                                "matched_keywords": [],
                                "rationale": f"向量相似度 {score:.3f}",
                                "source": "kb",
                                "external_id": f"{a.source}:{a.external_id}",
                                "top_papers": top_papers[:8] if isinstance(top_papers, list) else [],
                            }
                        )
                    candidates = kb_candidates
                else:
                    if not fallback_to_llm and background_tasks is not None:
                        def _bg_generate():
                            with SessionLocal() as db2:
                                p2 = PaperService.get_paper(db2, paper_id, str(current_user.id))
                                if p2:
                                    virtual_reviewer_service.get_or_generate_candidates(db=db2, paper=p2, limit=limit, refresh=True)

                        background_tasks.add_task(_bg_generate)
                        candidates = []
                    else:
                        candidates = virtual_reviewer_service.get_or_generate_candidates(db=db, paper=paper, limit=limit, refresh=refresh)
        else:
            if not fallback_to_llm and background_tasks is not None:
                def _bg_generate():
                    with SessionLocal() as db2:
                        p2 = PaperService.get_paper(db2, paper_id, str(current_user.id))
                        if p2:
                            virtual_reviewer_service.get_or_generate_candidates(db=db2, paper=p2, limit=limit, refresh=True)

                background_tasks.add_task(_bg_generate)
                candidates = []
            else:
                candidates = virtual_reviewer_service.get_or_generate_candidates(db=db, paper=paper, limit=limit, refresh=refresh)
    else:
        candidates = virtual_reviewer_service.get_or_generate_candidates(db=db, paper=paper, limit=limit, refresh=refresh)

    return ReviewerCandidateResponse(
        candidates=[
            ReviewerCandidate(
                id=c["id"],
                name=c.get("name", ""),
                affiliation=c.get("affiliation", ""),
                h_index=c.get("h_index", 0),
                citation_count=c.get("citation_count", 0),
                paper_count=c.get("paper_count", 0),
                match_score=c.get("match_score", 0),
                matched_keywords=c.get("matched_keywords", []) or [],
                rationale=c.get("rationale"),
                source=c.get("source", ""),
                external_id=c.get("external_id", ""),
                top_papers=[
                    ReviewerCandidatePaper(
                        paper_id=p.get("paper_id"),
                        title=p.get("title"),
                        abstract=p.get("abstract"),
                        year=p.get("year"),
                        venue=p.get("venue"),
                        citation_count=p.get("citation_count", 0),
                        url=p.get("url"),
                    )
                    for p in (c.get("top_papers") or [])
                ],
            )
            for c in candidates
        ],
        total=len(candidates),
    )


@router.get("/{paper_id}/reviewer-candidates/status", response_model=JobStatusResponse)
def get_reviewer_candidates_status(
    paper_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paper = PaperService.get_paper(db, paper_id, str(current_user.id))
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="论文不存在")

    jobs = (
        db.query(CrawlJob)
        .filter(CrawlJob.target_type == "paper", CrawlJob.target_id == uuid.UUID(paper_id))
        .order_by(CrawlJob.created_at.desc())
        .limit(20)
        .all()
    )

    status_value = "empty"
    if jobs:
        status_value = jobs[0].status

    return JobStatusResponse(status=status_value, jobs=[CrawlJobResponse.from_orm(j) for j in jobs])


@router.get("/{paper_id}/similar-papers", response_model=SimilarPapersResponse)
def get_similar_papers(
    paper_id: str,
    top_k: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paper = PaperService.get_paper(db, paper_id, str(current_user.id))
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="论文不存在")

    if not settings.PGVECTOR_ENABLED:
        return SimilarPapersResponse(paper_id=paper_id, items=[], total=0)

    emb = (
        db.query(Embedding)
        .filter(Embedding.object_type == "paper", Embedding.object_id == uuid.UUID(paper_id))
        .order_by(Embedding.updated_at.desc())
        .first()
    )
    if not emb or emb.vector is None:
        return SimilarPapersResponse(paper_id=paper_id, items=[], total=0)

    distance = Embedding.vector.cosine_distance(emb.vector).label("distance")
    ext_rows = (
        db.query(ExternalPaper, distance)
        .join(Embedding, Embedding.object_id == ExternalPaper.id)
        .filter(Embedding.object_type == "external_paper", Embedding.vector.isnot(None))
        .order_by(distance.asc())
        .limit(top_k)
        .all()
    )
    items = []
    for p, d in ext_rows:
        try:
            score = 1.0 - float(d)
        except Exception:
            score = 0.0
        items.append({"paper_id": f"{p.source}:{p.external_id}", "title": p.title, "score": score})

    if not items:
        local_rows = (
            db.query(Paper, distance)
            .join(Embedding, Paper.id == Embedding.object_id)
            .filter(Embedding.object_type == "paper", Embedding.object_id != uuid.UUID(paper_id), Embedding.vector.isnot(None))
            .order_by(distance.asc())
            .limit(top_k)
            .all()
        )
        for p, d in local_rows:
            try:
                score = 1.0 - float(d)
            except Exception:
                score = 0.0
            items.append({"paper_id": str(p.id), "title": p.title or p.filename, "score": score})

    return SimilarPapersResponse(paper_id=paper_id, items=items, total=len(items))


@router.post("/{paper_id}/kb/ingest")
def trigger_kb_ingest(
    paper_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paper = PaperService.get_paper(db, paper_id, str(current_user.id))
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="论文不存在")
    running = (
        db.query(CrawlJob)
        .filter(
            CrawlJob.target_type == "paper",
            CrawlJob.target_id == uuid.UUID(paper_id),
            CrawlJob.status.in_(["queued", "running"]),
        )
        .count()
        > 0
    )
    if running:
        return {"status": "already_running"}
    try:
        if getattr(settings, "CELERY_RUN_INLINE", False):
            threading.Thread(target=kb_ingest_paper, args=(paper_id,), daemon=True).start()
            return {"status": "running"}
        async_result = kb_ingest_paper.delay(paper_id)
        return {"status": "queued", "task_id": async_result.id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"任务投递失败: {str(e)}")


@router.post("/kb/seed-domain-experts", response_model=SeedDomainExpertsResponse)
def seed_domain_experts(
    payload: SeedDomainExpertsRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        if getattr(settings, "CELERY_RUN_INLINE", False):
            threading.Thread(target=kb_seed_domain_experts, args=(payload.query, payload.per_page, payload.max_authors), daemon=True).start()
            return SeedDomainExpertsResponse(status="running")
        async_result = kb_seed_domain_experts.delay(payload.query, payload.per_page, payload.max_authors)
        return SeedDomainExpertsResponse(status="queued", task_id=async_result.id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"任务投递失败: {str(e)}")


@router.post("/{paper_id}/review", response_model=ReviewListResponse)
def generate_reviews(
    paper_id: str,
    request: GenerateReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    reviewer_service: ReviewerService = Depends(get_reviewer_service)
):
    """
    生成审稿意见

    - **paper_id**: 论文ID
    - **reviewer_ids**: 审稿人ID列表

    为指定审稿人生成审稿意见
    """
    # 获取论文
    paper = PaperService.get_paper(db, paper_id, str(current_user.id))
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在"
        )

    reviews = []

    try:
        for reviewer_id in request.reviewer_ids:
            reviewer_name = f"Reviewer_{reviewer_id[:8]}"
            reviewer_profile = ""
            if reviewer_id.startswith("vr:"):
                vr_id = reviewer_id.split("vr:", 1)[1]
                vr = db.query(VirtualReviewer).filter(VirtualReviewer.id == uuid.UUID(vr_id)).first()
                if not vr:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="审稿人不存在或已过期")
                reviewer_name = vr.name or reviewer_name
                reviewer_profile = vr.profile_text or ""
                if not reviewer_profile:
                    reviewer_profile = f"Name: {reviewer_name}\nAffiliation: {vr.affiliation or 'N/A'}"
            elif reviewer_id.startswith("kb:author:"):
                author_id = reviewer_id.split("kb:author:", 1)[1]
                a = db.query(Author).filter(Author.id == uuid.UUID(author_id)).first()
                if not a:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="审稿人不存在或已过期")
                reviewer_name = a.name or reviewer_name
                affiliations = a.affiliations or []
                aff = ""
                if isinstance(affiliations, list) and affiliations:
                    aff = str(affiliations[0])
                raw = a.raw_profile or {}
                top_papers = raw.get("top_papers") or []
                top_titles = [p.get("title") for p in top_papers if isinstance(p, dict) and p.get("title")]
                lines = [
                    f"Name: {reviewer_name}",
                    f"Affiliation: {aff}" if aff else "Affiliation: N/A",
                    f"Metrics: h-index={a.h_index}, citations={a.citation_count}, papers={a.paper_count}",
                ]
                if top_titles:
                    lines.append("Representative works:")
                    lines.extend([f"- {t}" for t in top_titles[:6]])
                lines.append("Review style: Focus on methodology soundness, dataset validity, and reproducibility; compare to strong baselines; highlight concrete fixes.")
                reviewer_profile = "\n".join([x for x in lines if x]).strip()
            else:
                reviewer_profile = reviewer_service.generate_reviewer_profile(
                    reviewer_id=reviewer_id,
                    reviewer_name=reviewer_name
                )

            # 生成审稿意见
            review_dict = reviewer_service.generate_review(
                paper_content=paper.content,
                reviewer_profile=reviewer_profile,
                reviewer_name=reviewer_name,
                paper_title=paper.title
            )

            # 保存到数据库
            review = PaperService.save_review(
                db=db,
                paper_id=paper_id,
                user_id=str(current_user.id),
                reviewer_id=reviewer_id,
                reviewer_name=review_dict.get("reviewer_name", reviewer_name),
                reviewer_profile=reviewer_profile,
                review_content=review_dict.get("review_content", ""),
                rating=review_dict.get("rating"),
                review_metadata={
                    "confidence": review_dict.get("confidence"),
                    "recommendation": review_dict.get("recommendation"),
                }
                if (review_dict.get("confidence") or review_dict.get("recommendation"))
                else None,
                strengths=review_dict.get("strengths"),
                weaknesses=review_dict.get("weaknesses"),
                suggestions=review_dict.get("suggestions")
            )

            reviews.append(review)

        def to_response(r: PaperReview) -> ReviewResponse:
            meta = r.review_metadata or {}
            conf = meta.get("confidence") if isinstance(meta, dict) else None
            return ReviewResponse(
                id=r.id,
                paper_id=r.paper_id,
                reviewer_id=r.reviewer_id,
                reviewer_name=r.reviewer_name or "",
                reviewer_profile=r.reviewer_profile or "",
                review_content=r.review_content or "",
                rating=r.rating,
                confidence=conf,
                strengths=r.strengths,
                weaknesses=r.weaknesses,
                suggestions=r.suggestions,
                created_at=r.created_at,
            )

        return ReviewListResponse(reviews=[to_response(r) for r in reviews], total=len(reviews))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成审稿意见失败: {str(e)}"
        )


@router.get("/{paper_id}/reviews", response_model=ReviewListResponse)
def get_paper_reviews(
    paper_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取论文的审稿意见列表

    - **paper_id**: 论文ID
    """
    # 验证论文所有权
    paper = PaperService.get_paper(db, paper_id, str(current_user.id))
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在"
        )

    reviews = PaperService.get_paper_reviews(
        db=db,
        paper_id=paper_id,
        user_id=str(current_user.id)
    )

    def to_response(r: PaperReview) -> ReviewResponse:
        meta = r.review_metadata or {}
        conf = meta.get("confidence") if isinstance(meta, dict) else None
        return ReviewResponse(
            id=r.id,
            paper_id=r.paper_id,
            reviewer_id=r.reviewer_id,
            reviewer_name=r.reviewer_name or "",
            reviewer_profile=r.reviewer_profile or "",
            review_content=r.review_content or "",
            rating=r.rating,
            confidence=conf,
            strengths=r.strengths,
            weaknesses=r.weaknesses,
            suggestions=r.suggestions,
            created_at=r.created_at,
        )

    return ReviewListResponse(reviews=[to_response(r) for r in reviews], total=len(reviews))


@router.post("/{paper_id}/suggestions", response_model=SuggestionsResponse)
def generate_suggestions(
    paper_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    reviewer_service: ReviewerService = Depends(get_reviewer_service)
):
    """
    基于审稿意见生成修改建议

    - **paper_id**: 论文ID

    需要先有审稿意见，根据审稿意见生成具体的修改建议
    """
    # 获取论文
    paper = PaperService.get_paper(db, paper_id, str(current_user.id))
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文不存在"
        )

    # 获取审稿意见
    reviews = PaperService.get_paper_reviews(db, paper_id, str(current_user.id))
    if not reviews:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有审稿意见，请先生成审稿意见"
        )

    # 生成修改建议
    suggestions = reviewer_service.generate_modification_suggestions(
        paper_content=paper.content,
        reviews=[
            {
                "weaknesses": r.weaknesses or [],
                "suggestions": r.suggestions or []
            }
            for r in reviews
        ],
        paper_title=paper.title
    )

    return SuggestionsResponse(
        suggestions=[
            ModificationSuggestion(
                section=s.get("section", ""),
                issue=s.get("issue", ""),
                suggestion=s.get("suggestion", ""),
                priority=s.get("priority", "中")
            )
            for s in suggestions
        ],
        total=len(suggestions)
    )


@router.post("/{paper_id}/version", response_model=PaperUploadResponse, status_code=201)
async def upload_paper_version(
    paper_id: str,
    file: UploadFile = File(...),
    title: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传新版本论文

    - **paper_id**: 原始论文ID
    - **file**: 新版本的PDF文件

    创建论文的新版本，保持版本链接
    """
    # 验证原始论文存在
    parent_paper = PaperService.get_paper(db, paper_id, str(current_user.id))
    if not parent_paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="原始论文不存在"
        )

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持PDF文件格式"
        )

    try:
        file_content = await file.read()

        paper = await run_in_threadpool(
            PaperService.create_new_version,
            db=db,
            parent_paper_id=paper_id,
            user_id=str(current_user.id),
            filename=file.filename,
            file_content=file_content,
            title=title
        )

        return PaperUploadResponse(
            id=str(paper.id),
            filename=paper.filename,
            title=paper.title,
            file_size=paper.file_size,
            version=paper.version,
            created_at=paper.created_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败: {str(e)}"
        )


@router.get("/{paper_id}/versions", response_model=VersionListResponse)
def get_paper_versions(
    paper_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取论文的所有版本

    - **paper_id**: 论文ID

    返回该论文的所有版本历史
    """
    versions = PaperService.get_paper_versions(
        db=db,
        paper_id=paper_id,
        user_id=str(current_user.id)
    )

    if not versions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="论文版本不存在"
        )

    return VersionListResponse(
        versions=[
            VersionResponse(
                id=str(v.id),
                version=v.version,
                title=v.title,
                filename=v.filename,
                parent_id=str(v.parent_id) if v.parent_id else None,
                created_at=v.created_at
            )
            for v in versions
        ],
        current_version=max(v.version for v in versions) if versions else 1,
        total=len(versions)
    )


def _get_best_abstract(paper) -> str:
    abstract = (paper.abstract or "").strip() if paper else ""
    if abstract:
        return abstract
    meta = paper.paper_metadata or {}
    auto_abs = (meta.get("auto_extracted_abstract") or "").strip()
    if auto_abs:
        return auto_abs
    content = (paper.content or "").strip()
    if not content:
        title = (paper.title or paper.filename or "").strip()
        return title
    head = content.replace("\r\n", "\n").replace("\r", "\n")
    return head[:1200]


def _truncate_text(text: str, max_len: int) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    if len(t) <= max_len:
        return t
    return t[:max_len]


@router.post("/format-review", response_model=AdhocFormatReviewResponse)
async def adhoc_format_review(
    file: Optional[UploadFile] = File(None, description="PDF 或 DOCX"),
    text: Optional[str] = Form(None, description="直接粘贴的论文文本"),
    title: Optional[str] = Form(None, description="可选：文档标题"),
    scope: str = Form("auto", description="auto / abstract / full"),
    language: str = Form("auto", description="auto / zh / en"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    scope = (scope or "auto").strip().lower()
    if scope not in {"auto", "abstract", "full"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scope 参数不合法（auto/abstract/full）")

    content = ""
    filename = None
    source_type = "text"
    docx_style_snapshot = None

    if file is not None:
        filename = file.filename
        raw = await file.read()
        ext = os.path.splitext(filename or "")[1].lower()
        if ext == ".pdf":
            source_type = "pdf"
            content = PaperService.extract_text_from_pdf(raw)
        elif ext == ".docx":
            source_type = "docx"
            content = PaperService.extract_text_from_docx(raw)
            try:
                docx_style_snapshot = PaperService.extract_docx_style_snapshot(raw)
            except Exception:
                docx_style_snapshot = None
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 PDF 或 DOCX 文件")
    else:
        content = (text or "").strip()

    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请上传文件或粘贴文本")

    meta = PaperService.extract_metadata(content)
    doc_title = (title or "").strip()
    auto_title = (meta.get("auto_extracted_title") or "").strip() if isinstance(meta, dict) else ""
    final_title = doc_title or auto_title or (filename or "未命名文档")

    auto_abs = (meta.get("auto_extracted_abstract") or "").strip() if isinstance(meta, dict) else ""
    abstract = auto_abs[:1200].strip() if auto_abs else _truncate_text(content, 1200)

    if scope == "abstract":
        body = ""
    else:
        body = _truncate_text(content, 18000)

    try:
        result = llm_service.generate_format_review(
            paper_title=final_title,
            abstract=abstract,
            paper_content=body,
            paper_language=(language or "auto").strip().lower(),
            full_text=content,
            source_type=source_type,
            docx_style_snapshot=docx_style_snapshot,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"格式审查失败: {str(e)}")

    from datetime import datetime

    issues = result.get("issues")
    rule_issues = result.get("rule_issues")
    llm_issues = result.get("llm_issues")
    auto_metrics = result.get("auto_metrics")
    overall_grade = result.get("overall_grade")
    priority = result.get("priority")
    markdown = result.get("review_markdown") or ""

    return AdhocFormatReviewResponse(
        markdown=markdown,
        issues=issues if isinstance(issues, list) else None,
        rule_issues=rule_issues if isinstance(rule_issues, list) else None,
        llm_issues=llm_issues if isinstance(llm_issues, list) else None,
        auto_metrics=auto_metrics if isinstance(auto_metrics, dict) else None,
        overall_grade=overall_grade if isinstance(overall_grade, str) else None,
        priority=priority if isinstance(priority, str) else None,
        generated_at=datetime.utcnow(),
    )



@router.post("/{paper_id}/format-review", response_model=PaperFormatReviewResponse)
def format_review(
    paper_id: str,
    request: FormatReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    paper = PaperService.get_paper(db, paper_id, str(current_user.id))
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="论文不存在")

    scope = (request.scope or "auto").strip().lower()
    if scope not in {"auto", "abstract", "full"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scope 参数不合法（auto/abstract/full）")

    title = (paper.title or paper.filename or "").strip()
    abstract = _get_best_abstract(paper)
    raw_full = (paper.content or "").replace("\r\n", "\n").replace("\r", "\n")
    source_type = "text"
    docx_style_snapshot = None
    try:
        ext = os.path.splitext(paper.filename or "")[1].lower()
        if ext == ".pdf":
            source_type = "pdf"
        elif ext == ".docx":
            source_type = "docx"
            try:
                with open(paper.file_path, "rb") as f:
                    docx_style_snapshot = PaperService.extract_docx_style_snapshot(f.read())
            except Exception:
                docx_style_snapshot = None
    except Exception:
        source_type = "text"
    if scope == "abstract":
        content = ""
    else:
        content = _truncate_text(raw_full, 18000)

    try:
        result = llm_service.generate_format_review(
            paper_title=title,
            abstract=abstract,
            paper_content=content,
            paper_language=(request.language or "auto").strip().lower(),
            full_text=raw_full,
            source_type=source_type,
            docx_style_snapshot=docx_style_snapshot,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"格式审查失败: {str(e)}")

    from datetime import datetime

    issues = result.get("issues")
    rule_issues = result.get("rule_issues")
    llm_issues = result.get("llm_issues")
    auto_metrics = result.get("auto_metrics")
    overall_grade = result.get("overall_grade")
    priority = result.get("priority")
    markdown = result.get("review_markdown") or ""

    return PaperFormatReviewResponse(
        paper_id=paper.id,
        markdown=markdown,
        issues=issues if isinstance(issues, list) else None,
        rule_issues=rule_issues if isinstance(rule_issues, list) else None,
        llm_issues=llm_issues if isinstance(llm_issues, list) else None,
        auto_metrics=auto_metrics if isinstance(auto_metrics, dict) else None,
        overall_grade=overall_grade if isinstance(overall_grade, str) else None,
        priority=priority if isinstance(priority, str) else None,
        generated_at=datetime.utcnow(),
    )


@router.post("/{paper_id}/polish", response_model=PaperPolishResponse)
def polish_paper(
    paper_id: str,
    request: PaperPolishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    paper = PaperService.get_paper(db, paper_id, str(current_user.id))
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="论文不存在")

    original_abstract = _get_best_abstract(paper)
    if not original_abstract:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未能从论文中提取摘要内容")

    reviews = PaperService.get_paper_reviews(db, paper_id, str(current_user.id))
    if not reviews and not (request.selected_suggestions or []):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有审稿意见，请先生成审稿意见")

    applied = [s.strip() for s in (request.selected_suggestions or []) if s and s.strip()]
    if not applied:
        derived: List[str] = []
        for r in reviews:
            derived.extend(r.suggestions or [])
            derived.extend(r.weaknesses or [])
        applied = [s.strip() for s in derived if s and s.strip()][:12]

    mode = request.mode or "abstract_only"
    is_title_only = not (paper.abstract or (paper.paper_metadata or {}).get("auto_extracted_abstract") or (paper.content or "").strip())
    task_line = "基于审稿意见对摘要进行润色" if not is_title_only else "基于论文标题与审稿意见生成一段摘要草稿"
    prompt = f"""请你充当资深学术论文编辑，{task_line}。要求：
1) 只输出润色后的摘要正文，不要输出任何解释、标题、列表或前后缀
2) 保持学术风格，语言为中文（如果原摘要为英文则保持英文）
3) 不要编造不存在的实验结果/数据
4) 控制长度在 150-250 字左右（若有原摘要则与原摘要长度相当）

原摘要：
{original_abstract}

需要重点改进的点（审稿意见摘要）：
{chr(10).join([f"- {s}" for s in applied])}
"""

    try:
        polished = llm_service.chat_with_context(
            user_message=prompt,
            system_prompt="你是一位严谨的学术论文编辑，只输出润色后的摘要正文。",
            history=[],
        ).strip()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"润色失败: {str(e)}")

    import difflib
    diff_lines = difflib.unified_diff(
        original_abstract.splitlines(),
        polished.splitlines(),
        fromfile="original",
        tofile="polished",
        lineterm="",
    )
    diff = "\n".join(diff_lines)

    from datetime import datetime
    return PaperPolishResponse(
        paper_id=paper.id,
        mode=mode,
        original_abstract=original_abstract,
        polished_abstract=polished,
        diff=diff,
        applied_suggestions=applied,
        generated_at=datetime.utcnow(),
    )


@router.get("/{paper_id}/report", response_model=PaperReviewReportResponse)
def get_review_report(
    paper_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paper = PaperService.get_paper(db, paper_id, str(current_user.id))
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="论文不存在")

    reviews = PaperService.get_paper_reviews(db, paper_id, str(current_user.id))

    def join_list(items: Optional[List[str]]) -> str:
        if not items:
            return ""
        return "\n".join([f"- {x}" for x in items if x])

    def sanitize_markdown(md: str) -> str:
        import re

        text = (md or "").strip()
        if not text:
            return ""
        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        return text

    lines: List[str] = []
    lines.append("# 模拟审稿报告")
    lines.append("")
    lines.append(f"- Paper ID: {paper.id}")
    lines.append(f"- Title: {paper.title or paper.filename}")
    lines.append(f"- Version: {paper.version}")
    lines.append("")

    if paper.abstract:
        lines.append("## 摘要")
        lines.append("")
        lines.append(paper.abstract.strip())
        lines.append("")

    lines.append(f"## 审稿意见（{len(reviews)}）")
    lines.append("")
    if not reviews:
        lines.append("暂无审稿意见。")
    else:
        for idx, r in enumerate(reviews, start=1):
            lines.append(f"### Reviewer {idx}: {r.reviewer_name or 'Unknown'}")
            lines.append("")
            if r.rating is not None:
                lines.append(f"- Rating: {r.rating}/10")
            lines.append(f"- Created At: {r.created_at.isoformat()}")
            lines.append("")
            if r.review_content:
                lines.append("**Review**")
                lines.append("")
                lines.append(sanitize_markdown(r.review_content))
                lines.append("")
            strengths_md = join_list(r.strengths)
            if strengths_md:
                lines.append("**Strengths**")
                lines.append("")
                lines.append(strengths_md)
                lines.append("")
            weaknesses_md = join_list(r.weaknesses)
            if weaknesses_md:
                lines.append("**Weaknesses**")
                lines.append("")
                lines.append(weaknesses_md)
                lines.append("")
            suggestions_md = join_list(r.suggestions)
            if suggestions_md:
                lines.append("**Suggestions**")
                lines.append("")
                lines.append(suggestions_md)
                lines.append("")

    from datetime import datetime
    return PaperReviewReportResponse(
        paper_id=paper.id,
        markdown="\n".join(lines).strip() + "\n",
        generated_at=datetime.utcnow(),
    )
