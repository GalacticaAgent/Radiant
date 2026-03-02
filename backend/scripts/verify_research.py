import time

import requests


def main() -> int:
    base = "http://localhost:8000/api/v1"
    login = requests.post(
        f"{base}/auth/login",
        json={"username_or_email": "testuser3", "password": "password123"},
        timeout=30,
    )
    print("login", login.status_code, login.text)
    login.raise_for_status()
    token = login.json()["access_token"]

    start = requests.post(
        f"{base}/research/start",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "graph neural networks", "sources": ["knowledge_graph"], "max_papers": 5},
        timeout=30,
    )
    print("start", start.status_code, start.text)
    start.raise_for_status()
    task_id = start.json()["task_id"]

    for i in range(10):
        time.sleep(0.5)
        status = requests.get(
            f"{base}/research/status/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        print("status", i, status.status_code, status.text)
        status.raise_for_status()
        if status.json().get("status") in ("completed", "failed"):
            break

    result = requests.get(
        f"{base}/research/result/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    print("result", result.status_code, result.text[:500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
