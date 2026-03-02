import os
import sys
import time
import uuid

import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.postgres import SessionLocal
from app.models.paper import Paper
from app.models.user import User


def ensure_real_paper() -> str:
    title = "Attention Is All You Need"
    abstract = (
        "We propose the Transformer, a novel neural network architecture based solely on attention mechanisms, "
        "dispensing with recurrence and convolutions entirely. The model achieves state-of-the-art results on machine translation."
    )
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "testuser3").first()
        if not user:
            raise RuntimeError("testuser3 not found")
        existing = db.query(Paper).filter(Paper.user_id == user.id, Paper.title == title).first()
        if existing:
            return str(existing.id)
        p = Paper(
            id=uuid.uuid4(),
            user_id=user.id,
            title=title,
            filename="real-title-seed.txt",
            file_path="seed://real-title",
            file_size=0,
            content="",
            abstract=abstract,
            paper_metadata={},
            version=1,
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        return str(p.id)


def main() -> int:
    paper_id = ensure_real_paper()
    base = "http://localhost:8000/api/v1"

    login = requests.post(
        f"{base}/auth/login",
        json={"username_or_email": "testuser3", "password": "password123"},
        timeout=30,
    )
    login.raise_for_status()
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.post(f"{base}/paper/{paper_id}/kb/ingest", headers=headers, timeout=120)
    print("ingest", r.status_code, r.text[:200])
    r.raise_for_status()

    for i in range(60):
        st = requests.get(f"{base}/paper/{paper_id}/reviewer-candidates/status", headers=headers, timeout=30)
        st.raise_for_status()
        status_val = st.json().get("status")
        print("status", i, status_val)

        c = requests.get(
            f"{base}/paper/{paper_id}/reviewer-candidates",
            headers=headers,
            params={"limit": 5, "fallback_to_llm": False},
            timeout=30,
        )
        if c.status_code == 200 and (c.json().get("total") or 0) > 0:
            s = requests.get(f"{base}/paper/{paper_id}/similar-papers", headers=headers, params={"top_k": 5}, timeout=60)
            print("candidates_total", c.json().get("total"))
            print("similar_total", s.json().get("total") if s.status_code == 200 else None)
            return 0
        time.sleep(5)

    raise RuntimeError("timeout waiting for semantic scholar authors to be built")


if __name__ == "__main__":
    raise SystemExit(main())
