"""End-to-end test for tenant isolation.

This script:
- Ensures models are imported and tables created.
- Uses FastAPI TestClient to call `/api/v1/auth/signup` twice (two tenants).
- Calls `/api/v1/users` with each token and verifies returned users belong to the token's tenant.

Run:
    PYTHONPATH=. .venv/bin/python scripts/e2e_test.py
"""
from app.core.database import engine, Base
import app.models.user  # noqa: F401
import app.models.tenant  # noqa: F401

from fastapi.testclient import TestClient
from app.main import app
import json


def setup_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)


def signup(client, name, email, password, tenant_name):
    payload = {"name": name, "email": email, "password": password, "tenant_name": tenant_name}
    r = client.post("/api/v1/auth/signup", json=payload)
    print("signup", tenant_name, r.status_code)
    r.raise_for_status()
    return r.json()


def get_users(client, token):
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/api/v1/users", headers=headers)
    print("get users", r.status_code)
    r.raise_for_status()
    return r.json()


def main():
    setup_db()

    client = TestClient(app)

    # Tenant 1: RTC League
    resp1 = signup(client, "Alice", "alice@rtcleague.test", "password123", "RTC League")
    token1 = resp1["access_token"] if isinstance(resp1, dict) and "access_token" in resp1 else resp1.get("access_token")

    # Tenant 2: Convai AI
    resp2 = signup(client, "Bob", "bob@convai.test", "password123", "Convai AI")
    token2 = resp2["access_token"] if isinstance(resp2, dict) and "access_token" in resp2 else resp2.get("access_token")

    users1 = get_users(client, token1)
    users2 = get_users(client, token2)

    print("Tenant 1 users:", json.dumps(users1, indent=2))
    print("Tenant 2 users:", json.dumps(users2, indent=2))

    # Basic assertions
    assert all(u["tenant_id"] == users1[0]["tenant_id"] for u in users1)
    assert all(u["tenant_id"] == users2[0]["tenant_id"] for u in users2)
    assert users1[0]["tenant_id"] != users2[0]["tenant_id"]

    print("E2E tenant isolation test passed")


if __name__ == "__main__":
    main()
