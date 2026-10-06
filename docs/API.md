# API Reference — Athletix

**Base URL:** `/api/v1`  
**Auth:** Bearer JWT token in `Authorization` header  
**Format:** All request and response bodies are JSON

---

## Authentication

### POST /auth/login
Authenticate and receive a JWT token.

**Request** (`application/x-www-form-urlencoded`)
```
username=email@example.com&password=secret
```

**Response 200**
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

**Errors:** 401 — wrong credentials

---

### POST /auth/logout
Invalidates the session on the client. The server acknowledges the request.

**Auth required:** Yes

**Response 200**
```json
{ "message": "Logged out successfully" }
```

---

### GET /auth/me
Returns the authenticated user's profile.

**Auth required:** Yes

**Response 200**
```json
{
  "id": "string",
  "email": "string",
  "full_name": "string",
  "role": "admin | coach | athlete",
  "is_active": true
}
```

---

### POST /auth/change-password
**Auth required:** Yes

**Request**
```json
{ "current_password": "string", "new_password": "string" }
```

**Response 200**
```json
{ "message": "Password updated successfully" }
```

---

## Users

### GET /users
List all users. **Admin only.**

### POST /users
Create a user. **Admin only.**

**Request**
```json
{
  "email": "string",
  "full_name": "string",
  "password": "string",
  "role": "admin | coach | athlete"
}
```

### GET /users/{id}
Get a user by ID. **Admin only.**

### PUT /users/{id}
Update a user. **Admin only.**

### PATCH /users/{id}/status
Activate or deactivate a user. **Admin only.**

---

## Sports

### GET /sports
List all sports. **All authenticated roles.**

### POST /sports
Create a sport. **Admin only.**

### GET /sports/{id}
Get a sport with its categories. **All roles.**

### PUT /sports/{id}
Update a sport. **Admin only.**

### POST /sports/{id}/categories
Add a category/metric to a sport. **Admin only.**

---

## Athletes

### GET /athletes
List athletes. **Admin sees all; Coach sees assigned; Athlete sees self.**

### POST /athletes
Create an athlete profile. **Admin only.**

### GET /athletes/{id}
Get an athlete. **Admin, assigned Coach, or the Athlete themselves.**

### PUT /athletes/{id}
Update an athlete. **Admin only.**

### GET /athletes/{id}/history
Get the full performance and attendance history for an athlete.

---

## Coaches

### GET /coaches
List all coaches. **Admin only.**

### POST /coaches
Create a coach profile. **Admin only.**

### GET /coaches/{id}
Get a coach. **Admin or the Coach themselves.**

### PUT /coaches/{id}
Update a coach. **Admin only.**

### POST /coaches/{id}/athletes
Assign athletes to a coach. **Admin only.**

### DELETE /coaches/{id}/athletes/{athlete_id}
Remove an athlete assignment. **Admin only.**

---

## Training Sessions

### GET /training
List sessions. **Coach sees own; Admin sees all; Athlete sees assigned.**

### POST /training
Create a session. **Coach or Admin.**

**Request**
```json
{
  "title": "string",
  "sport_id": "string",
  "date": "YYYY-MM-DD",
  "start_time": "HH:MM",
  "end_time": "HH:MM",
  "venue": "string",
  "objectives": "string",
  "athlete_ids": ["string"]
}
```

### GET /training/{id}
Get a session with its athlete list.

### PUT /training/{id}
Update a session. **Coach (own sessions) or Admin.**

### PATCH /training/{id}/status
Update session status (scheduled/completed/cancelled). **Coach or Admin.**

---

## Attendance

### GET /attendance
List attendance records. Filterable by `session_id` or `athlete_id`.

### POST /attendance
Record attendance for a session. **Coach or Admin.**

**Request**
```json
{
  "session_id": "string",
  "records": [
    { "athlete_id": "string", "status": "present | absent | late" }
  ]
}
```

### GET /attendance/athlete/{athlete_id}/summary
Returns total sessions, attended, absent, and attendance percentage.

---

## Performance Assessments

### GET /assessments
List assessments. **Coach sees for assigned athletes; Athlete sees own.**

### POST /assessments
Create an assessment. **Coach only.**

**Request**
```json
{
  "athlete_id": "string",
  "sport_id": "string",
  "date": "YYYY-MM-DD",
  "metrics": { "speed": 82, "agility": 76, "endurance": 88 },
  "remarks": "string"
}
```

The `overall_score` is calculated by the backend as the mean of metric values.

### GET /assessments/{id}
Get a single assessment.

### GET /assessments/athlete/{athlete_id}
Get all assessments for one athlete, ordered by date descending.

---

## Analytics

### GET /analytics/athlete/{athlete_id}
Returns performance analytics calculated from real assessment data.

**Response**
```json
{
  "current_score": 82.0,
  "previous_score": 75.6,
  "improvement_pct": 8.47,
  "attendance_pct": 91.3,
  "assessment_count": 5,
  "strongest_metric": "endurance",
  "weakest_metric": "agility",
  "trend": "improving",
  "insight": "Overall performance improved by 8.5% compared with the previous assessment.",
  "history": [ { "date": "2026-09-01", "overall_score": 75.6, "metrics": {} } ]
}
```

If fewer than 2 assessments: `"insight": "Not enough assessment history yet."`

---

## Tournaments

### GET /tournaments
List tournaments. **All roles.**

### POST /tournaments
Create a tournament. **Admin only.**

### GET /tournaments/{id}
Get tournament details including participants.

### PUT /tournaments/{id}
Update a tournament. **Admin only.**

### POST /tournaments/{id}/register
Register an athlete for a tournament. **Admin or Coach.**

### POST /tournaments/{id}/results
Record a result for a participant. **Admin or Coach.**

### GET /tournaments/athlete/{athlete_id}
Get all tournaments an athlete participated in.

---

## Rankings

### GET /rankings
Returns athletes ranked by overall performance score.

**Query params:**
- `sport_id` (optional) — filter by sport
- `limit` (optional, default 20)

**Response**
```json
[
  { "rank": 1, "athlete_name": "string", "sport": "string", "score": 91.2, "assessments": 6 }
]
```

---

## Notifications

### GET /notifications
Returns notifications for the authenticated user.

### PATCH /notifications/{id}/read
Mark a notification as read.

### PATCH /notifications/read-all
Mark all notifications as read.

### GET /notifications/unread-count
Returns `{ "count": 3 }`.

---

## Reports

### GET /reports/overview
Academy-wide summary. **Admin only.**

Returns: total athletes, coaches, sports, average performance score, average attendance.

### GET /reports/athletes
Per-athlete summary list. **Admin only.**

---

## Performance Analytics (Phase 5)

### GET /analytics/athlete/me
Returns personal performance and attendance analytics for the authenticated athlete.
**Auth required:** Yes (Athlete role)

### GET /analytics/athlete/{athlete_id}
Returns full performance analytics for an athlete.
**Auth required:** Yes (Admin, assigned Coach, or Athlete themselves)

### GET /analytics/coach/summary
Returns aggregate performance and attendance analytics for coach's assigned athletes.
**Auth required:** Yes (Coach role)

### GET /analytics/coach/athletes
Returns list of assigned athletes with performance score, trend, and attendance metrics.
**Query params:** `sport_id` (optional)
**Auth required:** Yes (Coach role)

### GET /analytics/admin/summary
Returns academy-wide totals, averages, and trend counts.
**Auth required:** Yes (Admin role)

### GET /analytics/admin/sports
Returns sport-wise performance and attendance breakdown.
**Auth required:** Yes (Admin role)

---

## Tournaments & Rankings (Phase 6)

### Tournaments

#### GET /tournaments
List all tournaments.
- **Auth required:** Yes (All roles)
- **Query params:** `search`, `sport_id`, `status`, `start_date`, `end_date`, `skip`, `limit`

#### POST /tournaments
Create a new tournament.
- **Auth required:** Yes (Admin only)
- **Status:** 201 Created

#### GET /tournaments/{tournament_id}
Get tournament details and participant count.
- **Auth required:** Yes (All roles)

#### PUT /tournaments/{tournament_id}
Update tournament details.
- **Auth required:** Yes (Admin only)

#### DELETE /tournaments/{tournament_id}
Delete a tournament and its participant records.
- **Auth required:** Yes (Admin only)

### Tournament Participation

#### GET /tournaments/{tournament_id}/participants
List all registered participants and their recorded results.
- **Auth required:** Yes (All roles)

#### POST /tournaments/{tournament_id}/participants
Register an athlete for a tournament.
- **Auth required:** Yes
- **Permissions:** Admin (any active athlete), Coach (assigned athletes only), Athlete (self only)
- **Status:** 201 Created

#### DELETE /tournaments/{tournament_id}/participants/{athlete_id}
Withdraw an athlete from a tournament.
- **Auth required:** Yes
- **Permissions:** Admin, Coach (assigned athletes only), Athlete (self only)

### Tournament Results

#### GET /tournaments/{tournament_id}/results
Get all results for a tournament.
- **Auth required:** Yes (All roles)

#### POST /tournaments/{tournament_id}/results
Record an athlete's result (position, score, medal, points, remarks).
- **Auth required:** Yes
- **Permissions:** Admin, Coach (assigned athletes only). Athlete is 403 Forbidden.

#### PUT /tournaments/{tournament_id}/results/{athlete_id}
Update an athlete's result.
- **Auth required:** Yes
- **Permissions:** Admin, Coach (assigned athletes only). Athlete is 403 Forbidden.

### Athlete Tournament History

#### GET /athletes/me/tournaments
Personal tournament competition history.
- **Auth required:** Yes (Athlete role)

#### GET /tournaments/history/{athlete_id}
Tournament history for a specific athlete.
- **Auth required:** Yes (Admin, assigned Coach, or Athlete themselves)

### Rankings

#### GET /rankings
Unified rankings endpoint.
- **Auth required:** Yes (All authenticated users)
- **Query params:** `type` (tournament | performance | attendance | improvement), `sport_id` (optional)

#### GET /rankings/tournament
Tournament points & medal rankings with deterministic tie-breaking (Points -> Gold -> Silver -> Bronze -> Athlete name).
- **Auth required:** Yes (All authenticated users)
- **Query params:** `sport_id` (optional)

#### GET /rankings/performance
Performance score rankings based on latest Phase 5 assessment score.
- **Auth required:** Yes (All authenticated users)
- **Query params:** `sport_id` (optional)

#### GET /rankings/attendance
Attendance percentage rankings based on Phase 3 training attendance (cancelled sessions excluded).
- **Auth required:** Yes (All authenticated users)
- **Query params:** `sport_id` (optional)

#### GET /rankings/improvement
Improvement percentage rankings based on Phase 5 assessment progression (requires >= 2 assessments).
- **Auth required:** Yes (All authenticated users)
- **Query params:** `sport_id` (optional)

---

## Notifications (Phase 7)

### GET /notifications
List in-app notifications for the authenticated user.
- **Auth required:** Yes (All authenticated users)
- **Query params:** `unread: bool` (optional), `type: str` (training | performance | tournament | general), `skip: int`, `limit: int`

### GET /notifications/unread-count
Get unread notification count for the authenticated user.
- **Auth required:** Yes (All authenticated users)

### PATCH /notifications/{notification_id}/read
Mark a specific notification as read.
- **Auth required:** Yes (Notification recipient only — enforces ownership)

### PATCH /notifications/read-all
Mark all notifications for the authenticated user as read.
- **Auth required:** Yes (All authenticated users)

### DELETE /notifications/{notification_id}
Delete a specific notification.
- **Auth required:** Yes (Notification recipient only — enforces ownership)

---

## Reports (Phase 7)

### GET /reports/athlete/{athlete_id}/performance
Get comprehensive performance report for an athlete (current/previous score, improvement %, trend, strongest/weakest metrics, history).
- **Auth required:** Yes (Admin, assigned Coach, Athlete self)

### GET /reports/athlete/{athlete_id}/attendance
Get detailed attendance report for an athlete (total sessions, attended, percentage, warning below 75%, history). Excludes cancelled sessions.
- **Auth required:** Yes (Admin, assigned Coach, Athlete self)

### GET /reports/athlete/{athlete_id}/tournaments
Get tournament history, medals tally, and points for an athlete.
- **Auth required:** Yes (Admin, assigned Coach, Athlete self)

### GET /reports/athlete/{athlete_id}/development
Aggregated athlete development summary (profile, attendance summary, performance metrics, tournament achievements).
- **Auth required:** Yes (Admin, assigned Coach, Athlete self)

### GET /reports/academy/summary
Academy-wide executive summary report across athletes, coaches, sports, sessions, attendance rate, assessments, average scores, tournaments, and medals.
- **Auth required:** Yes (Admin only)

### GET /reports/attendance
Team/academy attendance report across athletes.
- **Auth required:** Yes (Admin: all athletes; Coach: assigned athletes)
- **Query params:** `sport_id` (optional), `format=csv` (optional for CSV export)

### GET /reports/tournaments
Tournaments summary report with medalists and participation counts.
- **Auth required:** Yes (Admin, Coach)
- **Query params:** `sport_id` (optional), `format=csv` (optional for CSV export)

---

## Health

### GET /health
Returns application and database status. No auth required.

```json
{ "status": "ok", "app": "Athletix", "version": "1.0.0", "database": "connected" }
```

