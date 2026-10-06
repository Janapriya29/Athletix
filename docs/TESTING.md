# Testing — Athletix

---

## Strategy

Tests are written for correctness, not quantity. Each test validates a meaningful behaviour of the application. The backend test suite uses `pytest` with `pytest-asyncio` and `httpx.AsyncClient` wired directly to the FastAPI app — no live server or real MongoDB is required for most tests.

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

To run a specific file:
```bash
pytest tests/test_health.py -v
```

To see coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

---

## Test Configuration

| File | Purpose |
|---|---|
| `backend/pytest.ini` | asyncio_mode = auto, test discovery settings |
| `backend/tests/conftest.py` | Shared `client` fixture (AsyncClient + ASGITransport) |

---

## Test Files

### `tests/test_health.py` — Health endpoint

| Test | What it verifies |
|---|---|
| `test_root_endpoint` | GET / returns 200 and welcome message |
| `test_health_endpoint_reachable` | GET /api/v1/health returns 200, status=ok, app=Athletix |

---

### `tests/test_auth.py` — Authentication (Phase 1)

| Test | What it verifies |
|---|---|
| `test_login_valid` | Correct credentials return access_token |
| `test_login_wrong_password` | Wrong password returns 401 |
| `test_login_unknown_email` | Unknown email returns 401 |
| `test_get_me_authenticated` | Valid token returns user profile |
| `test_get_me_no_token` | Missing token returns 401 |
| `test_get_me_invalid_token` | Malformed token returns 401 |
| `test_change_password` | Correct current password updates successfully |
| `test_change_password_wrong_current` | Wrong current password returns 400 |

---

### `tests/test_sports.py` — Sports Management (Phase 2)

| Test | What it verifies |
|---|---|
| `test_admin_can_create_sport` | Admin token creates sport with categories |
| `test_duplicate_sport_rejected` | Case-insensitive duplicate name returns 409 |
| `test_coach_cannot_create_sport` | Coach POST returns 403 Forbidden |
| `test_athlete_cannot_create_sport` | Athlete POST returns 403 Forbidden |
| `test_unauthenticated_sports_rejected` | Missing token returns 401 Unauthorized |
| `test_admin_can_update_sport` | Admin PUT updates description/metadata |
| `test_admin_can_deactivate_sport` | Status toggle works; inactive hidden from athlete |
| `test_list_sports_search` | Name regex search returns matched records |

---

### `tests/test_users.py` — User Management (Phase 2)

| Test | What it verifies |
|---|---|
| `test_admin_can_list_users` | Admin lists users; passwords omitted |
| `test_coach_cannot_access_user_management` | Coach GET returns 403 Forbidden |
| `test_athlete_cannot_access_user_management` | Athlete GET returns 403 Forbidden |
| `test_admin_can_create_user_with_hashed_password` | User created with bcrypt hash, never plaintext |
| `test_admin_can_deactivate_user` | User status toggled |
| `test_search_and_filter_users` | Filter by role and search by name/email |

---

### `tests/test_coaches.py` — Coach Management (Phase 2)

| Test | What it verifies |
|---|---|
| `test_admin_can_create_and_view_coach` | Admin creates coach and resolves assigned sports |
| `test_coach_can_view_own_profile` | Coach fetches own profile via /coaches/me |
| `test_coach_cannot_create_coach` | Coach POST returns 403 Forbidden |
| `test_athlete_cannot_manage_coaches` | Athlete POST returns 403 Forbidden |
| `test_assign_and_remove_athletes` | Assigning and removing athlete assignments updates DB and counts |

---

### `tests/test_athletes.py` — Athlete Management (Phase 2)

| Test | What it verifies |
|---|---|
| `test_admin_can_create_and_view_athlete` | Admin creates athlete linked to sport and account |
| `test_invalid_sport_rejected` | Non-existent sport returns 400 Bad Request |
| `test_invalid_coach_rejected` | Non-existent coach returns 400 Bad Request |
| `test_athlete_can_view_own_profile` | Athlete fetches own profile via /athletes/me |
| `test_athlete_cannot_view_another_athlete` | Athlete accessing another athlete ID returns 403 |
| `test_coach_can_view_assigned_athlete_only` | Coach accessing unassigned athlete returns 403 |
| `test_athlete_self_update_allowed_fields` | Athlete updates allowed fields; protected fields unchanged |

---

---

### `tests/test_training.py` — Training Sessions & Attendance (Phase 3)

| Test | What it verifies |
|---|---|
| `test_admin_can_create_session` | Admin creates training session with sport and coach validation |
| `test_coach_can_create_permitted_session` | Coach creates session for assigned sport |
| `test_athlete_cannot_create_session` | Athlete cannot create training session (403 Forbidden) |
| `test_invalid_and_inactive_sport_rejected` | Non-existent or inactive sport rejected |
| `test_invalid_and_inactive_coach_rejected` | Non-existent or inactive coach rejected |
| `test_invalid_time_range_rejected` | End time before or equal to start time rejected |
| `test_coach_cannot_access_another_coach_session` | Coach cannot update session belonging to another coach |
| `test_admin_can_view_all_sessions` | Admin lists sessions academy-wide |
| `test_add_and_remove_participants` | Manage athlete roster for a session |
| `test_record_and_update_attendance` | Upsert attendance status (present/late/absent) with remarks |
| `test_attendance_calculation_rules` | Formula `(Present + Late) / Total Applicable * 100`, warning when < 75%, cancelled sessions excluded |
| `test_unauthenticated_requests_rejected` | 401 Unauthorized returned when no Bearer token provided |

---

### `tests/test_assessments.py` — Performance assessments (Phase 4)

| Test | What it verifies |
|---|---|
| `test_create_assessment` | Coach creates assessment, overall_score is computed |
| `test_overall_score_calculation` | Score = mean(metric values) |
| `test_retrieve_athlete_assessments` | Returns ordered list for correct athlete |
| `test_athlete_cannot_create_assessment` | Athlete POST returns 403 |

---

### `tests/test_analytics.py` — Performance Analytics (Phase 5)

| Test | What it verifies |
|---|---|
| `test_1_athlete_can_access_own_analytics` | Athlete GET /api/v1/analytics/athlete/me returns 200 and own profile data |
| `test_2_athlete_cannot_access_another_athlete_analytics` | Athlete accessing another athlete's analytics returns 403 Forbidden |
| `test_3_athlete_cannot_access_coach_analytics` | Athlete accessing coach analytics returns 403 Forbidden |
| `test_4_athlete_cannot_access_admin_analytics` | Athlete accessing admin analytics returns 403 Forbidden |
| `test_5_coach_can_access_assigned_athlete_analytics` | Coach can view detailed analytics for assigned athlete |
| `test_6_coach_cannot_access_unassigned_athlete_analytics` | Coach accessing unassigned athlete returns 403 Forbidden |
| `test_7_coach_summary_only_includes_assigned_athletes` | Coach summary only includes athletes assigned to that coach |
| `test_8_admin_can_access_academy_analytics` | Admin GET /api/v1/analytics/admin/summary returns academy-wide totals |
| `test_9_admin_can_access_all_athlete_analytics` | Admin can access analytics for any athlete in the academy |
| `test_10_current_performance_calculated_correctly` | Current performance score and date derived from latest assessment |
| `test_11_previous_performance_calculated_correctly` | Previous performance score and date derived from 2nd latest assessment |
| `test_12_improvement_percentage_calculated_correctly` | Verified formula `((current - previous) / previous) * 100` |
| `test_13_zero_previous_score_handled_safely` | Safe handling when previous score is zero (no DivisionByZero) |
| `test_14_insufficient_history_handled_correctly` | When < 2 assessments, returns None and 'Insufficient Data' |
| `test_15_trend_calculation_works` | Validates 'Improving', 'Declining', 'Stable', 'Insufficient Data' |
| `test_16_strongest_metric_is_correct` | Correctly identifies metric with highest score |
| `test_17_weakest_metric_is_correct` | Correctly identifies metric with lowest score |
| `test_18_attendance_percentage_phase3_logic` | Verifies Phase 3 formula `(Present + Late) / Total Applicable * 100` |
| `test_19_cancelled_sessions_are_excluded` | Cancelled training sessions excluded from applicable session count |
| `test_20_attendance_warning_below_75_percent` | Attendance warning flag is True when percentage < 75.0% |
| `test_21_no_attendance_data_handled_correctly` | When 0 applicable sessions exist, percentage is None (not fake 0%) |
| `test_22_no_assessment_data_handled_correctly` | When 0 assessments exist, score is None, trend is 'Insufficient Data' |
| `test_23_multiple_assessment_history_sorted_correctly` | Assessment history is sorted chronologically descending |
| `test_24_sport_filtering_works` | Admin sports breakdown and coach sport filter return accurate groupings |
| `test_25_unauthenticated_analytics_request_returns_401` | Unauthenticated requests return 401 Unauthorized |

---

### `tests/test_tournaments.py` — Tournaments & Participation (Phase 6)

| Test | What it verifies |
|---|---|
| `test_01_admin_can_create_tournament` | Admin can create tournaments with complete metadata |
| `test_02_coach_cannot_create_tournament` | Coach cannot create tournaments (403 Forbidden) |
| `test_03_athlete_cannot_create_tournament` | Athlete cannot create tournaments (403 Forbidden) |
| `test_04_invalid_sport_rejected` | Non-existent sport ID rejected with 400 Bad Request |
| `test_05_inactive_sport_rejected` | Inactive sport ID rejected with 400 Bad Request |
| `test_06_invalid_date_range_rejected` | End date before start date rejected (400/422) |
| `test_07_invalid_registration_deadline_rejected` | Registration deadline after start date rejected (400/422) |
| `test_08_admin_can_view_tournaments` | Admin can list all tournaments |
| `test_09_coach_can_view_tournaments` | Coach can view tournaments |
| `test_10_athlete_can_view_tournaments` | Athlete can view tournaments |
| `test_11_duplicate_participation_rejected` | Registering an already registered athlete returns 400 Bad Request |
| `test_12_admin_can_add_participant` | Admin can register any active athlete |
| `test_13_coach_can_add_assigned_athlete` | Coach can register an athlete assigned to them |
| `test_14_coach_cannot_add_unassigned_athlete` | Coach attempting to register an unassigned athlete returns 403 Forbidden |
| `test_15_athlete_cannot_add_another_athlete` | Athlete attempting to register another athlete returns 403 Forbidden |
| `test_16_admin_can_record_result` | Admin can record positions, scores, medals, and points |
| `test_17_coach_result_permissions_enforced` | Coach can record results for assigned athletes; 403 on unassigned |
| `test_18_athlete_cannot_modify_result` | Athletes are forbidden from recording or editing results (403 Forbidden) |
| `test_19_duplicate_result_handled` | Recording a result again updates cleanly without duplicate errors |
| `test_20_tournament_details_return_correct_participants_results` | Details endpoints return correct participant and result data |

---

### `tests/test_rankings.py` — Rankings Module (Phase 6)

| Test | What it verifies |
|---|---|
| `test_21_tournament_ranking_calculates_correctly` | Tournament leaderboard aggregates points, medals, and participation counts |
| `test_22_points_ranking_order_is_correct` | Leaderboard strictly orders athletes by points descending |
| `test_23_medal_counts_are_correct` | Accurate breakdown of gold, silver, bronze, and total medal tallies |
| `test_24_performance_ranking_uses_real_scores` | Performance leaderboard uses verified Phase 5 latest assessment scores |
| `test_25_attendance_ranking_uses_phase3_formula` | Attendance leaderboard uses Phase 3 `(Present + Late) / Total * 100` formula |
| `test_26_cancelled_sessions_excluded_from_attendance_ranking` | Cancelled training sessions are excluded from applicable session counts |
| `test_27_improvement_ranking_uses_phase5_improvement` | Improvement leaderboard calculates growth rate between consecutive assessments |
| `test_28_insufficient_performance_history_handled` | Athletes with < 2 assessments are omitted from improvement rankings |
| `test_29_sport_filtering_works` | Leaderboards support filtering by sport ID |
| `test_30_tie_ordering_is_deterministic` | Deterministic tie-breaking rules enforced (alphabetical fallback) |
| `test_31_unauthenticated_ranking_request_rejected` | Unauthenticated requests to ranking endpoints return 401 Unauthorized |
| `test_32_role_restrictions_work` | Validates role access across Admin, Coach, and Athlete roles |

---

### `tests/test_notifications.py` — In-App Notifications (Phase 7)

| Test | What it verifies |
|---|---|
| `test_training_session_creation_notifies_participants` | Scheduled session triggers in-app notification for athlete roster |
| `test_training_session_cancellation_notifies_participants` | Cancelled session triggers in-app notification for participants |
| `test_attendance_recorded_notifies_athlete` | Recording attendance notifies athlete with status and session date |
| `test_assessment_created_notifies_athlete` | Performance assessment creates notification with score |
| `test_tournament_registration_notifies_athlete` | Tournament registration notifies athlete |
| `test_tournament_result_notifies_athlete` | Result recorded notifies athlete with position and medal |
| `test_athlete_can_fetch_own_notifications` | Athlete fetches personal notification stream |
| `test_athlete_cannot_see_other_user_notifications` | Notifications are strictly isolated per user |
| `test_coach_can_fetch_own_notifications` | Coach fetches personal notification stream |
| `test_admin_can_fetch_own_notifications` | Admin fetches personal notification stream |
| `test_unread_count_accurate` | GET /notifications/unread-count returns accurate count |
| `test_mark_notification_as_read` | Marking single notification as read sets is_read=True and read_at |
| `test_mark_notification_as_read_forbidden_for_other_user` | Modifying another user's notification returns 403 Forbidden |
| `test_mark_all_as_read` | Marking all notifications as read resets unread count to 0 |
| `test_delete_notification_and_ownership_check` | Deleting notification removes it; deleting another user's returns 403 |
| `test_filter_notifications_by_type_and_unread` | Query filters by `unread=true` and `type` |
| `test_duplicate_notification_prevention` | Idempotent entity notifications prevent spam duplicates |
| `test_unauthenticated_notification_request_fails` | Unauthenticated requests return 401 Unauthorized |

---

### `tests/test_reports.py` — Reports & Data Export (Phase 7)

| Test | What it verifies |
|---|---|
| `test_athlete_can_access_own_performance_report` | Athlete accesses own performance report with score, trend, metrics |
| `test_athlete_cannot_access_other_performance_report` | Accessing another athlete's report returns 403 Forbidden |
| `test_coach_can_access_assigned_athlete_performance_report` | Coach accesses assigned athlete's performance report |
| `test_coach_cannot_access_unassigned_athlete_performance_report` | Coach accessing unassigned athlete returns 403 Forbidden |
| `test_admin_can_access_any_athlete_performance_report` | Admin accesses any athlete's performance report |
| `test_athlete_can_access_own_attendance_report` | Athlete accesses attendance report with breakdown and warning |
| `test_attendance_report_excludes_cancelled_sessions` | Attendance calculations exclude cancelled sessions |
| `test_athlete_can_access_own_tournaments_report` | Athlete accesses tournaments report with medal tally and points |
| `test_athlete_can_access_own_development_summary` | Athlete accesses integrated development profile summary |
| `test_admin_can_access_academy_summary` | Admin accesses academy-wide executive summary |
| `test_coach_and_athlete_cannot_access_academy_summary` | Coach and athlete access to academy summary returns 403 Forbidden |
| `test_academy_attendance_report_json` | Attendance report returns athlete roster with percentage rates |
| `test_academy_attendance_report_csv_export` | Attendance report exports formatted CSV with header row |
| `test_academy_tournaments_report_json` | Tournaments report returns list with medalists |
| `test_academy_tournaments_report_csv_export` | Tournaments report exports formatted CSV with header row |
| `test_unauthenticated_reports_request_fails` | Unauthenticated requests return 401 Unauthorized |

---

### `tests/test_phase8_workflow.py` — Quality, Security & Cross-Module Lifecycle (Phase 8)

| Test | What it verifies |
|---|---|
| `test_end_to_end_cross_module_lifecycle` | Complete cross-module lifecycle: Coach schedules training -> Athlete views -> Attendance recorded -> Attendance stats updated -> Assessment created -> Notification generated -> Analytics updated -> Tournament created -> Athlete registered -> Results awarded (Gold medal + points) -> Rankings updated -> Notifications generated -> Reports reflect complete multi-module state (development summary, academy summary, CSV exports) |
| `test_cross_role_report_and_notification_isolation` | Cross-role security boundaries: Athlete cannot view other athlete's reports (403), Coach cannot view unassigned athlete reports (403), Coach/Athlete cannot access academy summary (403), Athlete cannot modify/delete another user's notifications (403/404) |
| `test_input_validation_boundaries` | Boundary input validation: Tournament end_date before start_date rejected (400/422), registration deadline after start_date rejected (400/422), Training session end_time before start_time rejected (400/422) |
| `test_rbac_admin_endpoint_protection` | Role protection on admin endpoints: Coach and Athlete forbidden from creating sports (403) and forbidden from accessing academy admin analytics (403) |

---

## Notes

- Tests that require a database use a MongoDB test instance (configured via `MONGO_URI` in the test environment, pointing to a separate `athletix_test` database)
- Analytics tests (`test_analytics.py`) test pure calculation functions in `app/analytics/performance.py` directly
- Total Backend Tests: 152 passed (100% pass rate)
- Phase 0 health tests run without any MongoDB connection (the health endpoint reports "unavailable" but still returns 200)

---

## Frontend Testing

The frontend is validated by:

1. **Production build** — `npm run build` must succeed with no errors
2. **Manual login flow** — verify login redirects to the correct dashboard per role
3. **Route protection** — verify unauthenticated navigation redirects to /login
4. **404 route** — verify unknown paths render the NotFoundPage

A component test framework (e.g., Vitest + Testing Library) can be added in a later phase if required.
