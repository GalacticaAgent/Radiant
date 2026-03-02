import datetime as dt
import os
import sys
import time
from typing import Any, Dict, Tuple

import requests


BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)


def ok_fail(value: bool) -> str:
    return "OK" if value else "FAIL"


def check_postgres() -> Tuple[bool, str]:
    try:
        from app.db.postgres import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, ""
    except Exception as e:
        return False, str(e)


def check_redis() -> Tuple[bool, str]:
    try:
        import redis
        from app.core.config import settings

        url = settings.REDIS_URL
        for attempt in range(2):
            try:
                client = redis.Redis.from_url(
                    url,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                    decode_responses=True,
                )
                ok = bool(client.ping())
                return ok, "" if ok else "ping=false"
            except redis.exceptions.AuthenticationError:
                if attempt == 0 and ":6379/" in url:
                    url = url.replace(":6379/", ":6380/")
                    continue
                raise
    except Exception as e:
        return False, str(e)


def check_neo4j() -> Tuple[bool, str]:
    try:
        from app.db.neo4j import neo4j_conn

        return bool(neo4j_conn.verify_connectivity()), ""
    except Exception as e:
        return False, str(e)


def check_backend() -> Tuple[bool, str]:
    try:
        last = None
        for i in range(5):
            r = requests.get("http://localhost:8000/health", timeout=20, headers={"Connection": "close"})
            last = r
            if r.status_code == 200:
                return True, r.text[:200]
            if i < 4:
                time.sleep(1)
        if last is None:
            return False, ""
        return False, last.text[:200]
    except Exception as e:
        return False, str(e)


def check_login() -> Tuple[bool, str]:
    try:
        r = None
        for i in range(5):
            r = requests.post(
                "http://localhost:8000/api/v1/auth/login",
                json={"username_or_email": "testuser3", "password": "password123"},
                timeout=25,
                headers={"Connection": "close"},
            )
            if r.status_code == 200:
                break
            if i < 4:
                time.sleep(1)
        if r is None:
            return False, ""
        if r.status_code == 200:
            try:
                payload = r.json()
                user_id = (payload.get("user") or {}).get("id")
                return True, f"user_id={user_id}" if user_id else "ok"
            except Exception:
                return True, "ok"
        return False, r.text[:200]
    except Exception as e:
        return False, str(e)


def build_markdown(report: Dict[str, Any]) -> str:
    ts = report["generated_at"]
    lines = [
        "# STATUS_SSOT（单一事实来源）",
        "",
        f"生成时间：{ts}",
        "",
        "## 服务连通性",
        "",
        "| 项目 | 状态 | 备注 |",
        "|---|---|---|",
    ]
    for item in report["checks"]:
        lines.append(f"| {item['name']} | {ok_fail(item['ok'])} | {item.get('detail','')} |")

    lines += [
        "",
        "## 前端真实对接页面",
        "",
        "- Chat / 会话：已对接",
        "- Research：已对接",
        "- Idea Validation：已对接",
        "- Paper Polish：已对接",
        "- Knowledge Graph：已对接",
        "- Settings（Profile/API Key）：已对接",
        "",
        "## 端到端验收脚本",
        "",
        "- backend/scripts/verify_e2e.py",
        "- backend/scripts/verify_chat.py",
        "- backend/scripts/verify_idea.py",
        "- backend/scripts/verify_polish.py",
        "- backend/scripts/verify_research.py",
        "- backend/scripts/verify_review.py",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    checks = []
    for name, fn in [
        ("Backend /health", check_backend),
        ("Auth login", check_login),
        ("PostgreSQL", check_postgres),
        ("Redis", check_redis),
        ("Neo4j", check_neo4j),
    ]:
        ok, detail = fn()
        checks.append({"name": name, "ok": ok, "detail": detail})

    report = {
        "generated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "checks": checks,
    }

    md = build_markdown(report)
    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "STATUS_SSOT.md"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
