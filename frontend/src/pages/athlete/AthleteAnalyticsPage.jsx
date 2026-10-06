import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import { getMyAnalytics } from '../../services/analyticsService'
import PerformanceHistoryChart from '../../components/analytics/PerformanceHistoryChart'

export default function AthleteAnalyticsPage() {
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getMyAnalytics()
      setAnalytics(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load your performance analytics.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const getTrendBadge = (trend) => {
    if (trend === 'Improving') return styles.badgeImproving
    if (trend === 'Declining') return styles.badgeDeclining
    if (trend === 'Stable') return styles.badgeStable
    return styles.badgeInsufficient
  }

  return (
    <AppLayout title="Performance & Attendance Analytics">
      <div className={styles.container}>
        {error && <ErrorMessage message={error} />}

        {loading ? (
          <LoadingSpinner />
        ) : !analytics ? (
          <div className={styles.emptyState}>No analytics data available.</div>
        ) : (
          <div>
            {/* Header info */}
            <div style={{ marginBottom: 'var(--space-4)', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
              <div>
                <h2 style={{ margin: 0, fontSize: 'var(--text-xl)', color: 'var(--color-text)' }}>
                  {analytics.athlete_name}
                </h2>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)', marginTop: 4 }}>
                  Sport: <strong>{analytics.sport_name || 'Unassigned'}</strong> • Lead Coach: <strong>{analytics.coach_name || 'Unassigned'}</strong>
                </div>
              </div>
              <div>
                <span className={`${styles.badge} ${getTrendBadge(analytics.trend)}`} style={{ fontSize: 'var(--text-sm)', padding: '6px 12px' }}>
                  Trend: {analytics.trend}
                </span>
              </div>
            </div>

            {/* Attendance Warning Banner */}
            {analytics.attendance?.warning && (
              <div className={styles.warningBanner} style={{ marginBottom: 'var(--space-5)' }}>
                <span style={{ fontSize: '1.25rem' }}>⚠️</span>
                <div>
                  <strong>Attendance Warning:</strong> Your training attendance rate is{' '}
                  <strong>{analytics.attendance.percentage}%</strong>, which is below the 75% academy requirement.
                  Consistent attendance is required for assessment and tournament participation.
                </div>
              </div>
            )}

            {/* Core Metrics Grid */}
            <div className={styles.statsGrid} style={{ marginBottom: 'var(--space-5)' }}>
              {/* Current Score */}
              <div className={styles.statCard}>
                <span className={styles.statValue} style={{ color: 'var(--color-accent)' }}>
                  {analytics.current_performance?.score !== null && analytics.current_performance?.score !== undefined
                    ? analytics.current_performance.score
                    : '—'}
                </span>
                <span className={styles.statLabel}>Current Score</span>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                  {analytics.current_performance?.assessment_date
                    ? `Date: ${new Date(analytics.current_performance.assessment_date).toLocaleDateString()}`
                    : 'No assessment'}
                </span>
              </div>

              {/* Previous Score */}
              <div className={styles.statCard}>
                <span className={styles.statValue} style={{ color: '#94a3b8' }}>
                  {analytics.previous_performance?.score !== null && analytics.previous_performance?.score !== undefined
                    ? analytics.previous_performance.score
                    : '—'}
                </span>
                <span className={styles.statLabel}>Previous Score</span>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                  {analytics.previous_performance?.assessment_date
                    ? `Date: ${new Date(analytics.previous_performance.assessment_date).toLocaleDateString()}`
                    : 'Not enough history'}
                </span>
              </div>

              {/* Improvement */}
              <div className={styles.statCard}>
                <span
                  className={styles.statValue}
                  style={{
                    color:
                      analytics.improvement_percentage !== null
                        ? analytics.improvement_percentage > 0
                          ? '#22c55e'
                          : analytics.improvement_percentage < 0
                          ? '#ef4444'
                          : '#60a5fa'
                        : '#94a3b8',
                  }}
                >
                  {analytics.improvement_percentage !== null
                    ? `${analytics.improvement_percentage > 0 ? '+' : ''}${analytics.improvement_percentage}%`
                    : '—'}
                </span>
                <span className={styles.statLabel}>Improvement Rate</span>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                  {analytics.improvement_percentage !== null ? `Status: ${analytics.trend}` : 'Not enough history'}
                </span>
              </div>

              {/* Attendance */}
              <div className={styles.statCard}>
                <span
                  className={styles.statValue}
                  style={{
                    color: analytics.attendance?.warning ? '#ef4444' : '#22c55e',
                  }}
                >
                  {analytics.attendance?.percentage !== null && analytics.attendance?.percentage !== undefined
                    ? `${analytics.attendance.percentage}%`
                    : '—'}
                </span>
                <span className={styles.statLabel}>Attendance Rate</span>
                {analytics.attendance?.percentage !== null && (
                  <div className={styles.progressBar}>
                    <div
                      className={styles.progressFill}
                      style={{
                        width: `${Math.min(analytics.attendance.percentage, 100)}%`,
                        backgroundColor: analytics.attendance.warning ? '#ef4444' : '#22c55e',
                      }}
                    />
                  </div>
                )}
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                  {analytics.attendance?.total_sessions
                    ? `${analytics.attendance.attended_sessions} of ${analytics.attendance.total_sessions} sessions`
                    : 'No sessions recorded'}
                </span>
              </div>

              {/* Strongest Metric */}
              <div className={styles.statCard}>
                <span className={styles.statValue} style={{ fontSize: 'var(--text-lg)', color: '#22c55e', textTransform: 'capitalize' }}>
                  {analytics.strongest_metric ? `${analytics.strongest_metric.name} — ${analytics.strongest_metric.score}` : '—'}
                </span>
                <span className={styles.statLabel}>Strongest Metric</span>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                  {analytics.strongest_metric ? 'Highest assessment score' : 'No metrics'}
                </span>
              </div>

              {/* Weakest Metric */}
              <div className={styles.statCard}>
                <span className={styles.statValue} style={{ fontSize: 'var(--text-lg)', color: '#f59e0b', textTransform: 'capitalize' }}>
                  {analytics.weakest_metric ? `${analytics.weakest_metric.name} — ${analytics.weakest_metric.score}` : '—'}
                </span>
                <span className={styles.statLabel}>Focus Area (Weakest)</span>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                  {analytics.weakest_metric ? 'Target for training drills' : 'No metrics'}
                </span>
              </div>
            </div>

            {/* Performance History Chart */}
            <div className={styles.chartContainer}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: 'var(--text-md)', color: 'var(--color-text)' }}>
                  📈 Performance Score Progression
                </h3>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                  {analytics.assessment_history?.length || 0} Assessments Logged
                </span>
              </div>
              <PerformanceHistoryChart history={analytics.assessment_history} />
            </div>

            {/* Metric-wise Breakdown from Latest Assessment */}
            {analytics.metrics && analytics.metrics.length > 0 && (
              <div
                style={{
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius)',
                  padding: '20px',
                  marginBottom: 'var(--space-5)',
                }}
              >
                <h3 style={{ margin: '0 0 16px 0', fontSize: 'var(--text-md)', color: 'var(--color-text)' }}>
                  🎯 Latest Assessment Metrics Breakdown
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
                  {analytics.metrics.map((m) => (
                    <div
                      key={m.name}
                      style={{
                        backgroundColor: 'var(--color-surface-2)',
                        padding: '12px 16px',
                        borderRadius: 6,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 6,
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 600, textTransform: 'capitalize', color: 'var(--color-text)' }}>
                          {m.name}
                        </span>
                        <strong style={{ color: 'var(--color-accent)' }}>{m.score} / 100</strong>
                      </div>
                      <div className={styles.progressBar} style={{ margin: 0 }}>
                        <div
                          className={styles.progressFill}
                          style={{
                            width: `${Math.min(m.score, 100)}%`,
                            backgroundColor:
                              m.score >= 80 ? '#22c55e' : m.score >= 65 ? '#60a5fa' : '#f59e0b',
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Assessment History Table */}
            <div className={styles.tableWrapper}>
              <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)' }}>
                <h3 style={{ margin: 0, fontSize: 'var(--text-md)', color: 'var(--color-text)' }}>
                  📋 Assessment History Log
                </h3>
              </div>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Overall Score</th>
                    <th>Improvement</th>
                    <th>Trend</th>
                    <th>Remarks</th>
                  </tr>
                </thead>
                <tbody>
                  {!analytics.assessment_history || analytics.assessment_history.length === 0 ? (
                    <tr>
                      <td colSpan="5" className={styles.emptyState}>
                        No historical assessments found.
                      </td>
                    </tr>
                  ) : (
                    analytics.assessment_history.map((h) => (
                      <tr key={h.id}>
                        <td>
                          <strong>{new Date(h.date).toLocaleDateString()}</strong>
                        </td>
                        <td>
                          <strong style={{ color: 'var(--color-accent)' }}>{h.overall_score}</strong>
                        </td>
                        <td>
                          {h.improvement_percentage !== null ? (
                            <span
                              style={{
                                color: h.improvement_percentage >= 0 ? '#22c55e' : '#ef4444',
                                fontWeight: 600,
                              }}
                            >
                              {h.improvement_percentage >= 0 ? '+' : ''}
                              {h.improvement_percentage}%
                            </span>
                          ) : (
                            <span style={{ color: 'var(--color-text-muted)' }}>Not enough history</span>
                          )}
                        </td>
                        <td>
                          <span className={`${styles.badge} ${getTrendBadge(h.trend)}`}>
                            {h.trend}
                          </span>
                        </td>
                        <td style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-xs)' }}>
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
