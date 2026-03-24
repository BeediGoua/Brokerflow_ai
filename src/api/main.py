"""
FastAPI application setup.

Defines the FastAPI app instance and includes route modules.  The API is
versioned by prefixing paths with ``/v1`` (as configured in ``settings.api_version``).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.api.routes import health, scoring, review, scoring_real


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="BrokerFlow AI", version=settings.api_version)
    # Enable CORS for demo purposes
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    prefix = f"/{settings.api_version}"
    app.include_router(health.router, prefix=prefix)
    app.include_router(scoring.router, prefix=prefix)
    app.include_router(review.router, prefix=prefix)
    app.include_router(scoring_real.router, prefix="/v2")
    return app


app = create_app()