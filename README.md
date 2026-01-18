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
├── README.md                  # High-level project overview and architecture
├── ROADMAP.md                 # Planned features, milestones and long-term vision
├── DECISIONS.md               # Architectural Decision Records (ADR)
├── docker-compose.yml         # Local infrastructure (PostgreSQL, services)
├── alembic.ini                # Alembic configuration
│
├── alembic/
│   ├── env.py                 # Alembic runtime environment and DB context
│   └── versions/              # Database migration history (core + staging)
│
├── app/
│   ├── main.py                # Application entrypoint (FastAPI bootstrap)
│   │
│   ├── api/
│   │   └── v1/                # Versioned API (contract stability)
│   │       ├── __init__.py
│   │       ├── health.py      # Health check endpoint
│   │       ├── auth.py        # Authentication & token lifecycle
│   │       ├── products.py    # Product CRUD endpoints (core domain)
│   │       ├── customers.py   # Customer / Supplier endpoints
│   │       ├── schemas.py     # Shared Pydantic schemas (request / response)
│   │       └── schemas_auth.py# Auth-specific schemas
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Application settings and environment loading
│   │   ├── database.py        # Database engine and session management
│   │   ├── deps.py            # Dependency injection (DB, auth, RBAC)
│   │   ├── security.py        # JWT, password hashing, auth helpers
│   │   └── audit.py           # Centralized audit logging
│   │
│   └── models/
│       ├── __init__.py
│       ├── product.py         # Product core domain model
│       ├── customer.py        # Customer / Supplier core model
│       ├── user.py            # User and authentication model
│       ├── role.py            # RBAC role model
│       ├── refresh_token.py   # Refresh token persistence
│       └── audit_log.py       # Audit log persistence
│
├── scripts/
│   └── etl/                            # Data adapters (legacy systems → core schema)
│       ├── load_stg_products.py        # Load raw legacy products into staging
│       ├── load_products_from_stg.py   # Promote staged products into core
│       ├── load_stg_clients.py         # Load raw legacy clients into staging
│       └── load_customers_from_stg.py  # Promote staged clients into core
│
└── .gitignore                 # Ignored files and secrets

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
