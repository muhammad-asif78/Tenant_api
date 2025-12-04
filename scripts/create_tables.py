"""Utility script to create all DB tables from the SQLAlchemy models.

Run this with the project's virtualenv to populate the database with the tables
defined in `app.models` (useful for local development when migrations are not run).

Usage:
    .venv/bin/python scripts/create_tables.py
"""
from app.core.database import engine, Base
# Ensure model modules are imported so they register with Base.metadata
import app.models.user  # noqa: F401
import app.models.tenant  # noqa: F401
import logging


def main():
    logging.getLogger("uvicorn").info("Creating database tables from models...")
    Base.metadata.create_all(bind=engine)
    logging.getLogger("uvicorn").info("Tables created")


if __name__ == "__main__":
    main()
