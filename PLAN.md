# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

fastapi-react-skeleton

## Roadmap

### fastapi-react-skeleton — FastAPI + React skeleton with health check

Status: done

Acceptance:
- FastAPI backend runs on port 8000 with /health endpoint
- React + TypeScript + Vite frontend runs on port 5173
- Frontend displays backend health status
- Dockerfiles for both services
- docker-compose.yml with both services

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/api/health.py`, `backend/Dockerfile`, `backend/requirements.txt`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/components/HealthStatus.tsx`, `frontend/src/hooks/useHealth.ts`, `frontend/src/api/client.ts`, `frontend/Dockerfile`, `docker-compose.yml`

Tests: `backend/tests/test_health.py`, `frontend/src/components/HealthStatus.test.tsx`

### core-domain-model — Core domain model for AI-powered CRM entities

Status: planned

Acceptance:
- SQLAlchemy models for Contacts, Companies, Opportunities
- Pydantic schemas for API validation
- Database migrations with Alembic
- CRUD API endpoints

### ai-enrichment-engine — AI enrichment engine for contact/company data

Status: planned

Acceptance:
- Deterministic offline enrichment (no LLM required)
- Optional LLM enrichment with OpenAI-compatible/Anthropic/Gemini adapters
- Provider-agnostic configuration
- Enrichment job queue and status tracking

### auth-oidc-keycloak — OIDC authentication with Keycloak

Status: planned

Acceptance:
- Keycloak realm configuration
- Backend token validation with PyJWT
- Frontend PKCE login flow
- Role-based access control (viewer/operator/admin)

### frontend-dashboard — React dashboard with CRUD workflows

Status: planned

Acceptance:
- Contact list with search/filter/pagination
- Contact create/edit/detail views
- Company and Opportunity views
- Loading/error/empty states
- Export to CSV

