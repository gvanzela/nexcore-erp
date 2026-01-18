from fastapi import FastAPI

from app.core.config import settings
from app.api.v1.health import router as health_router
from app.api.v1.products import router as products_router
from app.api.v1.auth import router as auth_router
from app.api.v1.customers import router as customers_router
from app.api.v1.orders import router as orders_router

# Create FastAPI application instance
app = FastAPI(title=settings.app_name)

# Health check routes
app.include_router(health_router)

# Product routes
app.include_router(products_router)

# Auth routes
app.include_router(auth_router, prefix="/api/v1")

# Customer routes
app.include_router(customers_router)

# Order routes
app.include_router(orders_router)

