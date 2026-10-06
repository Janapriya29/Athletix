# Database Design — Athletix

**Database:** MongoDB 7  
**Driver:** Motor 3 (async)

---

## Collections

### `users`

Stores all user accounts regardless of role.

```json
{
  "_id": ObjectId,
  "email": "string (unique)",
  "hashed_password": "string",
  "full_name": "string",
  "role": "admin | coach | athlete",
  "is_active": true,
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**Indexes:** `email` (unique)

---

### `sports`

Configurable sports. Seeded with 5 initial entries.

```json
{
  "_id": ObjectId,
  "name": "string",
  "description": "string",
  "is_active": true,
  "created_at": ISODate
}
```

---

### `categories`

Performance metric categories per sport.

```json
{
  "_id": ObjectId,
  "sport_id": ObjectId,
  "name": "string",
  "description": "string",
  "created_at": ISODate
}
```

**Examples:**  
Football → Speed, Passing, Shooting, Dribbling, Endurance  
Cricket → Batting, Bowling, Fielding, Endurance

---

### `athletes`

Extended profile for users with role `athlete`.

```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "full_name": "string",
  "email": "string",
  "phone": "string",
  "date_of_birth": ISODate,
  "gender": "male | female | other",
  "sport_id": ObjectId,
  "joining_date": ISODate,
  "emergency_contact": "string",
  "profile_photo_url": "string (optional)",
  "status": "active | inactive",
  "coach_id": ObjectId,
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**Indexes:** `user_id`, `sport_id`

---

### `coaches`

Extended profile for users with role `coach`.

```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "full_name": "string",
  "email": "string",
  "phone": "string",
  "sport_ids": [ObjectId],
  "bio": "string",
  "status": "active | inactive",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**Indexes:** `user_id`

---

### `coach_athlete_assignments`

Explicit assignment table for coach ↔ athlete relationships.

```json
{
  "_id": ObjectId,
  "coach_id": ObjectId,
  "athlete_id": ObjectId,
  "assigned_at": ISODate
}
```

**Indexes:** `(coach_id, athlete_id)` (unique compound)

---

### `training_sessions`

A training event planned or delivered by a coach.

```json
{
  "_id": ObjectId,
  "title": "string",
  "sport_id": ObjectId,
  "coach_id": ObjectId,
  "date": ISODate,
  "start_time": "HH:MM",
  "end_time": "HH:MM",
  "venue": "string",
  "objectives": "string",
  "athlete_ids": [ObjectId],
  "status": "scheduled | completed | cancelled",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**Indexes:** `date`, `coach_id`

---

### `attendance`

One document per athlete per training session.

```json
{
  "_id": ObjectId,
  "session_id": ObjectId,
  "athlete_id": ObjectId,
  "status": "present | absent | late",
  "recorded_by": ObjectId,
  "recorded_at": ISODate
}
```

**Indexes:** `(session_id, athlete_id)` (unique compound), `athlete_id`

---

### `performance_assessments`

A set of metric scores recorded by a coach for one athlete.

```json
{
  "_id": ObjectId,
  "athlete_id": ObjectId,
  "coach_id": ObjectId,
  "sport_id": ObjectId,
  "date": ISODate,
  "metrics": {
    "speed": 82,
    "agility": 76,
    "endurance": 88,
    "strength": 80,
    "technique": 84
  },
  "overall_score": 82.0,
  "remarks": "string",
  "created_at": ISODate
}
```

**Indexes:** `(athlete_id, date DESC)`

---

### `tournaments`

An event that athletes can participate in.

```json
{
  "_id": ObjectId,
  "name": "string",
  "sport_id": ObjectId,
  "venue": "string",
  "start_date": ISODate,
  "end_date": ISODate,
  "description": "string",
  "status": "upcoming | ongoing | completed",
  "created_by": ObjectId,
  "created_at": ISODate
}
```

**Indexes:** `start_date`

---

### `tournament_participants`

One document per athlete per tournament.

```json
{
  "_id": ObjectId,
  "tournament_id": ObjectId,
  "athlete_id": ObjectId,
  "event": "string (optional)",
  "status": "registered | participated | withdrawn",
  "position": "number (optional)",
  "score": "string (optional)",
  "points": "float (optional)",
  "medal": "Gold | Silver | Bronze (optional)",
  "remarks": "string (optional)",
  "result_date": "ISODate (optional)",
  "recorded_by": "ObjectId (optional)",
  "registered_by": "ObjectId (optional)",
  "registered_at": ISODate,
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**Indexes:** `(tournament_id, athlete_id)`

---

### `notifications`

In-app notifications per user.

```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "title": "string",
  "message": "string",
  "type": "training | attendance | assessment | tournament | system",
  "is_read": false,
  "created_at": ISODate
}
```

**Indexes:** `(user_id, is_read)`

---

## Relationships Summary

```
users  ──── athletes (user_id)
users  ──── coaches  (user_id)
sports ──── categories (sport_id)
sports ──── athletes   (sport_id)
coaches ─── athletes   (coach_id in athletes)
coaches ─── coach_athlete_assignments (coach_id)
athletes ── coach_athlete_assignments (athlete_id)
coaches ─── training_sessions (coach_id)
athletes ── training_sessions (athlete_ids array)
training_sessions ── attendance (session_id)
athletes ── attendance (athlete_id)
athletes ── performance_assessments (athlete_id)
sports ──── tournaments (sport_id)
athletes ── tournament_participants (athlete_id)
tournaments ─ tournament_participants (tournament_id)
users ──── notifications (user_id)
```

---

## Index Summary

| Collection | Index | Type |
|---|---|---|
| users | email | unique |
| athletes | user_id | single |
| athletes | sport_id | single |
| coaches | user_id | single |
| coach_athlete_assignments | (coach_id, athlete_id) | unique compound |
| training_sessions | date | single |
| training_sessions | coach_id | single |
| attendance | (session_id, athlete_id) | unique compound |
| attendance | athlete_id | single |
| performance_assessments | (athlete_id, date DESC) | compound |
| tournaments | start_date | single |
| tournament_participants | (tournament_id, athlete_id) | compound |
| notifications | (user_id, is_read) | compound |
