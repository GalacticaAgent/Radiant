import os
import tempfile

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

    repo_pdf = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "基于偏好建模的人机交互系统.pdf"))
    with tempfile.TemporaryDirectory() as td:
        if os.path.exists(repo_pdf):
            pdf_path = repo_pdf
        else:
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

        suggestions = requests.post(
            f"{base}/paper/{paper_id}/suggestions",
            headers=headers,
            timeout=120,
        )
        print("paper.suggestions", suggestions.status_code, suggestions.text[:200])
        suggestions.raise_for_status()
        items = suggestions.json()["suggestions"]
        selected = [f"[{s['priority']}] {s['section']}: {s['suggestion']}" for s in items][:10]

        polish = requests.post(
            f"{base}/paper/{paper_id}/polish",
            headers=headers,
            json={"mode": "abstract_only", "selected_suggestions": selected},
            timeout=120,
        )
        print("paper.polish", polish.status_code, polish.text[:200])
        polish.raise_for_status()

        report = requests.get(
            f"{base}/paper/{paper_id}/report",
            headers=headers,
            timeout=60,
        )
        print("paper.report", report.status_code, report.text[:200])
        report.raise_for_status()

        with open(pdf_path, "rb") as f:
            v = requests.post(
                f"{base}/paper/{paper_id}/version",
                headers=headers,
                files={"file": ("test.pdf", f, "application/pdf")},
                timeout=60,
            )
        print("paper.version", v.status_code, v.text[:200])
        v.raise_for_status()

        versions = requests.get(
            f"{base}/paper/{paper_id}/versions",
            headers=headers,
            timeout=60,
        )
        print("paper.versions", versions.status_code, versions.text[:200])
        versions.raise_for_status()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
