"""
Push Notification Service - FastAPI Application
==============================================

Standalone microservice for handling web push notifications.
Extracted from Django portfolio application.
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from .config import settings
from .database import database, engine
from .routers import subscriptions, notifications, analytics, health
from .middleware import RateLimitMiddleware
from .models import metadata
from .auth import verify_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Sentry
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(auto_enabling=True),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )

# Database lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connections and startup/shutdown events"""
    try:
        # Connect to database
        await database.connect()
        logger.info("Database connected successfully")
        
        # Create tables if they don't exist
        metadata.create_all(engine)
        logger.info("Database tables created/verified")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        # Disconnect from database
        await database.disconnect()
        logger.info("Database disconnected")


# Create FastAPI application
app = FastAPI(
    title="Push Notification Service",
    description="Microservice for handling web push notifications",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# Security middleware
security = HTTPBearer()

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)

app.add_middleware(RateLimitMiddleware)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured response"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_error"
            },
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "server_error"
            },
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Dependency for authentication
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user information"""
    try:
        payload = verify_token(credentials.credentials)
        return payload
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Include routers
app.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

app.include_router(
    subscriptions.router,
    prefix="/subscriptions",
    tags=["subscriptions"],
    dependencies=[Depends(get_current_user)] if settings.REQUIRE_AUTH else []
)

app.include_router(
    notifications.router,
    prefix="/notifications", 
    tags=["notifications"],
    dependencies=[Depends(get_current_user)] if settings.REQUIRE_AUTH else []
)

app.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(get_current_user)] if settings.REQUIRE_AUTH else []
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Push Notification Service",
        "version": "1.0.0",
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "documentation": "/docs" if settings.ENVIRONMENT == "development" else None
    }


# Prometheus metrics endpoint
if settings.PROMETHEUS_METRICS_ENABLED:
    from prometheus_fastapi_instrumentator import Instrumentator
    
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health", "/health/ready", "/health/live"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    )
    
    instrumentator.instrument(app)
    instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )