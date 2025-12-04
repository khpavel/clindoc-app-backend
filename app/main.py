import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine, Base
from app.api.v1.studies import router as studies_router
from app.api.v1.csr import router as csr_router
from app.api.v1.ai import router as ai_router
from app.api.v1.sources import router as sources_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="CSR Assistant Backend",
    version="0.1.0",
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
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# create tables on startup (for MVP; later replace with Alembic)
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(studies_router, prefix="/api/v1", tags=["studies"])
app.include_router(csr_router, prefix="/api/v1", tags=["csr"])
app.include_router(ai_router, prefix="/api/v1", tags=["ai"])
app.include_router(sources_router, prefix="/api/v1", tags=["sources"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
