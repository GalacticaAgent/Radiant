import time

import requests


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

    paper_list = requests.get(f"{base}/paper", headers=headers, timeout=30)
    print("paper list", paper_list.status_code)
    paper_list.raise_for_status()
    papers = paper_list.json().get("papers", [])
    if not papers:
        raise RuntimeError("no papers found; upload one paper first")
    paper_id = None
    for p in papers:
        title = (p.get("title") or p.get("filename") or "").lower()
        if "fall detection" in title or str(p.get("filename") or "").startswith("seed-"):
            paper_id = p["id"]
            break
    if not paper_id:
        paper_id = papers[0]["id"]
    print("using paper", paper_id)

    ingest = requests.post(f"{base}/paper/{paper_id}/kb/ingest", headers=headers, timeout=30)
    print("ingest", ingest.status_code, ingest.text[:200])
    ingest.raise_for_status()

    for i in range(30):
        st = requests.get(f"{base}/paper/{paper_id}/reviewer-candidates/status", headers=headers, timeout=30)
        print("status", i, st.status_code)
        st.raise_for_status()
        if st.json().get("status") in {"done", "failed"}:
            break
        time.sleep(2)

    cands = requests.get(f"{base}/paper/{paper_id}/reviewer-candidates", headers=headers, params={"limit": 5}, timeout=60)
    print("candidates", cands.status_code, cands.text[:300])
    cands.raise_for_status()

    sim = requests.get(f"{base}/paper/{paper_id}/similar-papers", headers=headers, params={"top_k": 5}, timeout=60)
    print("similar", sim.status_code, sim.text[:300])
    sim.raise_for_status()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
