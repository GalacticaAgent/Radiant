from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, graph, chat, research, idea, paper, user, private_graph
from app.api import format_review, upload, rule, system
from app.core.config import settings
from app.db.postgres import engine
from app.db.postgres import Base
from app.db.schema_check import check_schema, format_schema_issues
from sqlalchemy import text
from app.core.celery_app import celery_app as _celery_app
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uuid
import logging

app = FastAPI(
    title="Radiant API",
    description="学术研究 Agent 后端服务",
    version="0.1.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "https://ai4research.com.cn",
        "https://www.ai4research.com.cn",
        "http://ai4research.com.cn",
        "http://www.ai4research.com.cn",
    ],
    allow_origin_regex=r"^(https?://)(ai4research\.com\.cn|www\.ai4research\.com\.cn|localhost|127\.0\.0\.1|0\.0\.0\.0|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response


app.add_middleware(TraceIdMiddleware)
logger = logging.getLogger(__name__)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["知识图谱"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["对话"])
app.include_router(research.router, prefix="/api/v1/research", tags=["调研"])
app.include_router(idea.router, prefix="/api/v1/idea", tags=["Idea检验"])
app.include_router(paper.router, prefix="/api/v1/paper", tags=["论文"])
app.include_router(user.router, prefix="/api/v1/user", tags=["用户"])
app.include_router(private_graph.router, prefix="/api/v1/private-graph", tags=["私有图谱"])
app.include_router(format_review.router, prefix="/api/format-review", tags=["格式审查"])
app.include_router(upload.router, prefix="/api/upload", tags=["上传"])
app.include_router(rule.router, prefix="/api/rule", tags=["格式规则"])
app.include_router(system.router, prefix="/api/system", tags=["系统"])

@app.on_event("startup")
def validate_database_schema():
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        Base.metadata.create_all(bind=engine)
        with engine.begin() as conn:
            conn.execute(text("DROP INDEX IF EXISTS ix_format_review_sessions_session_key;"))
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_format_review_sessions_user_session_key "
                    "ON format_review_sessions (user_id, session_key);"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_format_review_sessions_session_key "
                    "ON format_review_sessions (session_key);"
                )
            )
        issues = check_schema(engine)
        if issues:
            logger.warning("Database schema check failed:\n%s", format_schema_issues(issues))
    except Exception as e:
        logger.warning("Database init skipped: %s", str(e))

@app.get("/")
async def root():
    return {
        "message": "Radiant API",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}
