"""
seed_data.py — Populate the database with consistent development data.

Inserts:
  - 5 sports with metric categories
  - 1 admin user
  - 2 coaches
  - 8 athletes (across sports)
  - coach-athlete assignments
  - 10 training sessions
  - attendance records
  - performance assessments (3-4 per athlete)
  - 2 tournaments with participants and results
  - notifications

Safe to re-run: checks for existing data before inserting.

Usage (local):
    cd backend
    python ../scripts/seed_data.py

Usage (Docker):
    docker exec athletix_backend python scripts/seed_data.py
"""

import asyncio
import os
import sys
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

import bcrypt as _bcrypt
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "athletix")


def _hash(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

now = datetime.now(timezone.utc)


def dt(days_offset: int = 0) -> datetime:
    return now + timedelta(days=days_offset)


def oid() -> ObjectId:
    return ObjectId()


# ── Sport definitions ──────────────────────────────────────────────────────────

SPORTS_DEF = [
    {
        "name": "Football",
        "description": "Association football (soccer)",
        "metrics": ["Speed", "Passing", "Shooting", "Dribbling", "Endurance"],
    },
    {
        "name": "Cricket",
        "description": "Bat-and-ball team sport",
        "metrics": ["Batting", "Bowling", "Fielding", "Endurance"],
    },
    {
        "name": "Badminton",
        "description": "Racquet sport",
        "metrics": ["Agility", "Speed", "Smash", "Footwork", "Endurance"],
    },
    {
        "name": "Basketball",
        "description": "Team basketball",
        "metrics": ["Shooting", "Dribbling", "Passing", "Speed", "Vertical Jump"],
    },
    {
        "name": "Athletics",
        "description": "Track and field events",
        "metrics": ["Sprint", "Endurance", "Long Jump", "Strength"],
    },
]


async def seed(db):
    print("\n=== Athletix Seed Data ===\n")

    # ── 1. Sports & categories ─────────────────────────────────────────────────
    sport_ids = {}
    for sport_def in SPORTS_DEF:
        existing = await db.sports.find_one({"name": sport_def["name"]})
        if existing:
            sport_ids[sport_def["name"]] = existing["_id"]
            print(f"  Sport already exists: {sport_def['name']}")
            continue

        s_id = oid()
        await db.sports.insert_one({
            "_id": s_id,
            "name": sport_def["name"],
            "description": sport_def["description"],
            "is_active": True,
            "created_at": now,
        })
        sport_ids[sport_def["name"]] = s_id

        for metric_name in sport_def["metrics"]:
            await db.categories.insert_one({
                "_id": oid(),
                "sport_id": s_id,
                "name": metric_name,
                "description": f"{metric_name} performance metric",
                "created_at": now,
            })
        print(f"  Created sport: {sport_def['name']} ({len(sport_def['metrics'])} metrics)")

    # ── 2. Users ───────────────────────────────────────────────────────────────
    users_def = [
        {"email": "admin@athletix.dev",    "full_name": "Academy Admin",   "role": "admin",   "password": "Admin@123"},
        {"email": "coach1@athletix.dev",   "full_name": "Sarah Mitchell",  "role": "coach",   "password": "Coach@123"},
        {"email": "coach2@athletix.dev",   "full_name": "James Fernandez", "role": "coach",   "password": "Coach@123"},
        {"email": "athlete1@athletix.dev", "full_name": "Rahul Sharma",    "role": "athlete", "password": "Athlete@123"},
        {"email": "athlete2@athletix.dev", "full_name": "Priya Nair",      "role": "athlete", "password": "Athlete@123"},
        {"email": "athlete3@athletix.dev", "full_name": "David Okonkwo",   "role": "athlete", "password": "Athlete@123"},
        {"email": "athlete4@athletix.dev", "full_name": "Emma Walsh",      "role": "athlete", "password": "Athlete@123"},
        {"email": "athlete5@athletix.dev", "full_name": "Arjun Patel",     "role": "athlete", "password": "Athlete@123"},
        {"email": "athlete6@athletix.dev", "full_name": "Sofia Reyes",     "role": "athlete", "password": "Athlete@123"},
        {"email": "athlete7@athletix.dev", "full_name": "Michael Chen",    "role": "athlete", "password": "Athlete@123"},
        {"email": "athlete8@athletix.dev", "full_name": "Amira Hassan",    "role": "athlete", "password": "Athlete@123"},
    ]

    user_ids = {}
    for u in users_def:
        existing = await db.users.find_one({"email": u["email"]})
        if existing:
            user_ids[u["email"]] = existing["_id"]
            print(f"  User already exists: {u['email']}")
            continue
        u_id = oid()
        await db.users.insert_one({
            "_id": u_id,
            "email": u["email"],
            "hashed_password": _hash(u["password"]),
            "full_name": u["full_name"],
            "role": u["role"],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        })
        user_ids[u["email"]] = u_id
        print(f"  Created user: {u['email']} ({u['role']})")

    # ── 3. Coach profiles ──────────────────────────────────────────────────────
    coach_ids = {}
    coaches_def = [
        {
            "email": "coach1@athletix.dev",
            "sport_names": ["Football", "Athletics"],
            "phone": "+44 7700 900001",
            "bio": "UEFA B licensed coach with 8 years of academy experience.",
        },
        {
            "email": "coach2@athletix.dev",
            "sport_names": ["Cricket", "Badminton", "Basketball"],
            "phone": "+44 7700 900002",
            "bio": "Former professional cricketer, specialist in batting technique.",
        },
    ]
    for cd in coaches_def:
        existing = await db.coaches.find_one({"user_id": user_ids[cd["email"]]})
        if existing:
            coach_ids[cd["email"]] = existing["_id"]
            print(f"  Coach profile already exists: {cd['email']}")
            continue
        c_id = oid()
        await db.coaches.insert_one({
            "_id": c_id,
            "user_id": user_ids[cd["email"]],
            "full_name": next(u["full_name"] for u in users_def if u["email"] == cd["email"]),
            "email": cd["email"],
            "phone": cd["phone"],
            "sport_ids": [sport_ids[s] for s in cd["sport_names"]],
            "bio": cd["bio"],
            "status": "active",
            "created_at": now,
            "updated_at": now,
        })
        coach_ids[cd["email"]] = c_id
        print(f"  Created coach profile: {cd['email']}")

    # ── 4. Athlete profiles ────────────────────────────────────────────────────
    athletes_def = [
        {"email": "athlete1@athletix.dev", "sport": "Football",   "dob": date(2004, 3, 15), "gender": "male",   "coach": "coach1@athletix.dev", "phone": "+91 98000 00001"},
        {"email": "athlete2@athletix.dev", "sport": "Football",   "dob": date(2005, 7, 22), "gender": "female", "coach": "coach1@athletix.dev", "phone": "+91 98000 00002"},
        {"email": "athlete3@athletix.dev", "sport": "Cricket",    "dob": date(2003, 11, 8), "gender": "male",   "coach": "coach2@athletix.dev", "phone": "+91 98000 00003"},
        {"email": "athlete4@athletix.dev", "sport": "Cricket",    "dob": date(2004, 5, 19), "gender": "female", "coach": "coach2@athletix.dev", "phone": "+91 98000 00004"},
        {"email": "athlete5@athletix.dev", "sport": "Badminton",  "dob": date(2005, 1, 30), "gender": "male",   "coach": "coach2@athletix.dev", "phone": "+91 98000 00005"},
        {"email": "athlete6@athletix.dev", "sport": "Basketball", "dob": date(2003, 9, 14), "gender": "female", "coach": "coach2@athletix.dev", "phone": "+91 98000 00006"},
        {"email": "athlete7@athletix.dev", "sport": "Athletics",  "dob": date(2004, 6, 3),  "gender": "male",   "coach": "coach1@athletix.dev", "phone": "+91 98000 00007"},
        {"email": "athlete8@athletix.dev", "sport": "Athletics",  "dob": date(2005, 12, 11),"gender": "female", "coach": "coach1@athletix.dev", "phone": "+91 98000 00008"},
    ]

    athlete_ids = {}
    for ad in athletes_def:
        existing = await db.athletes.find_one({"user_id": user_ids[ad["email"]]})
        if existing:
            athlete_ids[ad["email"]] = existing["_id"]
            print(f"  Athlete profile already exists: {ad['email']}")
            continue
        a_id = oid()
        full_name = next(u["full_name"] for u in users_def if u["email"] == ad["email"])
        await db.athletes.insert_one({
            "_id": a_id,
            "user_id": user_ids[ad["email"]],
            "full_name": full_name,
            "email": ad["email"],
            "phone": ad["phone"],
            "date_of_birth": datetime.combine(ad["dob"], datetime.min.time()).replace(tzinfo=timezone.utc),
            "gender": ad["gender"],
            "sport_id": sport_ids[ad["sport"]],
            "joining_date": dt(-180),
            "emergency_contact": f"Parent of {full_name}: +91 99900 00000",
            "profile_photo_url": None,
            "status": "active",
            "coach_id": coach_ids[ad["coach"]],
            "created_at": now,
            "updated_at": now,
        })
        athlete_ids[ad["email"]] = a_id
        print(f"  Created athlete profile: {ad['email']}")

    # ── 5. Coach-athlete assignments ───────────────────────────────────────────
    assignments = [
        ("coach1@athletix.dev", ["athlete1@athletix.dev", "athlete2@athletix.dev", "athlete7@athletix.dev", "athlete8@athletix.dev"]),
        ("coach2@athletix.dev", ["athlete3@athletix.dev", "athlete4@athletix.dev", "athlete5@athletix.dev", "athlete6@athletix.dev"]),
    ]
    for coach_email, ath_emails in assignments:
        for ath_email in ath_emails:
            existing = await db.coach_athlete_assignments.find_one({
                "coach_id": coach_ids[coach_email],
                "athlete_id": athlete_ids[ath_email],
            })
            if not existing:
                await db.coach_athlete_assignments.insert_one({
                    "_id": oid(),
                    "coach_id": coach_ids[coach_email],
                    "athlete_id": athlete_ids[ath_email],
                    "assigned_at": now,
                })
    print("  Coach-athlete assignments created.")

    # ── 6. Training sessions ───────────────────────────────────────────────────
    sessions_def = [
        # Coach 1 — Football / Athletics sessions
        {"title": "Football Drills — Passing", "sport": "Football", "coach": "coach1@athletix.dev",
         "date_offset": -14, "athletes": ["athlete1@athletix.dev", "athlete2@athletix.dev"], "status": "completed"},
        {"title": "Football Drills — Shooting", "sport": "Football", "coach": "coach1@athletix.dev",
         "date_offset": -7, "athletes": ["athlete1@athletix.dev", "athlete2@athletix.dev"], "status": "completed"},
        {"title": "Athletics — Sprint Training", "sport": "Athletics", "coach": "coach1@athletix.dev",
         "date_offset": -10, "athletes": ["athlete7@athletix.dev", "athlete8@athletix.dev"], "status": "completed"},
        {"title": "Athletics — Endurance Run", "sport": "Athletics", "coach": "coach1@athletix.dev",
         "date_offset": -3, "athletes": ["athlete7@athletix.dev", "athlete8@athletix.dev"], "status": "completed"},
        {"title": "Football — Upcoming Tactics", "sport": "Football", "coach": "coach1@athletix.dev",
         "date_offset": 3, "athletes": ["athlete1@athletix.dev", "athlete2@athletix.dev"], "status": "scheduled"},
        # Coach 2 — Cricket / Badminton / Basketball
        {"title": "Cricket — Batting Practice", "sport": "Cricket", "coach": "coach2@athletix.dev",
         "date_offset": -12, "athletes": ["athlete3@athletix.dev", "athlete4@athletix.dev"], "status": "completed"},
        {"title": "Cricket — Bowling Session", "sport": "Cricket", "coach": "coach2@athletix.dev",
         "date_offset": -5, "athletes": ["athlete3@athletix.dev", "athlete4@athletix.dev"], "status": "completed"},
        {"title": "Badminton — Agility Drills", "sport": "Badminton", "coach": "coach2@athletix.dev",
         "date_offset": -8, "athletes": ["athlete5@athletix.dev"], "status": "completed"},
        {"title": "Basketball — Shooting Practice", "sport": "Basketball", "coach": "coach2@athletix.dev",
         "date_offset": -6, "athletes": ["athlete6@athletix.dev"], "status": "completed"},
        {"title": "Cricket — Upcoming Match Prep", "sport": "Cricket", "coach": "coach2@athletix.dev",
         "date_offset": 5, "athletes": ["athlete3@athletix.dev", "athlete4@athletix.dev"], "status": "scheduled"},
    ]

    session_ids = []
    for i, sd in enumerate(sessions_def):
        session_date = dt(sd["date_offset"])
        existing = await db.training_sessions.find_one({"title": sd["title"], "coach_id": coach_ids[sd["coach"]]})
        if existing:
            session_ids.append((existing["_id"], sd))
            continue
        s_id = oid()
        await db.training_sessions.insert_one({
            "_id": s_id,
            "title": sd["title"],
            "sport_id": sport_ids[sd["sport"]],
            "coach_id": coach_ids[sd["coach"]],
            "date": session_date,
            "start_time": "09:00",
            "end_time": "11:00",
            "venue": "Academy Ground A" if i % 2 == 0 else "Indoor Arena B",
            "objectives": f"Focus on fundamentals and technique development.",
            "athlete_ids": [athlete_ids[e] for e in sd["athletes"]],
            "status": sd["status"],
            "created_at": now,
            "updated_at": now,
        })
        session_ids.append((s_id, sd))
    print(f"  Training sessions created/verified: {len(session_ids)}")

    # ── 7. Attendance ──────────────────────────────────────────────────────────
    attendance_count = 0
    for s_id, sd in session_ids:
        if sd["status"] != "completed":
            continue
        for ath_email in sd["athletes"]:
            existing = await db.attendance.find_one({
                "session_id": s_id,
                "athlete_id": athlete_ids[ath_email],
            })
            if existing:
                continue
            # Vary attendance: athlete5 misses one, athlete3 is late once
            status = "present"
            if ath_email == "athlete5@athletix.dev" and "Agility" in sd["title"]:
                status = "absent"
            elif ath_email == "athlete3@athletix.dev" and "Batting" in sd["title"]:
                status = "late"
            await db.attendance.insert_one({
                "_id": oid(),
                "session_id": s_id,
                "athlete_id": athlete_ids[ath_email],
                "status": status,
                "recorded_by": coach_ids[sd["coach"]],
                "recorded_at": dt(sd["date_offset"]),
            })
            attendance_count += 1
    print(f"  Attendance records created: {attendance_count}")

    # ── 8. Performance assessments ─────────────────────────────────────────────
    def score(base, variance=10):
        import random
        return max(0, min(100, base + random.randint(-variance, variance)))

    assessments_def = [
        # Rahul Sharma — Football
        {"athlete": "athlete1@athletix.dev", "sport": "Football", "coach": "coach1@athletix.dev",
         "date_offset": -60, "bases": [72, 68, 70, 74, 71]},
        {"athlete": "athlete1@athletix.dev", "sport": "Football", "coach": "coach1@athletix.dev",
         "date_offset": -30, "bases": [78, 74, 75, 79, 77]},
        {"athlete": "athlete1@athletix.dev", "sport": "Football", "coach": "coach1@athletix.dev",
         "date_offset": -7, "bases": [82, 76, 80, 84, 83]},
        # Priya Nair — Football
        {"athlete": "athlete2@athletix.dev", "sport": "Football", "coach": "coach1@athletix.dev",
         "date_offset": -55, "bases": [65, 63, 67, 64, 66]},
        {"athlete": "athlete2@athletix.dev", "sport": "Football", "coach": "coach1@athletix.dev",
         "date_offset": -25, "bases": [70, 69, 72, 70, 71]},
        {"athlete": "athlete2@athletix.dev", "sport": "Football", "coach": "coach1@athletix.dev",
         "date_offset": -5, "bases": [75, 73, 76, 74, 77]},
        # David Okonkwo — Cricket
        {"athlete": "athlete3@athletix.dev", "sport": "Cricket", "coach": "coach2@athletix.dev",
         "date_offset": -50, "bases": [80, 75, 78, 77]},
        {"athlete": "athlete3@athletix.dev", "sport": "Cricket", "coach": "coach2@athletix.dev",
         "date_offset": -20, "bases": [84, 79, 82, 81]},
        {"athlete": "athlete3@athletix.dev", "sport": "Cricket", "coach": "coach2@athletix.dev",
         "date_offset": -4, "bases": [88, 83, 85, 86]},
        # Emma Walsh — Cricket
        {"athlete": "athlete4@athletix.dev", "sport": "Cricket", "coach": "coach2@athletix.dev",
         "date_offset": -45, "bases": [60, 65, 62, 63]},
        {"athlete": "athlete4@athletix.dev", "sport": "Cricket", "coach": "coach2@athletix.dev",
         "date_offset": -15, "bases": [66, 70, 68, 67]},
        {"athlete": "athlete4@athletix.dev", "sport": "Cricket", "coach": "coach2@athletix.dev",
         "date_offset": -3, "bases": [71, 74, 72, 73]},
        # Arjun Patel — Badminton
        {"athlete": "athlete5@athletix.dev", "sport": "Badminton", "coach": "coach2@athletix.dev",
         "date_offset": -40, "bases": [77, 72, 80, 75, 74]},
        {"athlete": "athlete5@athletix.dev", "sport": "Badminton", "coach": "coach2@athletix.dev",
         "date_offset": -10, "bases": [82, 78, 85, 80, 79]},
        # Sofia Reyes — Basketball
        {"athlete": "athlete6@athletix.dev", "sport": "Basketball", "coach": "coach2@athletix.dev",
         "date_offset": -35, "bases": [74, 71, 73, 75, 70]},
        {"athlete": "athlete6@athletix.dev", "sport": "Basketball", "coach": "coach2@athletix.dev",
         "date_offset": -8, "bases": [79, 76, 78, 80, 75]},
        # Michael Chen — Athletics
        {"athlete": "athlete7@athletix.dev", "sport": "Athletics", "coach": "coach1@athletix.dev",
         "date_offset": -50, "bases": [85, 78, 80, 82]},
        {"athlete": "athlete7@athletix.dev", "sport": "Athletics", "coach": "coach1@athletix.dev",
         "date_offset": -20, "bases": [88, 82, 84, 86]},
        {"athlete": "athlete7@athletix.dev", "sport": "Athletics", "coach": "coach1@athletix.dev",
         "date_offset": -6, "bases": [91, 86, 87, 89]},
        # Amira Hassan — Athletics
        {"athlete": "athlete8@athletix.dev", "sport": "Athletics", "coach": "coach1@athletix.dev",
         "date_offset": -48, "bases": [68, 65, 67, 70]},
        {"athlete": "athlete8@athletix.dev", "sport": "Athletics", "coach": "coach1@athletix.dev",
         "date_offset": -18, "bases": [73, 70, 72, 74]},
        {"athlete": "athlete8@athletix.dev", "sport": "Athletics", "coach": "coach1@athletix.dev",
         "date_offset": -5, "bases": [78, 75, 77, 79]},
    ]

    sport_metrics = {
        "Football":   ["speed", "passing", "shooting", "dribbling", "endurance"],
        "Cricket":    ["batting", "bowling", "fielding", "endurance"],
        "Badminton":  ["agility", "speed", "smash", "footwork", "endurance"],
        "Basketball": ["shooting", "dribbling", "passing", "speed", "vertical_jump"],
        "Athletics":  ["sprint", "endurance", "long_jump", "strength"],
    }

    import random
    random.seed(42)  # Reproducible scores

    assessment_count = 0
    for ad in assessments_def:
        metrics_keys = sport_metrics[ad["sport"]]
        metric_values = {k: score(b, 5) for k, b in zip(metrics_keys, ad["bases"])}
        overall = round(sum(metric_values.values()) / len(metric_values), 2)

        # Check for duplicate (same athlete + date)
        check_date = dt(ad["date_offset"])
        existing = await db.performance_assessments.find_one({
            "athlete_id": athlete_ids[ad["athlete"]],
            "date": check_date,
        })
        if existing:
            continue

        await db.performance_assessments.insert_one({
            "_id": oid(),
            "athlete_id": athlete_ids[ad["athlete"]],
            "coach_id": coach_ids[ad["coach"]],
            "sport_id": sport_ids[ad["sport"]],
            "date": check_date,
            "metrics": metric_values,
            "overall_score": overall,
            "remarks": "Good session. Continue working on weak areas.",
            "created_at": now,
        })
        assessment_count += 1
    print(f"  Performance assessments created: {assessment_count}")

    # ── 9. Tournaments ─────────────────────────────────────────────────────────
    tournaments_def = [
        {
            "name": "City Youth Football Cup 2026",
            "sport": "Football",
            "venue": "City Sports Complex",
            "start_offset": 10,
            "end_offset": 12,
            "status": "upcoming",
            "participants": [
                {"athlete": "athlete1@athletix.dev", "event": "Open", "position": None},
                {"athlete": "athlete2@athletix.dev", "event": "Open", "position": None},
            ],
        },
        {
            "name": "Regional Athletics Championship 2026",
            "sport": "Athletics",
            "venue": "Regional Stadium",
            "start_offset": -30,
            "end_offset": -29,
            "status": "completed",
            "participants": [
                {"athlete": "athlete7@athletix.dev", "event": "100m Sprint", "position": 1, "score": "10.82s"},
                {"athlete": "athlete8@athletix.dev", "event": "200m Sprint", "position": 3, "score": "24.15s"},
            ],
        },
    ]

    tournament_ids = {}
    for td in tournaments_def:
        existing = await db.tournaments.find_one({"name": td["name"]})
        if existing:
            tournament_ids[td["name"]] = existing["_id"]
            print(f"  Tournament already exists: {td['name']}")
            continue
        t_id = oid()
        await db.tournaments.insert_one({
            "_id": t_id,
            "name": td["name"],
            "sport_id": sport_ids[td["sport"]],
            "venue": td["venue"],
            "start_date": dt(td["start_offset"]),
            "end_date": dt(td["end_offset"]),
            "description": f"{td['name']} — organized by the Regional Sports Association.",
            "status": td["status"],
            "created_by": user_ids["admin@athletix.dev"],
            "created_at": now,
        })
        tournament_ids[td["name"]] = t_id

        for p in td["participants"]:
            await db.tournament_participants.insert_one({
                "_id": oid(),
                "tournament_id": t_id,
                "athlete_id": athlete_ids[p["athlete"]],
                "event": p["event"],
                "position": p.get("position"),
                "score": p.get("score"),
                "remarks": "Good performance." if p.get("position") else None,
                "registered_at": now,
            })
        print(f"  Created tournament: {td['name']}")

    # ── 10. Notifications ──────────────────────────────────────────────────────
    notifications = [
        {"user_email": "athlete1@athletix.dev",
         "title": "Upcoming Training Session",
         "message": "You have a Football training session scheduled in 3 days.",
         "type": "training"},
        {"user_email": "athlete1@athletix.dev",
         "title": "New Assessment Recorded",
         "message": "Your coach has recorded a new performance assessment.",
         "type": "assessment"},
        {"user_email": "athlete7@athletix.dev",
         "title": "Tournament Result",
         "message": "Congratulations! You placed 1st in the 100m Sprint at the Regional Athletics Championship.",
         "type": "tournament"},
        {"user_email": "athlete8@athletix.dev",
         "title": "Tournament Result",
         "message": "You placed 3rd in the 200m Sprint at the Regional Athletics Championship.",
         "type": "tournament"},
        {"user_email": "coach1@athletix.dev",
         "title": "Upcoming Session Reminder",
         "message": "You have a Football session scheduled in 3 days.",
         "type": "training"},
    ]

    notif_count = 0
    for n in notifications:
        existing = await db.notifications.find_one({
            "user_id": user_ids[n["user_email"]],
            "title": n["title"],
        })
        if existing:
            continue
        await db.notifications.insert_one({
            "_id": oid(),
            "user_id": user_ids[n["user_email"]],
            "title": n["title"],
            "message": n["message"],
            "type": n["type"],
            "is_read": False,
            "created_at": now,
        })
        notif_count += 1
    print(f"  Notifications created: {notif_count}")

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n=== Seed Complete ===")
    print("\nDevelopment credentials:")
    print("  admin@athletix.dev   /  Admin@123")
    print("  coach1@athletix.dev  /  Coach@123")
    print("  coach2@athletix.dev  /  Coach@123")
    print("  athlete1@athletix.dev  /  Athlete@123  (Football)")
    print("  athlete3@athletix.dev  /  Athlete@123  (Cricket)")
    print("  athlete7@athletix.dev  /  Athlete@123  (Athletics)")
    print()


async def main():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    try:
        await db.command("ping")
        print(f"Connected to MongoDB: {MONGO_URI}/{MONGO_DB_NAME}")
        await seed(db)
    except Exception as e:
        print(f"\nERROR: Could not connect to MongoDB.\n  {e}")
        print("\nMake sure MongoDB is running before seeding.")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
