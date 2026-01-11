# Nexcore ERP — Roadmap

This document tracks what has been implemented and what comes next.
It is the source of truth for project continuity across sessions.

---

## DONE

### Foundation
- Project bootstrap (FastAPI + PostgreSQL)
- Environment management (.env + settings)
- Dockerized local database
- SQLAlchemy base configuration
- Alembic migrations setup

### Core Domain
- Product core entity
- Product database table
- Soft delete strategy (`active` flag)

### API
- API versioning (`/api/v1`)
- Health check endpoint
- Database connectivity check
- Product CRUD:
  - Create (POST)
  - Read (GET list)
  - Read by ID (GET /{id})
  - Update (PATCH, partial update)
  - Soft delete via `active=false`

### Tooling
- Swagger/OpenAPI documentation
- Clean project structure
- Consistent commit history

---

## NEXT (SHORT TERM)

### API Improvements
- GET filters (`?active=true`)
- Pagination for list endpoints
- Standardized error responses
- Dependency injection for DB sessions

### Data Model
- Add audit fields:
  - created_at
  - updated_at
- Enforce unique constraints and indexes

---

## MID TERM

### New Core Entities
- Client
- Supplier
- Stock / Inventory
- Orders (Sales / Purchase)

### Security
- Authentication (JWT)
- Role-based access control
- Protected endpoints

### Quality
- Unit tests for core services
- API contract validation
- Linting and formatting standards

---

## LONG TERM

### Architecture
- Multi-tenant support
- Background jobs (async tasks)
- Event-driven patterns

### Integration
- Legacy database migration layer
- External service integrations
- Webhook support

### Deployment
- Cloud deployment (AWS / GCP)
- CI/CD pipeline
- Environment separation (dev / staging / prod)
