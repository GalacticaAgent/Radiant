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
        print("upload", upload.status_code, upload.text[:300])
        upload.raise_for_status()
        paper_id = upload.json()["id"]

        review = requests.post(
            f"{base}/paper/{paper_id}/review",
            headers=headers,
            json={"reviewer_ids": ["dummy-reviewer-1"]},
            timeout=120,
        )
        print("review", review.status_code, review.text[:300])
        review.raise_for_status()

        reviews = requests.get(f"{base}/paper/{paper_id}/reviews", headers=headers, timeout=30)
        print("reviews", reviews.status_code, reviews.text[:300])
        reviews.raise_for_status()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
