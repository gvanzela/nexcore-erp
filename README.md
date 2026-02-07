# Nexcore ERP

Nexcore ERP is a backend-first, API-driven ERP core designed to be generic,
modular, and scalable.  
The project focuses on building a strong business core before any frontend or
legacy-system integration.

The architecture is intentionally domain-agnostic, allowing reuse across
different industries and business models.

---

## Tech Stack

- Python 3.12  
- FastAPI  
- PostgreSQL  
- SQLAlchemy (ORM)  
- Alembic (database migrations)  
- Docker / Docker Compose  

---

## High-Level Architecture

Client / Swagger / Frontend  
→ FastAPI  
→ API Routers (v1)  
→ SQLAlchemy ORM Models  
→ PostgreSQL  

---

## Project Structure

```text

nexcore-erp/
├── README.md                 # High-level project overview, architecture, and setup
├── ROADMAP.md                # Product and technical roadmap
├── .gitignore                # Ignore rules for env files, cache, and local artifacts
├── alembic.ini               # Alembic migration configuration
├── docker-compose.yml        # Local PostgreSQL container definition
├── Dockerfile                # FastAPI application container build
├── requirements.txt          # Python dependencies
│
├── app/
│   ├── main.py               # FastAPI bootstrap and API router registration
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py           # API v1 namespace marker
│   │       ├── auth.py               # Authentication and token lifecycle endpoints
│   │       ├── customers.py          # Customers/Suppliers CRUD and search endpoints
│   │       ├── health.py             # Health check and DB connectivity endpoint
│   │       ├── inventory.py          # Computed inventory balance and listings
│   │       ├── orders.py             # Orders CRUD and stock OUT movements
│   │       ├── payables.py            # Accounts Payable (purchase-based)
│   │       ├── products.py            # Product catalog CRUD endpoints
│   │       ├── purchases.py           # NF-e XML preview and confirm flow
│   │       ├── schemas.py             # Shared Pydantic schemas (core entities)
│   │       ├── schemas_auth.py        # Auth request/response schemas
│   │       └── schemas_payables.py    # Accounts Payable schemas
│   │
│   ├── core/
│   │   ├── __init__.py        # Core utilities namespace
│   │   ├── audit.py           # Audit log helper functions
│   │   ├── config.py          # Environment and settings loader
│   │   ├── database.py        # SQLAlchemy engine and Base definition
│   │   ├── deps.py            # Dependency injection (DB session lifecycle)
│   │   └── security.py        # Password hashing, JWT, RBAC, refresh tokens
│   │
│   └── models/
│       ├── __init__.py                # Centralized ORM model exports
│       ├── account_payable.py         # Accounts Payable ORM model
│       ├── audit_log.py               # Audit log ORM model
│       ├── customer.py                # Customer/Supplier ORM model
│       ├── inventory_movement.py      # Inventory movement ledger model
│       ├── order.py                   # Order header ORM model
│       ├── order_item.py              # Order line-item ORM model
│       ├── product.py                 # Product catalog ORM model
│       ├── refresh_token.py           # Refresh token persistence
│       ├── role.py                    # RBAC role model
│       ├── stg_record.py              # Universal staging table model
│       └── user.py                    # User and authentication model
│
└── scripts/
    ├── etl/
    │   ├── load_customers_from_stg.py        # Promote staged customers into core
    │   ├── load_inventory_from_stg.py        # Convert staged inventory into movements
    │   ├── load_missing_suppliers_from_stg.py# Insert missing suppliers from staging
    │   ├── load_orders_from_stg.py           # Promote staged orders into core orders
    │   ├── load_products_from_stg.py         # Promote staged products into catalog
    │   ├── load_stg_clients.py               # Extract legacy clients into staging
    │   ├── load_stg_inventory_initial.py     # Initial legacy inventory snapshot
    │   ├── load_stg_orders.py                # Extract legacy orders into staging
    │   ├── load_stg_products.py              # Extract legacy products into staging
    │   ├── load_stg_suppliers.py             # Extract legacy suppliers into staging
    │   └── load_suppliers_from_stg.py        # Normalize supplier role in customers
    │
    └── xml/
        ├── match_items_by_ean.py      # Match NF-e items to products by barcode/EAN
        ├── promote_purchase_in.py     # Create inventory IN movements from purchases
        └── read_nfe_xml.py            # NF-e XML parsing and normalization

```
---

## Design Principles

- API-first architecture  
- Clear separation of concerns  
- Explicit input/output schemas  
- Database versioned via migrations  
- Soft delete strategy using `active` flag  

---

## How to Run Locally

Requirements:
- Python 3.12+
- Docker + Docker Compose

Setup steps:

python -m venv .venv  
source .venv/Scripts/activate  
pip install -r requirements.txt  
docker compose up -d  
uvicorn app.main:app --reload  

API Docs:
- Swagger UI: http://127.0.0.1:8000/docs  

---

## Current Features

- Product core entity  
- Product CRUD:
  - Create (POST)  
  - Read (list and by id)  
  - Update (PATCH, partial update)  
  - Soft delete via `active` flag  
- Health check and database check endpoints  
- Alembic-managed database schema  

---

## Project Status

The project is under active development.  
Current focus is on strengthening the core domain, API consistency, and
enterprise-ready patterns before expanding to additional entities and
authentication.
