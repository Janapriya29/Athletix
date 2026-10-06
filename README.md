# Athletix — Integrated Sports Performance & Academy Management Platform

A full-stack web application for managing sports academies: athletes, coaches, training sessions, performance assessments, attendance, tournaments, and analytics — all in one place.

---

## Problem Statement

Sports academies typically track athlete performance, attendance, and training using spreadsheets or disconnected tools. Athletix replaces that fragmentation with a single, role-aware platform where admins, coaches, and athletes each have a clear, actionable view of the data that matters to them.

---

## Objectives

- Provide a central system for athlete profile and progress management
- Enable coaches to plan training, record attendance, and assess athlete performance
- Give athletes real-time visibility into their own progress and schedule
- Surface meaningful analytics calculated from real recorded data
- Support multi-sport configuration without code changes

---

## Key Features

| Feature | Description |
|---|---|
| Role-based access | Admin / Coach / Athlete — enforced on the backend |
| Athlete management | Profiles, history, sport/category assignment |
| Coach management | Assignment to athletes and sports |
| Training sessions | Scheduling, status tracking, athlete lists |
| Attendance | Per-session recording with percentage calculation |
| Performance assessments | Configurable sport metrics, 0–100 scale, overall score |
| Performance analytics | Progress charts, trend detection, strength/weakness identification |
| Tournament management | Registration, participation, results |
| Rankings | Sport-filtered athlete rankings from real data |
| Notifications | In-app alerts for key events |
| Reports | Exportable summaries |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, React Router v6, Axios, Recharts |
| Styling | Plain CSS with CSS Modules |
| Backend | Python 3.11, FastAPI, Pydantic v2 |
| Database | MongoDB (via Motor async driver) |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Infrastructure | Docker, Docker Compose |
| Testing | pytest, pytest-asyncio, httpx |

---

## Architecture

```
Browser
  │
  ├── React SPA (Vite / Nginx)
  │     └── Axios → /api/v1/*
  │
  └── FastAPI backend
        ├── JWT auth middleware
        ├── Role-based route guards
        ├── Business logic (services)
        └── Motor → MongoDB
```

See `docs/ARCHITECTURE.md` for the full diagram and layer descriptions.

---

## Project Structure

```
Athletix/
├── frontend/          React + Vite application
├── backend/           FastAPI application
├── scripts/           Admin creation and data seed scripts
├── docs/              Full documentation
├── docker-compose.yml All services
├── .env.example       Environment variable template
└── README.md
```

---

## Setup Instructions

### Prerequisites

- Docker Desktop (recommended)
- OR: Python 3.11, Node.js 20, MongoDB 7

### Option A — Docker (recommended)

```bash
# 1. Clone / copy the project to C:\Users\<you>\Desktop\Athletix
# 2. Copy the environment template
cp .env.example .env
# Edit .env and set a strong JWT_SECRET

# 3. Start all services
docker compose up --build

# 4. Seed development data (first run only)
docker cp scripts athletix_backend:/app/scripts
docker exec athletix_backend python /app/scripts/seed_data.py
# Or if running locally against MongoDB:
# python scripts/seed_data.py

# 5. Open the application
# Frontend: http://localhost
# Backend API docs: http://localhost:8000/docs
```

### Option B — Local development

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env            # edit values
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGO_DB_NAME` | Database name | `athletix` |
| `JWT_SECRET` | Secret key for JWT signing | **must be set** |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `60` |
| `VITE_API_URL` | Frontend API base URL | `/api/v1` |

---

## Seed Data & Default Credentials

After running the seed script, the following development accounts are available:

| Role | Email | Password |
|---|---|---|
| Admin | admin@athletix.dev | Admin@123 |
| Coach | coach1@athletix.dev | Coach@123 |
| Coach | coach2@athletix.dev | Coach@123 |
| Athlete | athlete1@athletix.dev | Athlete@123 |

> These credentials exist only in seed data and documentation. They are never hardcoded into application logic.

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

See `docs/TESTING.md` for full test descriptions and coverage targets.

---

## Docker

```bash
# Start
docker compose up --build

# Stop (preserves data)
docker compose down

# View logs
docker compose logs -f backend

# Health check
curl http://localhost:8000/api/v1/health
```

> Never run `docker compose down -v` unless you intentionally want to delete all stored data.

---

## Documentation

| File | Contents |
|---|---|
| `docs/SRS.md` | Software Requirements Specification |
| `docs/ARCHITECTURE.md` | System architecture and component diagram |
| `docs/DATABASE.md` | MongoDB collections, schemas, and indexes |
| `docs/API.md` | REST API endpoint reference |
| `docs/TESTING.md` | Test strategy, test descriptions, and coverage |
