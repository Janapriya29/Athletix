import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import { getMyAttendanceSummary, getMyTrainingSessions } from '../../services/trainingService'

export default function AthleteTrainingPage() {
  const [sessions, setSessions] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filter
  const [filter, setFilter] = useState('all') // 'all' | 'upcoming' | 'completed'
  const [search, setSearch] = useState('')

  // Details modal
  const [selectedSession, setSelectedSession] = useState(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [sessList, summData] = await Promise.all([
        getMyTrainingSessions(),
        getMyAttendanceSummary().catch(() => null),
      ])
      setSessions(sessList || [])
      setSummary(summData)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load your training schedule.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  // Filter sessions
  const filteredSessions = sessions.filter((s) => {
    if (search.trim()) {
      const q = search.toLowerCase()
      const matchTitle = s.title?.toLowerCase().includes(q)
      const matchSport = s.sport_name?.toLowerCase().includes(q)
      const matchCoach = s.coach_name?.toLowerCase().includes(q)
      if (!matchTitle && !matchSport && !matchCoach) return false
    }

    if (filter === 'upcoming') {
      return s.status === 'scheduled'
    }
    if (filter === 'completed') {
      return s.status === 'completed'
    }
    return true
  })

  // Next session
  const upcomingSessions = sessions
    .filter((s) => s.status === 'scheduled')
    .sort((a, b) => new Date(a.session_date) - new Date(b.session_date))
  const nextSession = upcomingSessions.length > 0 ? upcomingSessions[0] : null

  const getStatusBadge = (st) => {
    const s = st?.toLowerCase()
    if (s === 'completed') return styles.badgeCompleted
    if (s === 'cancelled') return styles.badgeCancelled
    return styles.badgeScheduled
  }

  const getAttBadge = (st) => {
    const s = st?.toLowerCase()
    if (s === 'present') return styles.badgePresent
    if (s === 'late') return styles.badgeLate
    if (s === 'absent') return styles.badgeAbsent
    return styles.badgeInactive
  }

  return (
    <AppLayout title="My Training Schedule">
      <div className={styles.container}>
        {error && <ErrorMessage message={error} />}

        {/* Warning Banner if < 75% */}
        {summary && summary.warning && (
          <div className={styles.warningBanner} style={{ marginBottom: 'var(--space-4)' }}>
            <span style={{ fontSize: '1.25rem' }}>⚠️</span>
            <div>
              <strong>Attendance Warning:</strong> Your current training attendance rate is{' '}
              <strong>{summary.attendance_percentage}%</strong>, which is below the mandatory 75% academy threshold.
              Please attend upcoming scheduled training sessions to remain eligible for competition.
            </div>
          </div>
        )}

        {/* Metrics Grid */}
        <div className={styles.statsGrid} style={{ marginBottom: 'var(--space-5)' }}>
          <div className={styles.statCard}>
            <span className={styles.statValue} style={{ color: 'var(--color-accent)' }}>
              {sessions.length}
            </span>
            <span className={styles.statLabel}>Enrolled Sessions</span>
          </div>

          <div className={styles.statCard}>
            <span
              className={styles.statValue}
              style={{ color: summary?.warning ? '#ef4444' : '#22c55e' }}
            >
              {summary ? `${summary.attendance_percentage}%` : '—'}
            </span>
            <span className={styles.statLabel}>Attendance Rate</span>
            {summary && (
              <div className={styles.progressBar}>
                <div
                  className={styles.progressFill}
                  style={{
                    width: `${Math.min(summary.attendance_percentage, 100)}%`,
                    backgroundColor: summary.warning ? '#ef4444' : '#22c55e',
                  }}
                />
              </div>
            )}
          </div>

          <div className={styles.statCard}>
            <span className={styles.statValue} style={{ color: '#60a5fa' }}>
              {upcomingSessions.length}
            </span>
            <span className={styles.statLabel}>Upcoming Sessions</span>
          </div>

          <div className={styles.statCard}>
            <span className={styles.statValue} style={{ fontSize: 'var(--text-base)', color: 'var(--color-text)' }}>
              {nextSession ? nextSession.title : 'None'}
            </span>
            <span className={styles.statLabel}>
              {nextSession
                ? `${new Date(nextSession.session_date).toLocaleDateString()} at ${nextSession.start_time}`
                : 'Next Scheduled'}
            </span>
          </div>
        </div>

        {/* Filter Controls */}
        <div className={styles.headerBar}>
          <div className={styles.controls}>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="Search session, sport, coach..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                type="button"
                className={filter === 'all' ? styles.primaryBtn : styles.secondaryBtn}
                style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                onClick={() => setFilter('all')}
              >
                All
              </button>
              <button
                type="button"
                className={filter === 'upcoming' ? styles.primaryBtn : styles.secondaryBtn}
                style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                onClick={() => setFilter('upcoming')}
              >
                Upcoming
              </button>
              <button
                type="button"
                className={filter === 'completed' ? styles.primaryBtn : styles.secondaryBtn}
                style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                onClick={() => setFilter('completed')}
              >
                Completed
              </button>
            </div>
          </div>

          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
            Showing <strong>{filteredSessions.length}</strong> sessions
          </span>
        </div>

        {/* Schedule Table */}
        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Session</th>
                  <th>Sport</th>
                  <th>Coach</th>
                  <th>Date & Time</th>
                  <th>Venue</th>
                  <th>Session Status</th>
                  <th>Attendance</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredSessions.length === 0 ? (
                  <tr>
                    <td colSpan="8" className={styles.emptyState}>
                      No training sessions found matching your criteria.
                    </td>
                  </tr>
                ) : (
                  filteredSessions.map((sess) => {
                    // Find athlete's participant status in session
                    const myPart = sess.participants?.find((p) => sess.athlete_ids?.includes(p.athlete_id))
                    const attStatus = myPart?.attendance_status

                    return (
                      <tr key={sess.id}>
                        <td>
                          <strong>{sess.title}</strong>
                          {sess.description && (
                            <div
                              style={{
                                fontSize: '0.75rem',
                                color: 'var(--color-text-muted)',
                                maxWidth: 220,
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                              }}
                            >
                              {sess.description}
                            </div>
                          )}
                        </td>
                        <td>{sess.sport_name || '—'}</td>
                        <td>{sess.coach_name || '—'}</td>
                        <td style={{ fontSize: 'var(--text-xs)' }}>
                          <div>{new Date(sess.session_date).toLocaleDateString()}</div>
                          <div style={{ color: 'var(--color-text-muted)' }}>
                            {sess.start_time} – {sess.end_time}
                          </div>
                        </td>
                        <td style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-xs)' }}>
                          {sess.location || '—'}
                        </td>
                        <td>
                          <span className={`${styles.badge} ${getStatusBadge(sess.status)}`}>
                            {sess.status}
                          </span>
                        </td>
                        <td>
                          {attStatus ? (
                            <span className={`${styles.badge} ${getAttBadge(attStatus)}`}>
                              {attStatus}
                            </span>
                          ) : (
                            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                              {sess.status === 'scheduled' ? 'Scheduled' : 'Unrecorded'}
                            </span>
                          )}
                        </td>
                        <td>
                          <button
                            className={styles.actionBtn}
                            onClick={() => setSelectedSession(sess)}
                          >
                            Details
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Modal: Session Details */}
        {selectedSession && (
          <div className={styles.modalOverlay}>
            <div className={styles.modal} style={{ maxWidth: 520 }}>
              <div className={styles.modalHeader}>
                <h3 className={styles.modalTitle}>Training Session Details</h3>
                <button className={styles.closeBtn} onClick={() => setSelectedSession(null)}>
                  ×
                </button>
              </div>

              <div className={styles.modalBody}>
                <h2 style={{ fontSize: 'var(--text-xl)', color: 'var(--color-text)', marginBottom: 8 }}>
                  {selectedSession.title}
                </h2>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: 12,
                    background: 'var(--color-surface-2)',
                    padding: 16,
                    borderRadius: 'var(--radius)',
                  }}
                >
                  <div>
                    <span className={styles.formLabel}>Sport</span>
                    <p style={{ fontWeight: 600, color: 'var(--color-text)' }}>
                      {selectedSession.sport_name || '—'}
                    </p>
                  </div>
                  <div>
                    <span className={styles.formLabel}>Coach</span>
                    <p style={{ fontWeight: 600, color: 'var(--color-text)' }}>
                      {selectedSession.coach_name || '—'}
                    </p>
                  </div>
                  <div>
                    <span className={styles.formLabel}>Date</span>
                    <p style={{ color: 'var(--color-text)' }}>
                      {new Date(selectedSession.session_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <span className={styles.formLabel}>Time</span>
                    <p style={{ color: 'var(--color-text)' }}>
                      {selectedSession.start_time} – {selectedSession.end_time}
                    </p>
                  </div>
                  <div>
                    <span className={styles.formLabel}>Venue / Location</span>
                    <p style={{ color: 'var(--color-text)' }}>{selectedSession.location}</p>
                  </div>
                  <div>
                    <span className={styles.formLabel}>Session Status</span>
                    <div>
                      <span className={`${styles.badge} ${getStatusBadge(selectedSession.status)}`}>
                        {selectedSession.status}
                      </span>
                    </div>
                  </div>
                </div>

                {selectedSession.description && (
                  <div style={{ marginTop: 14 }}>
                    <span className={styles.formLabel}>Objectives & Focus</span>
                    <p style={{ color: 'var(--color-text)', fontSize: 'var(--text-sm)', lineHeight: 1.5 }}>
                      {selectedSession.description}
                    </p>
                  </div>
                )}
              </div>

              <div className={styles.modalFooter}>
                <button className={styles.secondaryBtn} onClick={() => setSelectedSession(null)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
