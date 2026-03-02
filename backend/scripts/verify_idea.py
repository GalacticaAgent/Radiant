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

    validate = requests.post(
        f"{base}/idea/validate",
        headers={"Authorization": f"Bearer {token}"},
        json={"idea": "Use graph neural networks to improve citation recommendation."},
        timeout=120,
    )
    print("validate", validate.status_code, validate.text[:500])
    validate.raise_for_status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

