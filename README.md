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

nexcore-erp/  
├── app/  
│   ├── api/  
│   │   └── v1/  
│   │       ├── health.py        # Health & DB check endpoints  
│   │       ├── products.py      # Product CRUD endpoints  
│   │       └── schemas.py       # Pydantic schemas (API contracts)  
│   │  
│   ├── core/  
│   │   ├── config.py            # Environment & settings loader  
│   │   └── database.py          # SQLAlchemy engine & session  
│   │  
│   ├── models/  
│   │   └── product.py           # Product ORM model  
│   │  
│   └── main.py                  # Application bootstrap  
│  
├── alembic/  
│   ├── versions/                # Database migration files  
│   └── env.py                   # Alembic configuration  
│  
├── docker-compose.yml            # Local PostgreSQL setup  
├── .env                          # Environment variables (ignored)  
├── README.md  
└── ROADMAP.md  

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
