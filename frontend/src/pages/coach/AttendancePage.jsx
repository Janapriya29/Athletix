import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import {
  getAthleteAttendanceSummary,
  getTrainingSessions,
  recordAttendance,
  recordBulkAttendance,
} from '../../services/trainingService'
import { getAthletes } from '../../services/athletesService'

export default function AttendancePage() {
  const [activeView, setActiveView] = useState('sessions') // 'sessions' | 'athlete'
  const [sessions, setSessions] = useState([])
  const [selectedSessionId, setSelectedSessionId] = useState('')
  const [selectedSession, setSelectedSession] = useState(null)
  const [athletes, setAthletes] = useState([])
  const [selectedAthleteId, setSelectedAthleteId] = useState('')
  const [athleteSummary, setAthleteSummary] = useState(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [feedback, setFeedback] = useState(null)
  const [saving, setSaving] = useState(false)

  // In-session attendance form state: { [athleteId]: { status: 'present', remarks: '' } }
  const [attendanceMap, setAttendanceMap] = useState({})

  // Fetch initial sessions & athletes
  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [sessList, athList] = await Promise.all([
        getTrainingSessions(),
        getAthletes().catch(() => []),
      ])

      setSessions(sessList || [])
      setAthletes(athList || [])

      if (sessList && sessList.length > 0) {
        const first = sessList[0]
        setSelectedSessionId(first.id)
        setSelectedSession(first)
        initializeSessionMap(first)
      }
      if (athList && athList.length > 0) {
        setSelectedAthleteId(athList[0].id)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load attendance data.')
    } finally {
      setLoading(false)
    }
  }

  const initializeSessionMap = (sess) => {
    const map = {}
    sess.participants?.forEach((p) => {
      map[p.athlete_id] = {
        status: p.attendance_status || 'present',
        remarks: p.remarks || '',
      }
    })
    setAttendanceMap(map)
  }

  useEffect(() => {
    fetchData()
  }, [])

  // Handle switching session selection
  const handleSelectSession = (id) => {
    setSelectedSessionId(id)
    const found = sessions.find((s) => s.id === id)
    if (found) {
      setSelectedSession(found)
      initializeSessionMap(found)
    }
  }

  // Handle athlete attendance lookup
  const loadAthleteAttendance = async (athId) => {
    if (!athId) return
    try {
      setLoading(true)
      setError(null)
      const summary = await getAthleteAttendanceSummary(athId)
      setAthleteSummary(summary)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load athlete attendance summary.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (activeView === 'athlete' && selectedAthleteId) {
      loadAthleteAttendance(selectedAthleteId)
    }
  }, [activeView, selectedAthleteId])

  const handleStatusChange = (athleteId, newStatus) => {
    setAttendanceMap((prev) => ({
      ...prev,
      [athleteId]: {
        ...prev[athleteId],
        status: newStatus,
      },
    }))
  }

  const handleRemarksChange = (athleteId, newRemarks) => {
    setAttendanceMap((prev) => ({
      ...prev,
      [athleteId]: {
        ...prev[athleteId],
        remarks: newRemarks,
      },
    }))
  }

  const handleMarkAll = (targetStatus) => {
    if (!selectedSession?.participants) return
    const updated = { ...attendanceMap }
    selectedSession.participants.forEach((p) => {
      updated[p.athlete_id] = {
        ...(updated[p.athlete_id] || {}),
        status: targetStatus,
      }
    })
    setAttendanceMap(updated)
  }

  const handleSaveSingle = async (athleteId) => {
    if (!selectedSession) return
    try {
      setSaving(true)
      const rec = attendanceMap[athleteId] || { status: 'present', remarks: '' }
      await recordAttendance(selectedSession.id, athleteId, rec.status, rec.remarks || null)
      setFeedback('Attendance updated successfully.')
      refreshSelectedSession()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save attendance.')
    } finally {
      setSaving(false)
    }
  }

  const handleSaveBulk = async () => {
    if (!selectedSession || !selectedSession.participants) return
    try {
      setSaving(true)
      const records = selectedSession.participants.map((p) => ({
        athlete_id: p.athlete_id,
        status: attendanceMap[p.athlete_id]?.status || 'present',
        remarks: attendanceMap[p.athlete_id]?.remarks || null,
      }))
      await recordBulkAttendance(selectedSession.id, records)
      setFeedback('All attendance records saved successfully.')
      refreshSelectedSession()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save bulk attendance.')
    } finally {
      setSaving(false)
    }
  }

  const refreshSelectedSession = async () => {
    if (!selectedSession) return
    try {
      const refreshedList = await getTrainingSessions()
      setSessions(refreshedList)
      const found = refreshedList.find((s) => s.id === selectedSession.id)
      if (found) {
        setSelectedSession(found)
        initializeSessionMap(found)
      }
    } catch {
      // non-critical
    }
  }

  // Count attendance stats for current view
  const presentCount = Object.values(attendanceMap).filter((v) => v.status === 'present').length
  const lateCount = Object.values(attendanceMap).filter((v) => v.status === 'late').length
  const absentCount = Object.values(attendanceMap).filter((v) => v.status === 'absent').length

  const getAttBadge = (st) => {
    const s = st?.toLowerCase()
    if (s === 'present') return styles.badgePresent
    if (s === 'late') return styles.badgeLate
    if (s === 'absent') return styles.badgeAbsent
    return styles.badgeInactive
  }

  return (
    <AppLayout title="Attendance Management">
      <div className={styles.container}>
        {feedback && (
          <div className={styles.alertSuccess} role="alert">
            {feedback}
            <button
              style={{ float: 'right', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
              onClick={() => setFeedback(null)}
            >
              ×
            </button>
          </div>
        )}
        {error && <ErrorMessage message={error} />}

        {/* View Toggle Tabs */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 'var(--space-4)' }}>
          <button
            className={activeView === 'sessions' ? styles.primaryBtn : styles.secondaryBtn}
            onClick={() => setActiveView('sessions')}
          >
            📋 Session Attendance Recording
          </button>
          <button
            className={activeView === 'athlete' ? styles.primaryBtn : styles.secondaryBtn}
            onClick={() => setActiveView('athlete')}
          >
            👤 Athlete Attendance Records
          </button>
        </div>

        {activeView === 'sessions' ? (
          <div>
            {/* Session Selector Bar */}
            <div className={styles.headerBar}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1 }}>
                <label style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--color-text-muted)' }}>
                  Select Session:
                </label>
                <select
                  className={styles.selectInput}
                  style={{ flex: 1, maxWidth: 500 }}
                  value={selectedSessionId}
                  onChange={(e) => handleSelectSession(e.target.value)}
                >
                  {sessions.length === 0 ? (
                    <option value="">No sessions available</option>
                  ) : (
                    sessions.map((s) => (
                      <option key={s.id} value={s.id}>
                        {new Date(s.session_date).toLocaleDateString()} — {s.title} ({s.sport_name}) [{s.status}]
                      </option>
                    ))
                  )}
                </select>
              </div>

              {selectedSession && selectedSession.participants?.length > 0 && (
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    type="button"
                    className={styles.secondaryBtn}
                    onClick={() => handleMarkAll('present')}
                  >
                    Mark All Present
                  </button>
                  <button
                    type="button"
                    className={styles.primaryBtn}
                    disabled={saving}
                    onClick={handleSaveBulk}
                  >
                    {saving ? 'Saving...' : 'Save All Attendance'}
                  </button>
                </div>
              )}
            </div>

            {loading ? (
              <LoadingSpinner />
            ) : !selectedSession ? (
              <div className={styles.emptyState}>No training sessions found.</div>
            ) : (
              <div>
                {/* Session Header Card & Stats */}
                <div className={styles.statsGrid} style={{ marginBottom: 'var(--space-5)' }}>
                  <div className={styles.statCard}>
                    <span className={styles.statValue} style={{ color: 'var(--color-accent)' }}>
                      {selectedSession.participants?.length || 0}
                    </span>
                    <span className={styles.statLabel}>Total Athletes</span>
                  </div>
                  <div className={styles.statCard}>
                    <span className={styles.statValue} style={{ color: '#22c55e' }}>
                      {presentCount}
                    </span>
                    <span className={styles.statLabel}>Present</span>
                  </div>
                  <div className={styles.statCard}>
                    <span className={styles.statValue} style={{ color: '#f59e0b' }}>
                      {lateCount}
                    </span>
                    <span className={styles.statLabel}>Late</span>
                  </div>
                  <div className={styles.statCard}>
                    <span className={styles.statValue} style={{ color: '#ef4444' }}>
                      {absentCount}
                    </span>
                    <span className={styles.statLabel}>Absent</span>
                  </div>
                </div>

                {/* Session Detail Summary */}
                <div
                  style={{
                    backgroundColor: 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius)',
                    padding: '16px 20px',
                    marginBottom: 'var(--space-4)',
                    display: 'flex',
                    flexWrap: 'wrap',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: 12,
                  }}
                >
                  <div>
                    <h3 style={{ margin: 0, fontSize: 'var(--text-lg)', color: 'var(--color-text)' }}>
                      {selectedSession.title}
                    </h3>
                    <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginTop: 4 }}>
                      Sport: <strong>{selectedSession.sport_name}</strong> • Date:{' '}
                      <strong>{new Date(selectedSession.session_date).toLocaleDateString()}</strong> • Time:{' '}
                      <strong>{selectedSession.start_time} - {selectedSession.end_time}</strong> • Venue:{' '}
                      <strong>{selectedSession.location}</strong>
                    </div>
                  </div>
                  <div>
                    <span
                      className={`${styles.badge} ${
                        selectedSession.status === 'completed'
                          ? styles.badgeCompleted
                          : selectedSession.status === 'cancelled'
                          ? styles.badgeCancelled
                          : styles.badgeScheduled
                      }`}
                    >
                      {selectedSession.status}
                    </span>
                  </div>
                </div>

                {/* Participants Attendance Table */}
                <div className={styles.tableWrapper}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>Athlete</th>
                        <th>Sport / Contact</th>
                        <th>Attendance Status</th>
                        <th>Remarks / Notes</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedSession.participants?.length === 0 ? (
                        <tr>
                          <td colSpan="5" className={styles.emptyState}>
                            No athletes enrolled in this session. Add athletes under the "Training" tab.
                          </td>
                        </tr>
                      ) : (
                        selectedSession.participants?.map((p) => {
                          const current = attendanceMap[p.athlete_id] || { status: 'present', remarks: '' }
                          return (
                            <tr key={p.athlete_id}>
                              <td>
                                <strong>{p.full_name}</strong>
                              </td>
                              <td style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                                {p.sport_name || 'Athlete'}
                                <div>{p.email}</div>
                              </td>
                              <td>
                                <div style={{ display: 'flex', gap: 6 }}>
                                  {['present', 'late', 'absent'].map((st) => (
                                    <button
                                      key={st}
                                      type="button"
                                      onClick={() => handleStatusChange(p.athlete_id, st)}
                                      style={{
                                        textTransform: 'capitalize',
                                        fontSize: '0.75rem',
                                        fontWeight: 600,
                                        padding: '4px 10px',
                                        borderRadius: 4,
                                        cursor: 'pointer',
                                        border: '1px solid var(--color-border)',
                                        backgroundColor:
                                          current.status === st
                                            ? st === 'present'
                                              ? '#22c55e'
                                              : st === 'late'
                                              ? '#f59e0b'
                                              : '#ef4444'
                                            : 'var(--color-surface)',
                                        color:
                                          current.status === st
                                            ? '#0f1117'
                                            : 'var(--color-text)',
                                      }}
                                    >
                                      {st}
                                    </button>
                                  ))}
                                </div>
                              </td>
                              <td>
                                <input
                                  type="text"
                                  className={styles.formInput}
                                  style={{ padding: '6px 10px', fontSize: '0.8rem', minWidth: 200 }}
                                  placeholder="e.g. Excused, injury, arrived 10m late"
                                  value={current.remarks}
                                  onChange={(e) => handleRemarksChange(p.athlete_id, e.target.value)}
                                />
                              </td>
                              <td>
                                <button
                                  type="button"
                                  className={styles.secondaryBtn}
                                  style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                                  disabled={saving}
                                  onClick={() => handleSaveSingle(p.athlete_id)}
                                >
                                  Save
                                </button>
                              </td>
                            </tr>
                          )
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Athlete Attendance Lookup View */
          <div>
            <div className={styles.headerBar}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1 }}>
                <label style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--color-text-muted)' }}>
                  Select Athlete:
                </label>
                <select
                  className={styles.selectInput}
                  style={{ flex: 1, maxWidth: 400 }}
                  value={selectedAthleteId}
                  onChange={(e) => setSelectedAthleteId(e.target.value)}
                >
                  {athletes.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.full_name} ({a.sport_name || 'No sport'})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {loading ? (
              <LoadingSpinner />
            ) : !athleteSummary ? (
              <div className={styles.emptyState}>No attendance records found for this athlete.</div>
            ) : (
              <div>
                {/* Warning Alert if < 75% */}
                {athleteSummary.warning && (
                  <div className={styles.warningBanner} style={{ marginBottom: 'var(--space-4)' }}>
                    <span>⚠️</span>
                    <div>
                      <strong>Attendance Alert:</strong> This athlete's attendance rate is currently{' '}
                      <strong>{athleteSummary.attendance_percentage}%</strong>, which is below the 75% academy requirement.
                    </div>
                  </div>
                )}

                {/* Athlete Attendance Stats */}
                <div className={styles.statsGrid} style={{ marginBottom: 'var(--space-5)' }}>
                  <div className={styles.statCard}>
                    <span className={styles.statValue} style={{ color: athleteSummary.warning ? '#ef4444' : '#22c55e' }}>
                      {athleteSummary.attendance_percentage}%
                    </span>
                    <span className={styles.statLabel}>Attendance Rate</span>
                    <div className={styles.progressBar}>
                      <div
                        className={styles.progressFill}
                        style={{
                          width: `${Math.min(athleteSummary.attendance_percentage, 100)}%`,
                          backgroundColor: athleteSummary.warning ? '#ef4444' : '#22c55e',
                        }}
                      />
                    </div>
                  </div>
                  <div className={styles.statCard}>
                    <span className={styles.statValue}>{athleteSummary.total_sessions}</span>
                    <span className={styles.statLabel}>Applicable Sessions</span>
                  </div>
                  <div className={styles.statCard}>
                    <span className={styles.statValue} style={{ color: '#22c55e' }}>
                      {athleteSummary.attended_sessions}
                    </span>
                    <span className={styles.statLabel}>Attended (Pres + Late)</span>
                  </div>
                  <div className={styles.statCard}>
                    <span className={styles.statValue} style={{ color: '#f59e0b' }}>
                      {athleteSummary.late_count}
                    </span>
                    <span className={styles.statLabel}>Late Count</span>
                  </div>
                  <div className={styles.statCard}>
                    <span className={styles.statValue} style={{ color: '#ef4444' }}>
                      {athleteSummary.absent_count}
                    </span>
                    <span className={styles.statLabel}>Absent Count</span>
                  </div>
                </div>

                {/* History Table */}
                <div className={styles.tableWrapper}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>Date & Time</th>
                        <th>Session Title</th>
                        <th>Sport</th>
                        <th>Location</th>
                        <th>Session Status</th>
                        <th>Attendance</th>
                        <th>Coach Remarks</th>
                      </tr>
                    </thead>
                    <tbody>
                      {athleteSummary.history?.length === 0 ? (
                        <tr>
                          <td colSpan="7" className={styles.emptyState}>
                            No session history available for this athlete.
                          </td>
                        </tr>
                      ) : (
                        athleteSummary.history?.map((h, i) => (
                          <tr key={h.session_id || i}>
                            <td style={{ fontSize: 'var(--text-xs)' }}>
                              <div>{new Date(h.date).toLocaleDateString()}</div>
                              <div style={{ color: 'var(--color-text-muted)' }}>
                                {h.start_time} - {h.end_time}
                              </div>
                            </td>
                            <td>
                              <strong>{h.title}</strong>
                            </td>
                            <td>{h.sport_name || '—'}</td>
                            <td style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                              {h.location || '—'}
                            </td>
                            <td>
                              <span
                                className={`${styles.badge} ${
                                  h.session_status === 'completed'
                                    ? styles.badgeCompleted
                                    : h.session_status === 'cancelled'
                                    ? styles.badgeCancelled
                                    : styles.badgeScheduled
                                }`}
                              >
                                {h.session_status}
                              </span>
                            </td>
                            <td>
                              <span className={`${styles.badge} ${getAttBadge(h.attendance_status)}`}>
                                {h.attendance_status || 'unrecorded'}
                              </span>
                            </td>
                            <td style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                              {h.remarks || '—'}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
