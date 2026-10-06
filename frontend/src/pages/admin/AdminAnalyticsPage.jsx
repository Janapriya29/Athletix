import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import {
  getAdminAnalyticsSummary,
  getAdminSportsAnalytics,
  getAthleteAnalytics,
} from '../../services/analyticsService'
import { getAthletes } from '../../services/athletesService'
import PerformanceHistoryChart from '../../components/analytics/PerformanceHistoryChart'

export default function AdminAnalyticsPage() {
  const [summary, setSummary] = useState(null)
  const [sportsAnalytics, setSportsAnalytics] = useState([])
  const [allAthletes, setAllAthletes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Athlete Drill-down Modal
  const [selectedAthleteId, setSelectedAthleteId] = useState('')
  const [athleteDetail, setAthleteDetail] = useState(null)
  const [drillLoading, setDrillLoading] = useState(false)
  const [drillError, setDrillError] = useState(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [summRes, sportsRes, athsRes] = await Promise.all([
        getAdminAnalyticsSummary(),
        getAdminSportsAnalytics(),
        getAthletes().catch(() => []),
      ])
      setSummary(summRes)
      setSportsAnalytics(sportsRes?.sports || [])
      setAllAthletes(athsRes || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load academy analytics.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleInspectAthlete = async (athId) => {
    if (!athId) return
    try {
      setSelectedAthleteId(athId)
      setDrillLoading(true)
      setDrillError(null)
      const data = await getAthleteAnalytics(athId)
      setAthleteDetail(data)
    } catch (err) {
      setDrillError(err.response?.data?.detail || 'Failed to load athlete analytics.')
    } finally {
      setDrillLoading(false)
    }
  }

  const closeDrillModal = () => {
    setSelectedAthleteId('')
    setAthleteDetail(null)
  }

  return (
    <AppLayout title="Academy Performance & Attendance Analytics">
      <div className={styles.container}>
        {error && <ErrorMessage message={error} />}

        {loading ? (
          <LoadingSpinner />
        ) : (
          <div>
            {/* Top Stat Summary Cards */}
            {summary && (
              <div className={styles.statsGrid} style={{ marginBottom: 'var(--space-5)' }}>
                <div className={styles.statCard}>
                  <span className={styles.statValue} style={{ color: 'var(--color-accent)' }}>
                    {summary.total_athletes}
                  </span>
                  <span className={styles.statLabel}>Total Athletes</span>
                </div>

                <div className={styles.statCard}>
                  <span className={styles.statValue}>{summary.total_coaches}</span>
                  <span className={styles.statLabel}>Total Coaches</span>
                </div>

                <div className={styles.statCard}>
                  <span className={styles.statValue} style={{ color: '#60a5fa' }}>
                    {summary.total_active_sports}
                  </span>
                  <span className={styles.statLabel}>Active Sports</span>
                </div>

                <div className={styles.statCard}>
                  <span className={styles.statValue} style={{ color: '#a855f7' }}>
                    {summary.total_assessments}
                  </span>
                  <span className={styles.statLabel}>Assessments Logged</span>
                </div>

                <div className={styles.statCard}>
                  <span className={styles.statValue} style={{ color: '#22c55e' }}>
                    {summary.average_performance !== null ? summary.average_performance : '—'}
                  </span>
                  <span className={styles.statLabel}>Avg Academy Score</span>
                </div>

                <div className={styles.statCard}>
                  <span className={styles.statValue} style={{ color: '#3b82f6' }}>
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
                  <span className={styles.statValue} style={{ color: '#60a5fa' }}>
                    {summary.stable_athletes_count}
                  </span>
                  <span className={styles.statLabel}>Stable Athletes</span>
                </div>

                <div className={styles.statCard}>
                  <span className={styles.statValue} style={{ color: '#f59e0b' }}>
                    {summary.athletes_below_attendance_threshold}
                  </span>
                  <span className={styles.statLabel}>Below 75% Attendance</span>
                </div>
              </div>
            )}

            {/* Quick Athlete Drill-down Bar */}
            <div
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius)',
                padding: '16px 20px',
                marginBottom: 'var(--space-5)',
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                gap: 12,
              }}
            >
              <label style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--color-text)' }}>
                🔍 Inspect Individual Athlete Analytics:
              </label>
              <select
                className={styles.selectInput}
                style={{ flex: 1, maxWidth: 350 }}
                onChange={(e) => handleInspectAthlete(e.target.value)}
                defaultValue=""
              >
                <option value="" disabled>
                  Select athlete to inspect full report...
                </option>
                {allAthletes.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.full_name} ({a.sport_name || 'No Sport'})
                  </option>
                ))}
              </select>
            </div>

            {/* Sport-wise Analytics Table */}
            <div className={styles.tableWrapper}>
              <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)' }}>
                <h3 style={{ margin: 0, fontSize: 'var(--text-md)', color: 'var(--color-text)' }}>
                  🏅 Sport-wise Performance & Attendance Breakdown
                </h3>
              </div>

              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Sport</th>
                    <th>Enrolled Athletes</th>
                    <th>Assessments Completed</th>
                    <th>Average Score</th>
                    <th>Average Attendance Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {sportsAnalytics.length === 0 ? (
                    <tr>
                      <td colSpan="5" className={styles.emptyState}>
                        No sports analytics available.
                      </td>
                    </tr>
                  ) : (
                    sportsAnalytics.map((s) => (
                      <tr key={s.sport_id}>
                        <td>
                          <strong>{s.sport_name}</strong>
                        </td>
                        <td>
                          <strong style={{ color: 'var(--color-accent)' }}>{s.athlete_count}</strong> athletes
                        </td>
                        <td>{s.assessment_count} assessments</td>
                        <td>
                          <span style={{ fontWeight: 600, color: '#60a5fa' }}>
                            {s.average_performance !== null ? s.average_performance : '—'}
                          </span>
                        </td>
                        <td>
                          <span style={{ fontWeight: 600, color: '#22c55e' }}>
                            {s.average_attendance !== null ? `${s.average_attendance}%` : '—'}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Modal: Detailed Athlete Analytics Drill-down */}
            {selectedAthleteId && (
              <div className={styles.modalOverlay}>
                <div className={styles.modal} style={{ maxWidth: 720 }}>
                  <div className={styles.modalHeader}>
                    <div>
                      <h3 className={styles.modalTitle}>
                        {athleteDetail ? athleteDetail.athlete_name : 'Loading Athlete...'}
                      </h3>
                      {athleteDetail && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                          Sport: {athleteDetail.sport_name || 'Unassigned'} • Trend: {athleteDetail.trend}
                        </div>
                      )}
                    </div>
                    <button className={styles.closeBtn} onClick={closeDrillModal}>
                      ×
                    </button>
                  </div>

                  <div className={styles.modalBody}>
                    {drillLoading ? (
                      <LoadingSpinner />
                    ) : drillError ? (
                      <div className={styles.alertError}>{drillError}</div>
                    ) : !athleteDetail ? (
                      <div className={styles.emptyState}>No data found.</div>
                    ) : (
                      <div>
                        {/* Attendance Warning if below threshold */}
                        {athleteDetail.attendance?.warning && (
                          <div className={styles.warningBanner} style={{ marginBottom: 16 }}>
                            <span>⚠️</span>
                            <div>
                              <strong>Attendance Warning:</strong> Attendance rate is{' '}
                              <strong>{athleteDetail.attendance.percentage}%</strong> (&lt; 75% requirement).
                            </div>
                          </div>
                        )}

                        {/* Stats grid */}
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

                        {/* Chart */}
                        <div className={styles.chartContainer}>
                          <h4 style={{ margin: '0 0 10px 0', fontSize: 'var(--text-sm)', color: 'var(--color-text)' }}>
                            Performance Progression
                          </h4>
                          <PerformanceHistoryChart history={athleteDetail.assessment_history} />
                        </div>

                        {/* Metric Scores */}
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
                    <button type="button" className={styles.secondaryBtn} onClick={closeDrillModal}>
                      Close
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
