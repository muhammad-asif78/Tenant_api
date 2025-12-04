"""Fix DB schema issues for local/dev environment.

This script inspects the `users` table and adds missing columns that were
recently introduced in the SQLAlchemy models but not present in the DB.

Run with:
    PYTHONPATH=. .venv/bin/python scripts/fix_schema.py

Note: For production, use Alembic migrations. This is a quick local fix.
"""
from sqlalchemy import inspect, text
from app.core.database import engine


def ensure_column(table: str, column: str, ddl: str):
    inspector = inspect(engine)
    cols = [c['name'] for c in inspector.get_columns(table)]
    if column in cols:
        print(f"Column '{column}' already exists on '{table}'")
        return
    print(f"Adding column '{column}' to '{table}'")
    with engine.begin() as conn:
        conn.execute(text(ddl))
    print("Done")


def main():
    # Add `name` column to users if missing
    ensure_column(
        table='users',
        column='name',
        ddl="ALTER TABLE users ADD COLUMN name VARCHAR;",
    )
    # Add `role` column to users if missing (default to 'user')
    ensure_column(
        table='users',
        column='role',
        ddl="ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user';",
    )


if __name__ == '__main__':
    main()
