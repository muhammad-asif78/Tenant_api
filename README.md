# Tenant API

Multi-tenant demo API built with FastAPI and SQLAlchemy. This project demonstrates:

- Shared database + shared schema multi-tenancy with row-level isolation by `tenant_id`.
- JWT authentication that includes `tenant_id` in the token payload.
- Basic user & tenant CRUD endpoints with tenant-aware filtering.

This README explains how to run the project locally, run migrations, and test tenant isolation.

--

**Table of contents**

- [Requirements](#requirements)
- [Quickstart](#quickstart)
- [Environment variables](#environment-variables)
- [Database & migrations](#database--migrations)
- [Convenience scripts](#convenience-scripts)
- [API Endpoints](#api-endpoints)
- [Row-level security / Tenant isolation](#row-level-security--tenant-isolation)
- [Development notes](#development-notes)
- [License](#license)

--

## Requirements

- Python 3.10+
- A PostgreSQL instance (recommended) or SQLite for development
- `virtualenv` or other venv tooling

## Quickstart

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root (see recommended variables below).

4. (Optional) For local dev using SQLite the app provides a default `DATABASE_URL` so you can skip step 3.

5. Create DB tables for local development (one-time):

```bash
PYTHONPATH=. .venv/bin/python scripts/create_tables.py
```

6. Start the dev server:

```bash
PYTHONPATH=. .venv/bin/uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API docs.

## Environment variables

Create a `.env` file (or set environment variables) with values like:

```env
# Database (example Postgres)
DATABASE_URL=postgresql+asyncpg://user:password@localhost/tenant_db

# Security
SECRET_KEY=your-very-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Optional: make app auto-create tables on startup (dev only)
CREATE_TABLES=true

# First superuser (optional - not required; first created user becomes admin)
FIRST_SUPERUSER_EMAIL=admin@example.com
FIRST_SUPERUSER_PASSWORD=supersecurepassword
```

> Note: defaults in `app/core/config.py` provide a dev-friendly `sqlite:///./tenant.db` and `dev-secret` SECRET_KEY. Do not use those in production.

## Database & migrations

This project uses Alembic for migrations. Typical workflow:

1. Make model changes in `app/models/`.
2. Generate a migration (example):

```bash
PYTHONPATH=. .venv/bin/alembic revision --autogenerate -m "Add X to users"
```

3. Apply migrations:

```bash
PYTHONPATH=. .venv/bin/alembic upgrade head
```

If you previously changed the DB schema manually during development, stamp the database to the latest revision to avoid Alembic attempting to reapply changes:

```bash
PYTHONPATH=. .venv/bin/alembic stamp head
```

## Convenience scripts

- `scripts/create_tables.py` — imports models and runs `Base.metadata.create_all(bind=engine)` to create tables (dev only).
- `scripts/fix_schema.py` — small helper to add missing columns in local DB (dev only). Prefer Alembic in production.
- `scripts/e2e_db_test.py` — DB-level test script creating two tenants and users and verifying tenant-scoped queries.

Run them with `PYTHONPATH=. .venv/bin/python scripts/<script>.py`.

## API Endpoints (overview)

Base URL: `/api/v1`

- `POST /auth/signup` — Create a user (does NOT return a token). The first user created in the DB is assigned `role='admin'` and `is_superuser=true` automatically.
	- Request sample:
		```json
		{
			"name": "Alice",
			"email": "alice@rtcleague.test",
			"password": "password123",
			"tenant_name": "RTC League"
		}
		```

- `POST /auth/login` — Login and receive access token (JWT). Token payload includes `sub` (user email) and `tenant_id`.

- `GET /auth/me` — Get current user (requires Bearer token).

- `GET /users` — List users for the current user's tenant only (requires auth). Example filter used in code:

```py
db.query(User).filter(User.tenant_id == current_user.tenant_id).all()
```

- `POST /tenants/` — Create tenant (superuser only).

Explore full endpoints and request/response schemas at `http://127.0.0.1:8000/docs`.

## Row-level security / Tenant isolation

This app implements tenant isolation at the application level. Key points:

- Every table that contains tenant data includes a `tenant_id` column.
- The authentication token contains the `tenant_id` of the logged-in user.
- All queries that return tenant data are explicitly filtered using the logged-in user's `tenant_id`. Example:

```py
# Good (tenant-aware)
users = db.query(User).filter(User.tenant_id == current_user.tenant_id).all()

# Bad (insecure)
# users = db.query(User).all()
```

Because the JWT is signed, clients cannot tamper with `tenant_id` without invalidating the token.

Note: For stricter, database-enforced row-level security you can evaluate PostgreSQL RLS policies. This app demonstrates the application-layer approach.

## Development notes & gotchas

- Password hashing: bcrypt is used and passwords are truncated to 72 bytes prior to hashing to avoid bcrypt limits.
- Signup does not return tokens — call `/auth/login` to obtain a JWT.
- The first user created in the system is automatically promoted to admin. For existing databases, you can promote users via SQL or an Alembic data migration.
- Use the project's venv's `alembic` executable or run Alembic with `PYTHONPATH=. .venv/bin/alembic ...` so your app imports are resolvable.

## Example local workflow

```bash
# create venv + install
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# (optional) create sqlite tables for local dev
PYTHONPATH=. .venv/bin/python scripts/create_tables.py

# run app
PYTHONPATH=. .venv/bin/uvicorn app.main:app --reload

# signup (no token returned)
curl -X POST http://127.0.0.1:8000/api/v1/auth/signup -H 'Content-Type: application/json' \
	-d '{"name":"Alice","email":"alice@rtcleague.test","password":"password123","tenant_name":"RTC"}'

# login
curl -X POST http://127.0.0.1:8000/api/v1/auth/login -H 'Content-Type: application/json' \
	-d '{"email":"alice@rtcleague.test","password":"password123"}'

# use token to call tenant-scoped endpoints
```

## Contributing

Contributions welcome. Please open issues or PRs for feature requests, bug fixes, or improvements. If making database schema changes, add Alembic revisions and tests where appropriate.

## License

This project does not include a license file. Add a `LICENSE` file if you want to specify terms.

