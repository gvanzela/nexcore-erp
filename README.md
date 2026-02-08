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
├── README.md                 # Project overview and architecture
├── ROADMAP.md                # Product and technical roadmap
├── alembic.ini               # Alembic migration configuration
├── docker-compose.yml        # Local PostgreSQL container
├── Dockerfile                # FastAPI container build
├── requirements.txt          # Python dependencies
│
├── app/
│   ├── main.py               # FastAPI bootstrap and router registration
│   ├── api/
│   │   └── v1/               # Versioned API endpoints
│   ├── core/                 # DB, security, audit, config
│   └── models/               # Domain models (ORM)
│
└── scripts/
    ├── etl/                  # Legacy ingestion and normalization
    └── xml/                  # NF-e XML parsing and matching
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
