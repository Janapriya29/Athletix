import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import { getMyAttendanceSummary } from '../../services/trainingService'

export default function AthleteAttendancePage() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filters
  const [statusFilter, setStatusFilter] = useState('all')
  const [search, setSearch] = useState('')

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getMyAttendanceSummary()
      setSummary(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load your attendance records.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const getAttBadge = (st) => {
    const s = st?.toLowerCase()
    if (s === 'present') return styles.badgePresent
    if (s === 'late') return styles.badgeLate
    if (s === 'absent') return styles.badgeAbsent
    return styles.badgeInactive
  }

  const filteredHistory = (summary?.history || []).filter((h) => {
    if (statusFilter !== 'all') {
      if ((h.attendance_status || '').toLowerCase() !== statusFilter) {
        return false
      }
    }
    if (search.trim()) {
      const q = search.toLowerCase()
      const matchTitle = h.title?.toLowerCase().includes(q)
      const matchSport = h.sport_name?.toLowerCase().includes(q)
      const matchCoach = h.coach_name?.toLowerCase().includes(q)
      if (!matchTitle && !matchSport && !matchCoach) return false
    }
    return true
  })

  return (
    <AppLayout title="My Attendance Records">
      <div className={styles.container}>
        {error && <ErrorMessage message={error} />}

        {loading ? (
          <LoadingSpinner />
        ) : !summary ? (
          <div className={styles.emptyState}>No attendance data found.</div>
        ) : (
          <div>
            {/* Banner: Warning or Good Standing */}
            {summary.warning ? (
              <div className={styles.warningBanner} style={{ marginBottom: 'var(--space-4)' }}>
                <span style={{ fontSize: '1.5rem' }}>⚠️</span>
                <div>
                  <strong>ATTENDANCE WARNING:</strong> Your attendance rate is{' '}
                  <strong>{summary.attendance_percentage}%</strong>, which is below the academy's mandatory 75%
                  compliance threshold. Maintain consistent training attendance to avoid suspension from tournament rosters.
                </div>
              </div>
            ) : (
              <div
                style={{
                  backgroundColor: 'rgba(34, 197, 94, 0.12)',
                  border: '1px solid rgba(34, 197, 94, 0.3)',
                  color: '#4ade80',
                  padding: 'var(--space-4)',
                  borderRadius: 'var(--radius)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-3)',
                  marginBottom: 'var(--space-4)',
                  fontSize: 'var(--text-sm)',
                }}
              >
                <span style={{ fontSize: '1.25rem' }}>✅</span>
                <div>
                  <strong>Good Standing:</strong> Your attendance rate is{' '}
                  <strong>{summary.attendance_percentage}%</strong> (above the 75% requirement). Great commitment!
                </div>
              </div>
            )}

            {/* Stat Cards */}
            <div className={styles.statsGrid} style={{ marginBottom: 'var(--space-5)' }}>
              <div className={styles.statCard}>
                <span
                  className={styles.statValue}
                  style={{ color: summary.warning ? '#ef4444' : '#22c55e' }}
                >
                  {summary.attendance_percentage}%
                </span>
                <span className={styles.statLabel}>Attendance Rate</span>
                <div className={styles.progressBar}>
                  <div
                    className={styles.progressFill}
                    style={{
                      width: `${Math.min(summary.attendance_percentage, 100)}%`,
                      backgroundColor: summary.warning ? '#ef4444' : '#22c55e',
                    }}
                  />
                </div>
              </div>

              <div className={styles.statCard}>
                <span className={styles.statValue}>{summary.total_sessions}</span>
                <span className={styles.statLabel}>Applicable Sessions</span>
              </div>

              <div className={styles.statCard}>
                <span className={styles.statValue} style={{ color: '#22c55e' }}>
                  {summary.attended_sessions}
                </span>
                <span className={styles.statLabel}>Attended (Pres + Late)</span>
              </div>

              <div className={styles.statCard}>
                <span className={styles.statValue} style={{ color: '#3b82f6' }}>
                  {summary.present_count}
                </span>
                <span className={styles.statLabel}>On-Time Present</span>
              </div>

              <div className={styles.statCard}>
                <span className={styles.statValue} style={{ color: '#f59e0b' }}>
                  {summary.late_count}
                </span>
                <span className={styles.statLabel}>Late Sessions</span>
              </div>

              <div className={styles.statCard}>
                <span className={styles.statValue} style={{ color: '#ef4444' }}>
                  {summary.absent_count}
                </span>
                <span className={styles.statLabel}>Absent Sessions</span>
              </div>
            </div>

            {/* Filters */}
            <div className={styles.headerBar}>
              <div className={styles.controls}>
                <input
                  type="text"
                  className={styles.searchInput}
                  placeholder="Search session title, coach..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <select
                  className={styles.selectInput}
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="all">All Statuses</option>
                  <option value="present">Present Only</option>
                  <option value="late">Late Only</option>
                  <option value="absent">Absent Only</option>
                </select>
              </div>

              <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
                Showing <strong>{filteredHistory.length}</strong> of {summary.history?.length || 0} sessions
              </span>
            </div>

            {/* History Table */}
            <div className={styles.tableWrapper}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Date & Time</th>
                    <th>Session Title</th>
                    <th>Sport</th>
                    <th>Lead Coach</th>
                    <th>Venue</th>
                    <th>Attendance Status</th>
                    <th>Coach Remarks</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredHistory.length === 0 ? (
                    <tr>
                      <td colSpan="7" className={styles.emptyState}>
                        No training attendance records found matching filters.
                      </td>
                    </tr>
                  ) : (
                    filteredHistory.map((h, i) => (
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
                        <td>{h.coach_name || '—'}</td>
                        <td style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                          {h.location || '—'}
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
    </AppLayout>
  )
}
