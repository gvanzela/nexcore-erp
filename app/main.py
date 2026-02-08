from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.health import router as health_router
from app.api.v1.products import router as products_router
from app.api.v1.auth import router as auth_router
from app.api.v1.customers import router as customers_router
from app.api.v1.orders import router as orders_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.purchases import router as purchases_router
from app.api.v1.payables import router as payables_router
from app.api.v1.receivables import router as receivables_router

# Create FastAPI application instance
app = FastAPI(title=settings.app_name)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check routes
app.include_router(health_router)

# Product routes
app.include_router(products_router)

# Auth routes
app.include_router(auth_router)

# Customer routes
app.include_router(customers_router)

# Order routes
app.include_router(orders_router)

# Inventory routes
app.include_router(inventory_router)

# Purchase routes
app.include_router(purchases_router)

# Payables routes
app.include_router(payables_router)

# Receivables routes
app.include_router(receivables_router)

