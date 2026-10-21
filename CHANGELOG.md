# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-10-21

### Added
- FastAPI backend with health check endpoint (`/api/health`)
- React + TypeScript + Vite frontend with health status display
- Dockerfiles for backend and frontend with non-root users
- docker-compose.yml with PostgreSQL, backend, and frontend services
- .env.example with all configuration options
- Backend tests for health endpoints (pytest + httpx)
- Frontend tests for HealthStatus component (vitest + testing-library)
- README with architecture diagram, quick start, and API reference
- MIT License with author attribution

### Infrastructure
- PostgreSQL 16 with health checks
- Nginx reverse proxy for frontend with API proxying
- Health checks on all services
- Development ports bound to 127.0.0.1