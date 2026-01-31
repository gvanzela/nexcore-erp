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
├── README.md            # Project overview, architecture, setup
├── ROADMAP.md           # Completed work and next steps
├── .gitignore           # Ignore env files and caches
├── alembic.ini          # Alembic configuration
├── docker-compose.yml   # Local PostgreSQL service
├── app/
│   ├── main.py          # FastAPI app entrypoint
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py        # Auth: login, refresh, RBAC
│   │       ├── customers.py  # Customer CRUD
│   │       ├── products.py   # Product CRUD
│   │       ├── orders.py     # Orders + inventory OUT
│   │       ├── inventory.py  # Computed stock endpoints
│   │       ├── purchases.py  # Purchase XML preview/confirm
│   │       ├── health.py     # Health checks
│   │       ├── schemas.py    # Pydantic schemas (core)
│   │       └── schemas_auth.py # Auth schemas
│   ├── core/
│   │   ├── database.py  # SQLAlchemy engine / Base
│   │   ├── deps.py      # FastAPI dependencies (get_db)
│   │   ├── security.py  # JWT, password hashing, RBAC
│   │   ├── audit.py     # Audit logging helper
│   │   └── config.py    # Env-based settings
│   └── models/
│       ├── product.py            # Product entity
│       ├── customer.py           # Customer / supplier
│       ├── order.py              # Order header
│       ├── order_item.py         # Order items
│       ├── inventory_movement.py # Stock events (IN/OUT/ADJUST)
│       ├── stg_record.py         # Universal staging table
│       ├── user.py               # User entity
│       ├── role.py               # RBAC roles
│       ├── refresh_token.py      # Refresh tokens
│       ├── audit_log.py          # Audit records
│       └── __init__.py
└── scripts/
    ├── etl/
    │   ├── load_stg_products.py            # Extract legacy products
    │   ├── load_stg_clients.py             # Extract legacy customers
    │   ├── load_stg_orders.py              # Extract legacy orders
    │   ├── load_stg_inventory_initial.py   # Extract initial stock
    │   ├── load_products_from_stg.py       # Promote products
    │   ├── load_customers_from_stg.py      # Promote customers
    │   ├── load_orders_from_stg.py         # Promote orders + items
    │   └── load_inventory_from_stg.py      # Promote inventory movements
    └── xml/
        ├── read_nfe_xml.py        # Parse NF-e XML
        ├── match_items_by_ean.py  # Match XML items to products
        └── promote_purchase_in.py # Create inventory IN movements
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
