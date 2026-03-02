import requests


def main() -> int:
    base = "http://localhost:8000/api/v1"
    paper_id = "f9825c6c-d83a-4a37-9276-0440f56185e8"

    login = requests.post(
        f"{base}/auth/login",
        json={"username_or_email": "testuser3", "password": "password123"},
        timeout=30,
    )
    login.raise_for_status()
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    status = requests.get(f"{base}/paper/{paper_id}/reviewer-candidates/status", headers=headers, timeout=30)
    print("status", status.status_code, status.json().get("status"))

    cands = requests.get(f"{base}/paper/{paper_id}/reviewer-candidates", headers=headers, params={"limit": 5}, timeout=60)
    print("candidates", cands.status_code, cands.json().get("total"))

    sim = requests.get(f"{base}/paper/{paper_id}/similar-papers", headers=headers, params={"top_k": 5}, timeout=60)
    print("similar", sim.status_code, sim.json().get("total"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

