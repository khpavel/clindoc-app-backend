import logging
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

from app.db.session import engine, Base
# Import models to ensure they're registered with SQLAlchemy Base
from app.models import user, study, csr, source  # noqa: F401
from app.api.v1.auth import router as auth_router
from app.api.v1.studies import router as studies_router
from app.api.v1.csr import router as csr_router
from app.api.v1.ai import router as ai_router
from app.api.v1.sources import router as sources_router

app = FastAPI(
    title="CSR Assistant Backend",
    version="0.1.0",
    description="Backend API for CSR Assistant application",
    docs_url="/docs",  # Swagger UI endpoint
    redoc_url="/redoc",  # ReDoc endpoint
    openapi_url="/openapi.json",  # OpenAPI schema endpoint
)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True
    )
    # In development, return more details about the error
    import os
    if os.environ.get("APP_ENV", "dev").lower() == "dev":
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "type": type(exc).__name__
            }
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# create tables on startup (for MVP; later replace with Alembic)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified successfully")
except Exception as e:
    logger.error(f"Failed to create database tables: {e}", exc_info=True)
    # Don't raise here - let the app start, but database operations will fail
    # This allows the app to start even if DB is temporarily unavailable

# Include routers
app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(studies_router, prefix="/api/v1", tags=["studies"])
app.include_router(csr_router, prefix="/api/v1", tags=["csr"])
app.include_router(ai_router, prefix="/api/v1", tags=["ai"])
app.include_router(sources_router, prefix="/api/v1", tags=["sources"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
