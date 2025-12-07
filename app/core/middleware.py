import uuid
import logging
from contextvars import ContextVar
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Context variable to store correlation_id for logging
correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)


class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation_id to log records."""
    
    def filter(self, record):
        correlation_id = correlation_id_ctx.get()
        record.correlation_id = correlation_id if correlation_id else "N/A"
        return True


class CorrelationIdFormatter(logging.Formatter):
    """Custom formatter that safely handles correlation_id field."""
    
    def format(self, record):
        # Ensure correlation_id is set on the record before formatting
        if not hasattr(record, 'correlation_id'):
            correlation_id = correlation_id_ctx.get()
            record.correlation_id = correlation_id if correlation_id else "N/A"
        return super().format(record)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation_id to each request.
    The correlation_id is:
    - Generated if not present in X-Correlation-ID header
    - Stored in request.state for access in handlers
    - Stored in contextvar for logging
    - Added to response headers as X-Correlation-ID
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get correlation_id from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Store in request state for access in handlers
        request.state.correlation_id = correlation_id
        
        # Store in contextvar for logging
        correlation_id_ctx.set(correlation_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add correlation_id to response headers
            if isinstance(response, Response):
                response.headers["X-Correlation-ID"] = correlation_id
            
            return response
        finally:
            # Clear contextvar after request
            correlation_id_ctx.set(None)

