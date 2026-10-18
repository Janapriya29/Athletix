import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AppLayout from '../../layouts/AppLayout'
import KpiCard from '../../components/common/KpiCard'
import TrainingCard from '../../components/common/TrainingCard'
import EmptyState from '../../components/common/EmptyState'
import SkeletonLoader from '../../components/common/SkeletonLoader'
import PerformanceHistoryChart from '../../components/analytics/PerformanceHistoryChart'
import { getMyAnalytics } from '../../services/analyticsService'
import {
  getMyTrainingSessions,
  getMyAttendanceSummary,
} from '../../services/trainingService'
import SportsBanner from '../../components/common/SportsBanner'
import styles from './AthleteDashboard.module.css'

export default function AthleteDashboard() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [attendance, setAttendance] = useState(null)
  const [sessions, setSessions] = useState([])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [anaRes, attRes, sessRes] = await Promise.allSettled([
        getMyAnalytics(),
        getMyAttendanceSummary(),
        getMyTrainingSessions(),
      ])

      if (anaRes.status === 'fulfilled') setAnalytics(anaRes.value)
      if (attRes.status === 'fulfilled') setAttendance(attRes.value)
      if (sessRes.status === 'fulfilled' && Array.isArray(sessRes.value)) {
        setSessions(sessRes.value.slice(0, 4))
      }
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load athlete dashboard')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const currentScore = analytics?.current_performance?.score
  const attRate =
    attendance?.attendance_percentage ??
    analytics?.attendance?.percentage
  const isAttendanceWarning =
    attendance?.warning ??
    analytics?.attendance?.warning ??
    (attRate !== undefined && attRate !== null && attRate < 75)

  const history = analytics?.assessment_history || []
  const metrics = analytics?.metrics || []

  return (
    <AppLayout title="Athlete Performance Hub">
      <div className={styles.dashboard}>
        {/* Sports Hero Banner */}
        <SportsBanner
          image="/images/athlete_track_sprint.jpg"
          alt="Athlete Track Sprint"
          badge="ATHLETE PERFORMANCE HUB"
          title={`Welcome back, ${analytics?.athlete_name || 'Athlete'}`}
          subtitle={
            analytics?.sport_name
              ? `${analytics.sport_name} Squad ${analytics.coach_name ? `• Coach: ${analytics.coach_name}` : ''}`
              : 'Track assessment history, attendance status, and tournament milestones'
          }
          actions={
            <div className={styles.actionRow}>
              <Link to="/athlete/training" className={styles.primaryBtn}>
                <span>⏱️</span> View Sessions
              </Link>
              <Link to="/athlete/attendance" className={styles.secondaryBtn}>
                <span>📋</span> Attendance Record
              </Link>
              <Link to="/athlete/analytics" className={styles.secondaryBtn}>
                <span>📈</span> Detailed Analytics
              </Link>
              <Link to="/athlete/reports" className={styles.secondaryBtn}>
                <span>📑</span> My Reports
              </Link>
            </div>
          }
          metrics={
            analytics ? [
              {
                label: 'Overall Score',
                value: currentScore !== undefined && currentScore !== null ? `${currentScore}/100` : '-',
              },
              {
                label: 'Attendance Rate',
                value: attRate !== undefined && attRate !== null ? `${attRate}%` : '-',
              },
              {
                label: 'Assessments',
                value: history.length > 0 ? history.length : '0',
              },
            ] : undefined
          }
        />

        {/* Low Attendance Alert */}
        {isAttendanceWarning && (
          <div className={styles.attendanceAlert}>
            <div className={styles.alertContent}>
              <span className={styles.alertIcon}>⚠️</span>
              <span className={styles.alertText}>
                <strong>Attendance Warning:</strong> Your current attendance is{' '}
                {attRate != null ? `${Math.round(attRate)}%` : 'under 75%'}, which is below the academy eligibility threshold.
              </span>
            </div>
            <Link to="/athlete/training" className={styles.primaryBtn}>
              Join Upcoming Drills
            </Link>
          </div>
        )}

        {error && (
          <div className={styles.errorBox}>
            <span>{error}</span>
            <button className={styles.retryBtn} onClick={loadData}>Retry</button>
          </div>
        )}

        {/* Top KPI Cards Grid */}
        {loading ? (
          <SkeletonLoader count={5} height="120px" />
        ) : (
          <div className={styles.kpiGrid}>
            <KpiCard
              title="Overall Performance"
              value={currentScore != null ? `${currentScore}/100` : '—'}
              icon="🎯"
              trend={
                analytics?.improvement_percentage != null
                  ? `${analytics.improvement_percentage > 0 ? '+' : ''}${analytics.improvement_percentage.toFixed(1)}%`
                  : null
              }
              trendDirection={
                (analytics?.improvement_percentage ?? 0) >= 0 ? 'up' : 'down'
              }
              variant="accent"
            />
            <KpiCard
              title="Attendance Rate"
              value={attRate != null ? `${Math.round(attRate)}%` : '—'}
              icon="📋"
              trend={
                isAttendanceWarning
                  ? 'Below 75% threshold'
                  : 'Eligibility active'
              }
              trendDirection={isAttendanceWarning ? 'down' : 'up'}
              variant={isAttendanceWarning ? 'danger' : 'default'}
            />
            <KpiCard
              title="Progress Trend"
              value={analytics?.trend || 'Stable'}
              icon="📈"
              variant="default"
            />
            <KpiCard
              title="Top Metric"
              value={analytics?.strongest_metric?.name || 'Agility'}
              icon="⭐"
              trend={
                analytics?.strongest_metric?.score != null
                  ? `Score: ${analytics.strongest_metric.score}`
                  : null
              }
              trendDirection="up"
              variant="accent"
            />
            <KpiCard
              title="Focus Area"
              value={analytics?.weakest_metric?.name || 'Endurance'}
              icon="🎯"
              trend={
                analytics?.weakest_metric?.score != null
                  ? `Score: ${analytics.weakest_metric.score}`
                  : null
              }
              trendDirection="down"
              variant="default"
            />
          </div>
        )}

        {/* 2-Column: Progression Curve & Metric Skills Breakdown */}
        <div className={styles.twoColGrid}>
          {/* Progression Curve */}
          <div className={styles.sectionCard}>
            <div className={styles.sectionHeader}>
              <h2><span>📈</span> Performance Progression Curve</h2>
              <Link to="/athlete/analytics" className={styles.viewAllLink}>
                Analytics Hub →
              </Link>
            </div>

            {loading ? (
              <SkeletonLoader count={1} height="200px" />
            ) : history.length === 0 ? (
              <EmptyState
                icon="📊"
                title="No assessment history recorded"
                description="Your coaches will conduct regular drills and track your skill progression here."
              />
            ) : (
              <PerformanceHistoryChart history={history} />
            )}
          </div>

          {/* Metric Breakdown */}
          <div className={styles.sectionCard}>
            <div className={styles.sectionHeader}>
              <h2><span>⭐</span> Key Skills Breakdown</h2>
              <Link to="/athlete/reports" className={styles.viewAllLink}>
                Full Report →
              </Link>
            </div>

            {loading ? (
              <SkeletonLoader count={4} height="50px" />
            ) : metrics.length === 0 ? (
              <EmptyState
                icon="⭐"
                title="No skill scores recorded"
                description="Sub-metrics like speed, endurance, and tactics appear after coaching evaluations."
              />
            ) : (
              <div className={styles.metricList}>
                {metrics.map((m, idx) => (
                  <div key={idx} className={styles.metricRow}>
                    <div className={styles.metricMeta}>
                      <span className={styles.metricName}>{m.name}</span>
                      <span className={styles.metricScore}>{m.score}/100</span>
                    </div>
                    <div className={styles.barContainer}>
                      <div
                        className={styles.barFill}
                        style={{ width: `${Math.min(100, Math.max(5, m.score))}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Upcoming Training Sessions Section */}
        <div className={styles.sectionCard}>
          <div className={styles.sectionHeader}>
            <h2><span>⏱️</span> Upcoming Training & Practice Sessions</h2>
            <Link to="/athlete/training" className={styles.viewAllLink}>
              View All Sessions →
            </Link>
          </div>

          {loading ? (
            <SkeletonLoader count={2} height="120px" />
          ) : sessions.length === 0 ? (
            <EmptyState
              icon="⏱️"
              title="No upcoming sessions scheduled"
              description="Your coach has not assigned any upcoming practice sessions yet."
              actionText="Check Training Schedule"
              onAction={() => navigate('/athlete/training')}
            />
          ) : (
            <div className={styles.sessionGrid}>
              {sessions.map((sess) => (
                <TrainingCard
                  key={sess.id || sess._id}
                  session={sess}
                  onSelect={() => navigate('/athlete/training')}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
