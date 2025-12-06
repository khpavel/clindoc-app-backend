import logging
import sys
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.middleware import CorrelationIdMiddleware, CorrelationIdFilter

# Configure logging based on environment
log_level = logging.WARNING if settings.app_env.lower() == "prod" else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Apply correlation_id filter to root logger
logging.getLogger().addFilter(CorrelationIdFilter())

logger = logging.getLogger(__name__)

from app.db.session import engine, Base
# Import models to ensure they're registered with SQLAlchemy Base
from app.models import user, study, output_document, source, template, rag, ai, study_member, qc, document  # noqa: F401
from app.api.v1.auth import router as auth_router
from app.api.v1.studies import router as studies_router
from app.api.v1.output_document import router as csr_router
from app.api.v1.output import router as output_router
from app.api.v1.ai import router as ai_router
from app.api.v1.sources import router as sources_router
from app.api.v1.templates import router as templates_router
from app.api.v1.rag import router as rag_router
from app.api.v1.qc import router as qc_router
from app.api.v1.documents import router as documents_router

app = FastAPI(
    title="ClinApp Backend",
    version="0.1.0",
    description="Backend API for Clinical Document Management application",
    docs_url="/docs",  # Swagger UI endpoint
    redoc_url="/redoc",  # ReDoc endpoint
    openapi_url="/openapi.json",  # OpenAPI schema endpoint
)


def custom_openapi():
    """Custom OpenAPI schema with proper security configuration for Swagger UI."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Ensure securitySchemes section exists
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    # HTTPBearer automatically adds security scheme, but we ensure it's properly configured
    # The scheme name will be "HTTPBearer" by default
    # Update description for better UX in Swagger UI
    if "HTTPBearer" in openapi_schema["components"]["securitySchemes"]:
        openapi_schema["components"]["securitySchemes"]["HTTPBearer"]["description"] = (
            "Enter JWT token obtained from /api/v1/auth/token endpoint. "
            "Click 'Authorize' button and enter your token (without 'Bearer' prefix)."
        )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Add correlation_id middleware (should be first to set correlation_id for all requests)
app.add_middleware(CorrelationIdMiddleware)

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


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException and add correlation_id to response."""
    # Get correlation_id from request state
    correlation_id = getattr(request.state, "correlation_id", "N/A")
    
    # Log the HTTP exception with correlation_id
    logger.warning(
        f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}",
        extra={"correlation_id": correlation_id}
    )
    
    # Add correlation_id to response
    response_content = exc.detail
    if isinstance(response_content, dict):
        response_content["correlation_id"] = correlation_id
    elif isinstance(response_content, str):
        response_content = {
            "detail": response_content,
            "correlation_id": correlation_id
        }
    else:
        response_content = {
            "detail": str(response_content),
            "correlation_id": correlation_id
        }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_content,
        headers=exc.headers
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    # Get correlation_id from request state
    correlation_id = getattr(request.state, "correlation_id", "N/A")
    
    # Log error with correlation_id and full traceback (but don't send traceback to client)
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True,
        extra={"correlation_id": correlation_id}
    )
    
    # In production, only return generic error message
    # Traceback is logged but not sent to client
    response_content = {
        "detail": "Internal server error",
        "correlation_id": correlation_id
    }
    
    # In development, include more details (but still no traceback)
    if settings.app_env.lower() == "dev":
        response_content.update({
            "error": str(exc),
            "type": type(exc).__name__
        })
    
    return JSONResponse(
        status_code=500,
        content=response_content
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
app.include_router(output_router, prefix="/api/v1", tags=["output"])
app.include_router(ai_router, prefix="/api/v1", tags=["ai"])
app.include_router(sources_router, prefix="/api/v1", tags=["sources"])
app.include_router(templates_router, prefix="/api/v1", tags=["templates"])
app.include_router(rag_router, prefix="/api/v1", tags=["rag"])
app.include_router(qc_router, prefix="/api/v1", tags=["qc"])
app.include_router(documents_router, prefix="/api/v1", tags=["documents"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
