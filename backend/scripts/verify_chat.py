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

    sessions = requests.get(f"{base}/chat/sessions", headers=headers, timeout=30)
    print("sessions", sessions.status_code, sessions.text[:300])
    sessions.raise_for_status()

    send = requests.post(
        f"{base}/chat/send",
        headers=headers,
        json={"message": "Hello, please summarize what Radiant does in one sentence.", "search_graph": False},
        timeout=120,
    )
    print("send", send.status_code, send.text[:300])
    send.raise_for_status()
    session_id = send.json()["session_id"]

    history = requests.get(
        f"{base}/chat/history",
        headers=headers,
        params={"session_id": session_id, "limit": 20},
        timeout=30,
    )
    print("history", history.status_code, history.text[:300])
    history.raise_for_status()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

