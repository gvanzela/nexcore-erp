# Nexcore ERP

Nexcore ERP is a backend-first, API-driven ERP core designed to be **generic,
modular, and predictable**.

The project focuses on building a **strong business and financial core**
before any frontend, BI layer, or legacy-system coupling.

The architecture is intentionally **domain-agnostic**, allowing reuse across
different industries and business models through adapters, ETL, and staging.

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
→ Domain Models (SQLAlchemy ORM)  
→ PostgreSQL  

Legacy systems are integrated **outside the core** via ETL + staging.

---

## Core Design Principles

- API-first architecture  
- Explicit input/output schemas  
- Clear separation of domain vs integration logic  
- Ledger-based inventory (no mutable stock table)  
- Financial consistency via atomic transactions  
- Database versioned exclusively via migrations  

---

## Inventory Model

There is **no stock table**.

Inventory is modeled as a **ledger**:

- Every physical event generates an `inventory_movement`
- Stock balance is always **computed**, never stored
- Adjustments are new movements, never updates

This guarantees:
- Auditability  
- Traceability  
- Zero silent corruption  

---

## Financial Flows (AP / AR)

The financial layer is **event-driven** and minimal by design.

### Accounts Payable (AP)
- Generated automatically on **purchase confirmation**
- 1 purchase → 1 payable (MVP)
- Status lifecycle: `OPEN → PAID`
- Duplicate protection via `(source_entity, source_id)` uniqueness

### Accounts Receivable (AR)
- Generated automatically on **order creation**
- 1 order → 1 receivable
- Same minimal lifecycle as AP
- Fully symmetric design with Payables

Financial state is always consistent with operational events.

---

## Purchases (NF-e XML Flow)

NF-e XML processing follows a strict, auditable pipeline:

1. **Preview**
   - XML parsed
   - Supplier identified
   - Items matched by EAN/barcode
   - No database side effects

2. **Confirm**
   - Inventory IN movements created
   - Supplier promoted if needed
   - Accounts Payable generated
   - Transaction committed atomically

---

## Project Structure

```text
nexcore-erp/
├── README.md                 # Project overview, architecture and principles
├── ROADMAP.md                # Product and technical roadmap
├── .gitignore                # Ignore rules (envs, cache, local artifacts)
├── alembic.ini               # Alembic migration configuration
├── docker-compose.yml        # Local PostgreSQL container
├── Dockerfile                # FastAPI application container
├── requirements.txt          # Python dependencies
│
├── alembic/
│   └── versions/             # Database migration history (authoritative)
│
├── app/
│   ├── main.py               # FastAPI bootstrap and router registration
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py           # API v1 namespace
│   │       ├── auth.py               # Authentication and token lifecycle
│   │       ├── customers.py          # Customers/Suppliers CRUD + search
│   │       ├── health.py             # Health check and DB connectivity
│   │       ├── inventory.py          # Computed stock and inventory listings
│   │       ├── orders.py             # Orders CRUD + inventory OUT + AR creation
│   │       ├── receivables.py        # Accounts Receivable (list + pay)
│   │       ├── payables.py            # Accounts Payable (list + pay)
│   │       ├── products.py            # Product catalog CRUD
│   │       ├── purchases.py           # NF-e XML preview / confirm flow
│   │       ├── schemas.py             # Shared Pydantic schemas (core entities)
│   │       ├── schemas_auth.py        # Auth schemas
│   │       ├── schemas_payables.py    # Accounts Payable schemas
│   │       └── schemas_receivables.py # Accounts Receivable schemas
│   │
│   ├── core/
│   │   ├── __init__.py        # Core utilities namespace
│   │   ├── audit.py           # Audit log helpers
│   │   ├── config.py          # Environment and settings loader
│   │   ├── database.py        # SQLAlchemy engine and Base
│   │   ├── deps.py            # Dependency injection (DB session lifecycle)
│   │   └── security.py        # Password hashing, JWT, RBAC, refresh tokens
│   │
│   └── models/
│       ├── __init__.py                # Centralized ORM exports
│       ├── account_payable.py         # Accounts Payable model
│       ├── account_receivable.py      # Accounts Receivable model
│       ├── audit_log.py               # Audit log model
│       ├── customer.py                # Customer / Supplier model
│       ├── inventory_movement.py      # Inventory ledger model
│       ├── order.py                   # Order header model
│       ├── order_item.py              # Order line-item model
│       ├── product.py                 # Product catalog model
│       ├── refresh_token.py           # Refresh token persistence
│       ├── role.py                    # RBAC role model
│       ├── stg_record.py              # Universal staging table
│       └── user.py                    # User and auth model
│
└── scripts/
    ├── etl/
    │   ├── load_customers_from_stg.py         # Promote staged customers
    │   ├── load_inventory_from_stg.py         # Convert staged inventory to movements
    │   ├── load_missing_suppliers_from_stg.py # Insert missing suppliers
    │   ├── load_orders_from_stg.py            # Promote staged orders
    │   ├── load_products_from_stg.py          # Promote staged products
    │   ├── load_stg_clients.py                # Extract legacy clients
    │   ├── load_stg_inventory_initial.py      # Initial inventory snapshot
    │   ├── load_stg_orders.py                 # Extract legacy orders
    │   ├── load_stg_products.py               # Extract legacy products
    │   ├── load_stg_suppliers.py              # Extract legacy suppliers
    │   └── load_suppliers_from_stg.py         # Normalize supplier role
    │
    └── xml/
        ├── match_items_by_ean.py      # Match NF-e items to products (EAN)
        ├── promote_purchase_in.py     # Inventory IN from confirmed purchases
        └── read_nfe_xml.py            # NF-e XML parsing and normalization
```

---

## How to Run Locally

Requirements:
- Python 3.12+
- Docker + Docker Compose

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
docker compose up -d
uvicorn app.main:app --reload
```

API Docs:
- Swagger UI: http://127.0.0.1:8000/docs  

---

## Project Status

This project is under **active development** and already supports
real operational and financial flows.

Current focus:
- API consistency  
- Financial correctness  
- Predictable evolution of the core domain  

The goal is **reliability first**, not premature abstraction.
