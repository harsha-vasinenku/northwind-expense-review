"""FastAPI application factory with lifespan hooks."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import AsyncSessionLocal, Base, engine
from app.routers import employees, overrides, policy_qa, receipts, submissions
from app.seed.seed_employees import seed_employees
from app.seed.seed_policies import seed_policies
from app.services.rag import get_rag_service

logger = structlog.get_logger(__name__)

VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: create tables, seed employees, index policies."""
    settings = get_settings()

    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    async with AsyncSessionLocal() as session:
        await seed_employees(session)

    rag = get_rag_service()
    await seed_policies(rag)

    logger.info("Application startup complete", version=VERSION)
    yield
    logger.info("Application shutdown")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Northwind Expense Review",
        version=VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(employees.router)
    app.include_router(submissions.router)
    app.include_router(receipts.router)
    app.include_router(overrides.router)
    app.include_router(policy_qa.router)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        from sqlalchemy import text

        from app.database import AsyncSessionLocal as _session

        db_status = "disconnected"
        chroma_status = "not_ready"

        try:
            async with _session() as session:
                await session.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception:
            logger.exception("DB health check failed")

        try:
            rag = get_rag_service()
            rag.get_indexed_doc_ids()
            chroma_status = "ready"
        except Exception:
            logger.exception("ChromaDB health check failed")

        return {
            "status": "ok",
            "db": db_status,
            "chroma": chroma_status,
            "version": VERSION,
        }

    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        from fastapi.responses import FileResponse

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str) -> FileResponse:
            file = static_dir / full_path
            if file.exists() and file.is_file():
                return FileResponse(str(file))
            return FileResponse(str(static_dir / "index.html"))

    return app


app = create_app()
