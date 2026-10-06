# Software Requirements Specification — Athletix

**Version:** 1.0  
**Date:** 2026-10-05  
**Project:** Athletix — Integrated Sports Performance & Academy Management Platform

---

## 1. Introduction

### 1.1 Purpose

This document specifies the functional and non-functional requirements for Athletix. It serves as the reference for implementation, testing, and future development.

### 1.2 Scope

Athletix is a web-based platform for sports academies. It manages athletes, coaches, training sessions, attendance, performance assessments, tournaments, and analytics. The system supports three user roles: Admin, Coach, and Athlete.

### 1.3 Definitions

| Term | Definition |
|---|---|
| Athlete | A registered sports academy member tracked in the system |
| Coach | A staff member who runs training sessions and assesses athletes |
| Admin | A privileged user who manages all system configuration and users |
| Assessment | A recorded set of performance metric scores for one athlete |
| Session | A scheduled or completed training event |
| Metric | A measurable performance attribute specific to a sport |

---

## 2. Overall Description

### 2.1 Product Perspective

Athletix is a standalone web application. It does not integrate with external systems in its current version. Data is stored in MongoDB and served through a FastAPI REST API consumed by a React single-page application.

### 2.2 User Classes

**Admin**
- Manages all system data
- Views academy-wide statistics and reports
- Creates and configures sports, categories, users, tournaments

**Coach**
- Manages training sessions for assigned athletes
- Records attendance and performance assessments
- Views analytics and development history

**Athlete**
- Views their own profile, schedule, and performance data
- Cannot access any other athlete's data

### 2.3 Constraints

- Backend authorization is enforced independently of frontend visibility
- Passwords are never stored in plaintext
- JWT tokens expire after a configurable duration
- MongoDB is the only database; no additional data stores are used
- The system does not send emails or SMS notifications

---

## 3. Functional Requirements

### 3.1 Authentication

| ID | Requirement |
|---|---|
| FR-AUTH-01 | Users log in with email and password |
| FR-AUTH-02 | Passwords are hashed with bcrypt |
| FR-AUTH-03 | A JWT access token is returned on successful login |
| FR-AUTH-04 | All protected endpoints validate the token |
| FR-AUTH-05 | Expired or invalid tokens return HTTP 401 |
| FR-AUTH-06 | Users can change their own password |
| FR-AUTH-07 | The current user profile is retrievable via GET /auth/me |

### 3.2 User & Role Management

| ID | Requirement |
|---|---|
| FR-USER-01 | Admin can create users with a specified role |
| FR-USER-02 | Admin can activate or deactivate any user |
| FR-USER-03 | Admin can reset a user's password |
| FR-USER-04 | Role is stored in the JWT and verified per endpoint |

### 3.3 Sports Management

| ID | Requirement |
|---|---|
| FR-SPORT-01 | Admin can create a sport with name and description |
| FR-SPORT-02 | Admin can define performance metric categories per sport |
| FR-SPORT-03 | Admin can edit or deactivate a sport |
| FR-SPORT-04 | Five sports are seeded: Football, Cricket, Badminton, Basketball, Athletics |

### 3.4 Athlete Management

| ID | Requirement |
|---|---|
| FR-ATH-01 | Admin can create, edit, and deactivate athlete profiles |
| FR-ATH-02 | Athlete profile includes: name, email, phone, DOB, gender, sport, joining date, emergency contact, status |
| FR-ATH-03 | Admin can assign an athlete to a coach |
| FR-ATH-04 | Admin can search and filter athletes |
| FR-ATH-05 | Coach can view profiles of their assigned athletes |
| FR-ATH-06 | Athlete can view only their own profile |

### 3.5 Coach Management

| ID | Requirement |
|---|---|
| FR-COACH-01 | Admin can create, edit, and deactivate coaches |
| FR-COACH-02 | Admin can assign sports to a coach |
| FR-COACH-03 | Admin can assign/unassign athletes to a coach |

### 3.6 Training Sessions

| ID | Requirement |
|---|---|
| FR-TRAIN-01 | Coach can create a training session with: title, sport, date, time, venue, objectives, status |
| FR-TRAIN-02 | Coach can assign athletes to a session |
| FR-TRAIN-03 | Coach can update session status (Scheduled / Completed / Cancelled) |
| FR-TRAIN-04 | Athletes can view sessions they are assigned to |

### 3.7 Attendance

| ID | Requirement |
|---|---|
| FR-ATT-01 | Coach can record attendance per athlete per session (Present / Absent / Late) |
| FR-ATT-02 | System calculates attendance percentage per athlete |
| FR-ATT-03 | A warning is surfaced when attendance falls below 75% |
| FR-ATT-04 | Athlete can view their own attendance history |

### 3.8 Performance Assessments

| ID | Requirement |
|---|---|
| FR-PERF-01 | Coach can create an assessment for any assigned athlete |
| FR-PERF-02 | Assessment records metric scores (0–100) based on the athlete's sport |
| FR-PERF-03 | Overall score is calculated as the average of metric scores |
| FR-PERF-04 | Coach can add remarks to each assessment |
| FR-PERF-05 | Assessment history is stored and retrievable per athlete |
| FR-PERF-06 | Athlete can view their own assessment history |

### 3.9 Performance Analytics

| ID | Requirement |
|---|---|
| FR-ANA-01 | The system calculates improvement percentage between the last two assessments |
| FR-ANA-02 | The system identifies the strongest and weakest metric from the latest assessment |
| FR-ANA-03 | Analytics are calculated from real database data only |
| FR-ANA-04 | If fewer than two assessments exist, the system clearly states insufficient history |
| FR-ANA-05 | Charts display metric scores and performance trends over time |

### 3.10 Tournaments

| ID | Requirement |
|---|---|
| FR-TOUR-01 | Admin can create, update, and delete tournaments with name, sport, venue, dates, registration deadline, description, status |
| FR-TOUR-02 | Admin can register any active athlete; Coach can register only assigned athletes; Athlete can self-register for eligible sports |
| FR-TOUR-03 | Results are recorded with position, score, points, medal (Gold/Silver/Bronze), and remarks |
| FR-TOUR-04 | Admin and Coach (assigned) can record/update results; Athletes are forbidden from modifying results |
| FR-TOUR-05 | Athletes can view personal tournament competition history, medals, and points |

### 3.11 Rankings

| ID | Requirement |
|---|---|
| FR-RANK-01 | Tournament Ranking aggregates points, gold/silver/bronze medals, and tournaments played |
| FR-RANK-02 | Performance Ranking ranks athletes by latest assessment overall score |
| FR-RANK-03 | Attendance Ranking ranks athletes by training attendance % (excluding cancelled sessions) |
| FR-RANK-04 | Improvement Ranking ranks athletes by assessment improvement % (requires >= 2 assessments) |
| FR-RANK-05 | All rankings support filtering by sport and academy-wide aggregation |
| FR-RANK-06 | Deterministic tie handling is enforced across all ranking categories |

### 3.12 Notifications

| ID | Requirement |
|---|---|
| FR-NOTIF-01 | In-app notifications are created for key events |
| FR-NOTIF-02 | Notifications show unread count |
| FR-NOTIF-03 | Users can mark notifications as read |
| FR-NOTIF-04 | No email, SMS, or push notifications are implemented |

### 3.13 Reports

| ID | Requirement |
|---|---|
| FR-REP-01 | Admin can view academy-wide performance summaries |
| FR-REP-02 | Reports cover attendance, assessment scores, and active athletes |

---

## 4. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | All API responses return JSON |
| NFR-02 | API endpoints follow REST conventions |
| NFR-03 | Backend enforces authorization on every protected endpoint |
| NFR-04 | Passwords are never logged or returned in API responses |
| NFR-05 | The application is containerized and runnable with `docker compose up` |
| NFR-06 | The frontend is responsive on desktop and mobile |
| NFR-07 | MongoDB data persists across container restarts via a named volume |
| NFR-08 | The health endpoint returns the database connectivity status |

---

## 5. Out of Scope (Current Version)

- Email or SMS notifications
- File upload / profile photo storage
- Mobile native app
- External authentication (OAuth, SSO)
- Machine learning predictions
- Payment processing
