import os
import tempfile
import time

import requests


def make_dummy_pdf(path: str) -> None:
    content = (
        b"%PDF-1.0\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
        b"3 0 obj<</Type/Page/MediaBox[0 0 3 3]/Parent 2 0 R/Resources<<>>>>endobj\n"
        b"xref\n"
        b"0 4\n"
        b"0000000000 65535 f\n"
        b"0000000010 00000 n\n"
        b"0000000060 00000 n\n"
        b"0000000117 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n"
        b"199\n"
        b"%%EOF"
    )
    with open(path, "wb") as f:
        f.write(content)


def main() -> int:
    base = "http://localhost:8000/api/v1"

    login = requests.post(
        f"{base}/auth/login",
        json={"username_or_email": "testuser3", "password": "password123"},
        timeout=30,
    )
    print("login", login.status_code)
    login.raise_for_status()
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    send = requests.post(
        f"{base}/chat/send",
        headers=headers,
        json={"message": "Please reply with 'ok' only.", "search_graph": False},
        timeout=120,
    )
    print("chat.send", send.status_code, send.text[:200])
    send.raise_for_status()
    session_id = send.json()["session_id"]

    history = requests.get(
        f"{base}/chat/history",
        headers=headers,
        params={"session_id": session_id, "limit": 20},
        timeout=30,
    )
    print("chat.history", history.status_code)
    history.raise_for_status()

    validate = requests.post(
        f"{base}/idea/validate",
        headers=headers,
        json={"idea": "Use graph neural networks to improve citation recommendation."},
        timeout=120,
    )
    print("idea.validate", validate.status_code)
    validate.raise_for_status()

    start = requests.post(
        f"{base}/research/start",
        headers=headers,
        json={"query": "graph neural networks", "sources": ["knowledge_graph"], "max_papers": 5},
        timeout=30,
    )
    print("research.start", start.status_code, start.text[:200])
    start.raise_for_status()
    task_id = start.json()["task_id"]

    deadline = time.time() + 120
    status_payload = None
    while time.time() < deadline:
        status = requests.get(f"{base}/research/status/{task_id}", headers=headers, timeout=30)
        status.raise_for_status()
        status_payload = status.json()
        print("research.status", status_payload.get("status"), status_payload.get("progress"), status_payload.get("message"))
        if status_payload.get("status") in ("completed", "failed"):
            break
        time.sleep(1.5)

    if not status_payload or status_payload.get("status") != "completed":
        raise RuntimeError(f"research not completed: {status_payload}")

    result = requests.get(f"{base}/research/result/{task_id}", headers=headers, timeout=30)
    print("research.result", result.status_code, result.text[:200])
    result.raise_for_status()

    with tempfile.TemporaryDirectory() as td:
        pdf_path = os.path.join(td, "test.pdf")
        make_dummy_pdf(pdf_path)
        with open(pdf_path, "rb") as f:
            upload = requests.post(
                f"{base}/paper/upload",
                headers=headers,
                files={"file": ("test.pdf", f, "application/pdf")},
                timeout=60,
            )
        print("paper.upload", upload.status_code, upload.text[:200])
        upload.raise_for_status()
        paper_id = upload.json()["id"]

        review = requests.post(
            f"{base}/paper/{paper_id}/review",
            headers=headers,
            json={"reviewer_ids": ["dummy-reviewer-1"]},
            timeout=120,
        )
        print("paper.review", review.status_code, review.text[:200])
        review.raise_for_status()

        reviews = requests.get(f"{base}/paper/{paper_id}/reviews", headers=headers, timeout=30)
        print("paper.reviews", reviews.status_code, reviews.text[:200])
        reviews.raise_for_status()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

