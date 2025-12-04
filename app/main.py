# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import auth, user, tenant
from app.core.database import engine, Base
import os
import logging

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-Tenant API with FastAPI and SQLAlchemy",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(user.router, prefix=settings.API_V1_STR)
app.include_router(tenant.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to the Multi-Tenant API"}


@app.on_event("startup")
def create_tables_on_startup():
    """Create DB tables on startup for local development or when explicitly requested.

    Behavior:
    - If `CREATE_TABLES=true` in env or `.env`, always run `Base.metadata.create_all`.
    - If using SQLite (DEV), create tables automatically.
    """
    try:
        create_flag = os.getenv("CREATE_TABLES", "false").lower() == "true"
        if create_flag or settings.DATABASE_URL.startswith("sqlite"):
            logging.getLogger("uvicorn").info("Creating database tables (create_all)")
            Base.metadata.create_all(bind=engine)
        else:
            logging.getLogger("uvicorn").info("Skipping automatic table creation on startup")
    except Exception as e:
        logging.getLogger("uvicorn.error").exception("Error creating tables on startup: %s", e)

