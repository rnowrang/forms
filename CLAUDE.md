# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IRB Forms Management System - a web application for managing Institutional Review Board applications with dynamic forms, versioning, review workflows, and document generation.

## Common Commands

### Development with Docker (Recommended)
```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Seed with sample data
docker-compose exec backend python scripts/seed.py

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Backend Development (Local)
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend Development (Local)
```bash
cd frontend
npm install
npm run dev
npm run build      # TypeScript check + build
npm run lint       # ESLint
```

### Database Migrations
```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback one migration
docker-compose exec backend alembic downgrade -1
```

## Architecture

### Backend (FastAPI)
- **Routers** (`app/routers/`): API endpoints organized by domain (auth, forms, templates, review, export, audit, versions)
- **Services** (`app/services/`): Business logic layer - each router has a corresponding service
- **Models** (`app/models/`): SQLAlchemy ORM models
- **Schemas** (`app/schemas/`): Pydantic models for request/response validation

Key patterns:
- All routes use dependency injection for database sessions and current user
- Form workflow states: Draft → In Review → Needs Changes → Approved → Locked
- FormData stores live working state; FormVersion stores immutable snapshots

### Frontend (React + TypeScript)
- **State Management**: Zustand store for auth (`stores/authStore.ts`)
- **Data Fetching**: Axios with interceptors for auth tokens (`lib/api.ts`)
- **Routing**: React Router with ProtectedRoute/PublicRoute wrappers
- **Forms**: React Hook Form + Zod for validation
- **Styling**: TailwindCSS

### Document Generation
Templates use a JSON schema with anchor-based field mapping:
- `anchor.type`: "paragraph", "table_cell", or "table" (for repeatables)
- DocumentService fills DOCX templates using python-docx
- LibreOffice headless converts DOCX to PDF

### Form Schema Structure
```json
{
  "sections": [{ "id": "...", "title": "...", "order": 0 }],
  "fields": [{ "id": "...", "type": "...", "anchor": {...} }],
  "rules": [{ "conditions": [...], "then_actions": [...] }]
}
```
Field types: text, textarea, email, phone, date, select, radio, checkbox, repeatable

## Access Points
- Frontend: http://localhost:5173 (or :3000 via Docker)
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: PostgreSQL on port 5433

## Test Users (after seeding)
- admin@example.com / admin123
- reviewer@example.com / reviewer123
- researcher@example.com / researcher123
