from fastapi import FastAPI

from app.core.config import settings
from app.api.v1.health import router as health_router
from app.api.v1.products import router as products_router

# Create FastAPI application instance
# Application metadata (title) is loaded from environment settings
app = FastAPI(title=settings.app_name)

# Register health check routes
# Used to verify API and infrastructure status
app.include_router(health_router)

# Register product routes
# Exposes CRUD operations for Product entity
app.include_router(products_router)
