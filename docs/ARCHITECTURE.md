# Architecture — Athletix

---

## System Overview

Athletix is a three-tier web application:

```
┌────────────────────────────────────────────────────────┐
│                     Browser / Client                   │
│                                                        │
│   React SPA (Vite)                                     │
│   ├── React Router (client-side routing)               │
│   ├── Axios (HTTP client)                              │
│   ├── AuthContext (JWT storage + refresh)              │
│   └── Recharts (data visualization)                    │
└──────────────────────┬─────────────────────────────────┘
                       │  HTTP/JSON  (port 80 in Docker,
                       │  proxied via nginx or Vite dev proxy)
┌──────────────────────▼─────────────────────────────────┐
│                    FastAPI Backend                      │
│                                                        │
│   app/main.py        — CORS, lifespan, router mount    │
│   app/core/          — config, security, dependencies  │
│   app/api/v1/        — route handlers (thin layer)     │
│   app/services/      — business logic                  │
│   app/repositories/  — MongoDB query layer             │
│   app/schemas/       — Pydantic request/response models│
│   app/models/        — internal data models            │
│   app/analytics/     — performance calculations        │
└──────────────────────┬─────────────────────────────────┘
                       │  Motor (async)
┌──────────────────────▼─────────────────────────────────┐
│                     MongoDB 7                          │
│                                                        │
│   Named volume: athletix_mongo_data                    │
│   Collections: users, athletes, coaches, sports,       │
│   training_sessions, attendance,                       │
│   performance_assessments, tournaments,                │
│   tournament_participants, notifications,              │
│   coach_athlete_assignments, categories                │
└────────────────────────────────────────────────────────┘
```

---

## Docker Compose Services

| Service | Image | Port | Role |
|---|---|---|---|
| `mongodb` | mongo:7.0 | 27017 | Persistent data store |
| `backend` | python:3.11-slim (built) | 8000 | FastAPI REST API |
| `frontend` | node:20-alpine + nginx:1.25-alpine | 80 | React SPA served by Nginx |

Startup order: `mongodb` → `backend` (waits for mongo healthcheck) → `frontend` (waits for backend healthcheck).

---

## Backend Layer Responsibilities

### `app/api/v1/endpoints/`
Route handlers only. Each handler:
1. Validates the request via Pydantic schema
2. Calls a service function
3. Returns a response schema

No business logic lives here.

### `app/services/`
Business logic. Services:
- Coordinate calls to repositories
- Apply rules (e.g., calculate overall score, check attendance threshold)
- Do not access the database directly

### `app/repositories/`
Database access. Repositories:
- Contain all Motor/MongoDB queries
- Return plain dicts or model instances
- Are the only layer that imports `get_database()`

### `app/core/`
Cross-cutting concerns:
- `config.py` — pydantic-settings, reads `.env`
- `security.py` — password hashing, JWT encode/decode
- `dependencies.py` — FastAPI `Depends()` for auth + role enforcement
- `exceptions.py` — typed HTTP exceptions

### `app/analytics/`
Pure calculation functions. Accept data structures and return analytics results. No database calls. Designed to be testable in isolation.

### `app/schemas/`
Pydantic v2 models. Separate `Request`, `Response`, and `DB` variants where needed.

---

## Frontend Architecture

```
src/
├── main.jsx          Entry point, BrowserRouter
├── App.jsx           Route definitions, AuthProvider wrapper
├── context/
│   └── AuthContext   User state, login/logout, token management
├── routes/
│   └── ProtectedRoute  Role-gated route wrapper
├── layouts/
│   ├── AppLayout     Sidebar + main content shell
│   ├── Sidebar       Role-aware navigation
│   └── Topbar        Page title + user info
├── pages/            One file per route, grouped by role
├── components/       Reusable UI pieces (cards, charts, forms)
├── services/         Axios calls, one file per API domain
├── hooks/            Custom React hooks (e.g., useAthletes)
├── utils/            Pure helper functions (formatDate, etc.)
└── styles/           global.css with CSS custom properties
```

### State Management

Athletix does not use a global state library. State lives:
- In `AuthContext` for the authenticated user
- In component-local `useState` / `useEffect` for page data
- Custom hooks abstract repeated fetch + loading + error patterns

---

## Authentication Flow

```
User submits email + password
        │
        ▼
POST /api/v1/auth/login
        │  (FastAPI OAuth2PasswordRequestForm)
        ▼
Verify email exists → verify bcrypt hash
        │
        ▼
Create JWT { sub: user_id, role, email, exp }
        │
        ▼
Return { access_token, token_type }
        │
        ▼
Frontend stores token in localStorage
        │
        ▼
GET /api/v1/auth/me  (Bearer token)
        │
        ▼
Decode JWT → fetch user document → return user profile
        │
        ▼
AuthContext sets user → React Router redirects to dashboard
```

---

## Role Enforcement

Role checks happen in `app/core/dependencies.py`.

```python
require_admin  = require_role("admin")
require_coach  = require_role("admin", "coach")
require_athlete = require_role("admin", "coach", "athlete")
```

Each endpoint declares the appropriate dependency:

```python
@router.get("/athletes")
async def list_athletes(current_user = Depends(require_coach)):
    ...
```

The frontend hides navigation items for inappropriate roles, but the backend enforces authorization independently. A user who guesses a URL and supplies a valid token for the wrong role receives HTTP 403.

---

## Performance Analytics Design

Analytics are calculated on-demand by the backend from stored assessment records.

Improvement % = ((current_overall - previous_overall) / previous_overall) × 100

Strongest metric = metric with the highest value in the latest assessment  
Weakest metric  = metric with the lowest value in the latest assessment

These calculations live in `app/analytics/performance.py` as pure functions so they can be unit-tested without a database.

---

## Tournaments & Rankings Design (Phase 6)

### Tournament Lifecycle & Participation
1. **Creation:** Admins create tournaments with title, sport, date ranges, and registration deadlines.
2. **Registration:**
   - Admins can register any active academy athlete.
   - Coaches can register only their assigned athletes (enforced at repository & service layers).
   - Athletes can self-register or withdraw prior to the tournament start.
3. **Results:**
   - Recorded by Admin or assigned Coach. Athletes are forbidden from modifying results (HTTP 403).
   - Standard derivations: Position 1 -> Gold (10 pts), Position 2 -> Silver (5 pts), Position 3 -> Bronze (3 pts), default 1 pt for participation. Custom points and scores supported.

### Leaderboard & Ranking Engines
Rankings are calculated dynamically from real MongoDB collections without duplicating state:
1. **Tournament / Points:** Sum of points across tournament records, gold/silver/bronze medal tallies.
   - Tie-breaking: `(-points, -gold_count, -silver_count, -bronze_count, athlete_name.lower())`
2. **Performance:** Latest assessment `overall_score` (from Phase 5).
   - Tie-breaking: `(-performance_score, athlete_name.lower())`
3. **Attendance:** Attendance percentage based on Phase 3 formula `(Present + Late) / Total Applicable * 100`, excluding cancelled training sessions.
   - Tie-breaking: `(-attendance_percentage, athlete_name.lower())`
4. **Improvement:** Growth percentage `((current - previous) / previous) * 100` between consecutive assessments. Requires >= 2 assessments.
   - Tie-breaking: `(-improvement_percentage, athlete_name.lower())`
5. **Sport Filtering:** All rankings support academy-wide views and sport-filtered leaderboards via `sport_id`.

