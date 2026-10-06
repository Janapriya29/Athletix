import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import {
  getAthleteAnalytics,
  getCoachAnalyticsSummary,
  getCoachAthletesAnalytics,
} from '../../services/analyticsService'
import { getSports } from '../../services/sportsService'
import PerformanceHistoryChart from '../../components/analytics/PerformanceHistoryChart'

export default function AnalyticsPage() {
  const [summary, setSummary] = useState(null)
  const [athletes, setAthletes] = useState([])
  const [sports, setSports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filters
  const [search, setSearch] = useState('')
  const [sportFilter, setSportFilter] = useState('all')

  // Detailed athlete analytics modal
  const [selectedAthleteId, setSelectedAthleteId] = useState(null)
  const [athleteDetail, setAthleteDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {}
      if (sportFilter !== 'all') params.sport_id = sportFilter

      const [summRes, athsRes, sportsRes] = await Promise.all([
        getCoachAnalyticsSummary(),
        getCoachAthletesAnalytics(params),
        getSports().catch(() => []),
      ])

      setSummary(summRes)
      setAthletes(athsRes || [])
      setSports(sportsRes || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load coach performance analytics.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [sportFilter])

  const openAthleteModal = async (athleteId) => {
    try {
      setSelectedAthleteId(athleteId)
      setDetailLoading(true)
      setDetailError(null)
      const data = await getAthleteAnalytics(athleteId)
      setAthleteDetail(data)
    } catch (err) {
      setDetailError(err.response?.data?.detail || 'Failed to load detailed athlete analytics.')
    } finally {
      setDetailLoading(false)
    }
  }

  const closeAthleteModal = () => {
    setSelectedAthleteId(null)
    setAthleteDetail(null)
  }

  const getTrendBadge = (trend) => {
    if (trend === 'Improving') return styles.badgeImproving
    if (trend === 'Declining') return styles.badgeDeclining
    if (trend === 'Stable') return styles.badgeStable
    return styles.badgeInsufficient
  }

  const filteredAthletes = athletes.filter((a) => {
    if (search.trim()) {
      const q = search.toLowerCase()
      const matchName = a.athlete_name?.toLowerCase().includes(q)
      const matchSport = a.sport_name?.toLowerCase().includes(q)
      if (!matchName && !matchSport) return false
    }
    return true
  })

  return (
    <AppLayout title="Assigned Athletes Performance Analytics">
      <div className={styles.container}>
        {error && <ErrorMessage message={error} />}

        {/* Aggregate Coach Metric Cards */}
        {summary && (
          <div className={styles.statsGrid} style={{ marginBottom: 'var(--space-5)' }}>
            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: 'var(--color-accent)' }}>
                {summary.total_assigned_athletes}
              </span>
              <span className={styles.statLabel}>Assigned Athletes</span>
            </div>

            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: '#60a5fa' }}>
                {summary.average_performance !== null ? `${summary.average_performance}` : '—'}
              </span>
              <span className={styles.statLabel}>Avg Performance Score</span>
            </div>

            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: '#22c55e' }}>
                {summary.average_attendance !== null ? `${summary.average_attendance}%` : '—'}
              </span>
              <span className={styles.statLabel}>Avg Attendance Rate</span>
            </div>

            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: '#22c55e' }}>
                {summary.improving_athletes_count}
              </span>
              <span className={styles.statLabel}>Improving Athletes</span>
            </div>

            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: '#ef4444' }}>
                {summary.declining_athletes_count}
              </span>
              <span className={styles.statLabel}>Declining Athletes</span>
            </div>

            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: '#f59e0b' }}>
                {summary.athletes_below_attendance_threshold}
              </span>
              <span className={styles.statLabel}>Below 75% Attendance</span>
            </div>
          </div>
        )}

        {/* Filter Controls */}
        <div className={styles.headerBar}>
          <div className={styles.controls}>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="Search athlete by name, sport..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              className={styles.selectInput}
              value={sportFilter}
              onChange={(e) => setSportFilter(e.target.value)}
            >
              <option value="all">All Sports</option>
              {sports.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
            Showing <strong>{filteredAthletes.length}</strong> of {athletes.length} athletes
          </span>
        </div>

        {/* Athletes Analytics Table */}
        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Athlete Name</th>
                  <th>Sport</th>
                  <th>Current Score</th>
                  <th>Previous Score</th>
                  <th>Improvement</th>
                  <th>Trend</th>
                  <th>Attendance</th>
                  <th>Strongest Metric</th>
                  <th>Weakest Metric</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredAthletes.length === 0 ? (
                  <tr>
                    <td colSpan="10" className={styles.emptyState}>
                      No assigned athletes found matching criteria.
                    </td>
                  </tr>
                ) : (
                  filteredAthletes.map((a) => (
                    <tr key={a.athlete_id}>
                      <td>
                        <strong>{a.athlete_name}</strong>
                      </td>
                      <td>{a.sport_name || '—'}</td>
                      <td>
                        <strong style={{ color: 'var(--color-accent)' }}>
                          {a.current_score !== null ? a.current_score : '—'}
                        </strong>
                      </td>
                      <td style={{ color: 'var(--color-text-muted)' }}>
                        {a.previous_score !== null ? a.previous_score : '—'}
                      </td>
                      <td>
                        {a.improvement_percentage !== null ? (
                          <span
                            style={{
                              color: a.improvement_percentage >= 0 ? '#22c55e' : '#ef4444',
                              fontWeight: 600,
                            }}
                          >
                            {a.improvement_percentage >= 0 ? '+' : ''}
                            {a.improvement_percentage}%
                          </span>
                        ) : (
                          <span style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
                            Not enough history
                          </span>
                        )}
                      </td>
                      <td>
                        <span className={`${styles.badge} ${getTrendBadge(a.trend)}`}>
                          {a.trend}
                        </span>
                      </td>
                      <td>
                        {a.attendance_percentage !== null ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <span
                              style={{
                                fontWeight: 600,
                                color: a.attendance_warning ? '#ef4444' : '#22c55e',
                              }}
                            >
                              {a.attendance_percentage}%
                            </span>
                            {a.attendance_warning && (
                              <span title="Attendance below 75%">⚠️</span>
                            )}
                          </div>
                        ) : (
                          <span style={{ color: 'var(--color-text-muted)' }}>—</span>
                        )}
                      </td>
                      <td style={{ fontSize: 'var(--text-xs)', textTransform: 'capitalize' }}>
                        {a.strongest_metric
                          ? `${a.strongest_metric.name} (${a.strongest_metric.score})`
                          : '—'}
                      </td>
                      <td style={{ fontSize: 'var(--text-xs)', textTransform: 'capitalize' }}>
                        {a.weakest_metric
                          ? `${a.weakest_metric.name} (${a.weakest_metric.score})`
                          : '—'}
                      </td>
                      <td>
                        <button
                          className={styles.actionBtn}
                          onClick={() => openAthleteModal(a.athlete_id)}
                        >
                          Detailed View
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Modal: Detailed Athlete Analytics */}
        {selectedAthleteId && (
          <div className={styles.modalOverlay}>
            <div className={styles.modal} style={{ maxWidth: 720 }}>
              <div className={styles.modalHeader}>
                <div>
                  <h3 className={styles.modalTitle}>
                    {athleteDetail ? athleteDetail.athlete_name : 'Loading Athlete Analytics...'}
                  </h3>
                  {athleteDetail && (
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                      Sport: {athleteDetail.sport_name || 'Unassigned'} • Trend: {athleteDetail.trend}
                    </div>
                  )}
                </div>
                <button className={styles.closeBtn} onClick={closeAthleteModal}>
                  ×
                </button>
              </div>

              <div className={styles.modalBody}>
                {detailLoading ? (
                  <LoadingSpinner />
                ) : detailError ? (
                  <div className={styles.alertError}>{detailError}</div>
                ) : !athleteDetail ? (
                  <div className={styles.emptyState}>No detailed analytics found.</div>
                ) : (
                  <div>
                    {/* Warning if below threshold */}
                    {athleteDetail.attendance?.warning && (
                      <div className={styles.warningBanner} style={{ marginBottom: 16 }}>
                        <span>⚠️</span>
                        <div>
                          <strong>Attendance Alert:</strong> This athlete has attended only{' '}
                          <strong>{athleteDetail.attendance.percentage}%</strong> of training sessions.
                        </div>
                      </div>
                    )}

                    {/* Stats summary */}
                    <div className={styles.statsGrid} style={{ marginBottom: 16 }}>
                      <div className={styles.statCard}>
                        <span className={styles.statValue} style={{ color: 'var(--color-accent)' }}>
                          {athleteDetail.current_performance?.score ?? '—'}
                        </span>
                        <span className={styles.statLabel}>Current Score</span>
                      </div>
                      <div className={styles.statCard}>
                        <span className={styles.statValue} style={{ color: '#94a3b8' }}>
                          {athleteDetail.previous_performance?.score ?? '—'}
                        </span>
                        <span className={styles.statLabel}>Previous Score</span>
                      </div>
                      <div className={styles.statCard}>
                        <span
                          className={styles.statValue}
                          style={{
                            color:
                              athleteDetail.improvement_percentage !== null
                                ? athleteDetail.improvement_percentage >= 0
                                  ? '#22c55e'
                                  : '#ef4444'
                                : '#94a3b8',
                          }}
                        >
                          {athleteDetail.improvement_percentage !== null
                            ? `${athleteDetail.improvement_percentage >= 0 ? '+' : ''}${athleteDetail.improvement_percentage}%`
                            : '—'}
                        </span>
                        <span className={styles.statLabel}>Improvement</span>
                      </div>
                      <div className={styles.statCard}>
                        <span
                          className={styles.statValue}
                          style={{
                            color: athleteDetail.attendance?.warning ? '#ef4444' : '#22c55e',
                          }}
                        >
                          {athleteDetail.attendance?.percentage !== null
                            ? `${athleteDetail.attendance.percentage}%`
                            : '—'}
                        </span>
                        <span className={styles.statLabel}>Attendance</span>
                      </div>
                    </div>

                    {/* Performance History Chart */}
                    <div className={styles.chartContainer}>
                      <h4 style={{ margin: '0 0 10px 0', fontSize: 'var(--text-sm)', color: 'var(--color-text)' }}>
                        Performance History
                      </h4>
                      <PerformanceHistoryChart history={athleteDetail.assessment_history} />
                    </div>

                    {/* Metrics breakdown */}
                    {athleteDetail.metrics?.length > 0 && (
                      <div style={{ marginBottom: 16 }}>
                        <h4 style={{ margin: '0 0 10px 0', fontSize: 'var(--text-sm)', color: 'var(--color-text)' }}>
                          Latest Assessment Metrics
                        </h4>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                          {athleteDetail.metrics.map((m) => (
                            <div
                              key={m.name}
                              style={{
                                backgroundColor: 'var(--color-surface-2)',
                                padding: '8px 12px',
                                borderRadius: 4,
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                                <span style={{ textTransform: 'capitalize', fontWeight: 600 }}>{m.name}</span>
                                <strong style={{ color: 'var(--color-accent)' }}>{m.score}</strong>
                              </div>
                              <div className={styles.progressBar} style={{ margin: '4px 0 0 0' }}>
                                <div
                                  className={styles.progressFill}
                                  style={{
                                    width: `${Math.min(m.score, 100)}%`,
                                    backgroundColor: m.score >= 75 ? '#22c55e' : '#f59e0b',
                                  }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className={styles.modalFooter}>
                <button type="button" className={styles.secondaryBtn} onClick={closeAthleteModal}>
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
