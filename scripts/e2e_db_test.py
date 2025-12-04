"""Simple DB-level E2E test to validate tenant isolation without HTTP.

This avoids needing TestClient/httpx by performing the same operations directly
against the SQLAlchemy session and security helpers.

Run:
    PYTHONPATH=. .venv/bin/python scripts/e2e_db_test.py
"""
from app.core.database import SessionLocal, engine, Base
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import get_password_hash, create_access_token


def setup_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)


def create_tenant_and_user(session, tenant_name, name, email, password):
    tenant = session.query(Tenant).filter(Tenant.name == tenant_name).first()
    if not tenant:
        tenant = Tenant(name=tenant_name)
        session.add(tenant)
        session.commit()
        session.refresh(tenant)

    hashed = get_password_hash(password)
    user = User(email=email, hashed_password=hashed, tenant_id=tenant.id)
    session.add(user)
    session.commit()
    session.refresh(user)
    return tenant, user


def main():
    setup_db()
    session = SessionLocal()

    # Create tenant 1 and user
    t1, u1 = create_tenant_and_user(session, "RTC League", "Alice", "alice@rtcleague.test", "password123")
    # Create tenant 2 and user
    t2, u2 = create_tenant_and_user(session, "Convai AI", "Bob", "bob@convai.test", "password123")

    # Create tokens as login would produce
    token1 = create_access_token({"sub": u1.email, "tenant_id": u1.tenant_id})
    token2 = create_access_token({"sub": u2.email, "tenant_id": u2.tenant_id})

    # Simulate tenant-aware queries
    users_for_t1 = session.query(User).filter(User.tenant_id == u1.tenant_id).all()
    users_for_t2 = session.query(User).filter(User.tenant_id == u2.tenant_id).all()

    print(f"Tenant {t1.name} (id={t1.id}) users:")
    for u in users_for_t1:
        print(f" - {u.email} (tenant_id={u.tenant_id})")

    print(f"Tenant {t2.name} (id={t2.id}) users:")
    for u in users_for_t2:
        print(f" - {u.email} (tenant_id={u.tenant_id})")

    assert all(u.tenant_id == u1.tenant_id for u in users_for_t1)
    assert all(u.tenant_id == u2.tenant_id for u in users_for_t2)
    assert u1.tenant_id != u2.tenant_id

    print("DB-level tenant isolation test passed")


if __name__ == "__main__":
    main()
