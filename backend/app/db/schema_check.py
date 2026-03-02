from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

from sqlalchemy import Engine, inspect


@dataclass(frozen=True)
class SchemaIssue:
    kind: str
    name: str
    details: str


def check_schema(engine: Engine) -> List[SchemaIssue]:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    required_columns: Dict[str, Sequence[str]] = {
        "users": ["id", "username", "email", "hashed_password", "is_active", "created_at"],
        "conversations": ["id", "user_id", "session_id", "role", "content", "created_at"],
        "chat_sessions": ["id", "user_id", "title", "is_pinned", "created_at", "updated_at"],
        "papers": ["id", "user_id", "title", "filename", "file_path", "file_size", "paper_metadata", "version", "created_at"],
        "paper_reviews": ["id", "paper_id", "user_id", "review_content", "created_at"],
        "virtual_reviewers": ["id", "source", "external_id", "name", "created_at"],
        "paper_reviewer_candidates": ["id", "paper_id", "reviewer_id", "rank", "score", "created_at"],
        "authors": ["id", "source", "external_id", "name", "created_at"],
        "paper_authors": ["id", "paper_id", "author_id", "created_at"],
        "topics": ["id", "name", "created_at"],
        "paper_topics": ["id", "paper_id", "topic_id", "source", "created_at"],
        "external_papers": ["id", "source", "external_id", "title", "created_at"],
        "embeddings": ["id", "object_type", "object_id", "model", "dim", "created_at"],
        "crawl_jobs": ["id", "job_type", "target_type", "status", "created_at"],
        "crawl_events": ["id", "job_id", "level", "message", "created_at"],
    }

    issues: List[SchemaIssue] = []

    for table_name, cols in required_columns.items():
        if table_name not in existing_tables:
            issues.append(SchemaIssue(kind="missing_table", name=table_name, details="table not found"))
            continue

        try:
            existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
        except Exception as e:
            issues.append(SchemaIssue(kind="inspect_failed", name=table_name, details=str(e)))
            continue

        missing = [c for c in cols if c not in existing_cols]
        if missing:
            issues.append(
                SchemaIssue(
                    kind="missing_columns",
                    name=table_name,
                    details="missing: " + ", ".join(missing),
                )
            )

    return issues


def format_schema_issues(issues: Iterable[SchemaIssue]) -> str:
    lines = []
    for issue in issues:
        lines.append(f"- {issue.kind}: {issue.name} ({issue.details})")
    return "\n".join(lines)
