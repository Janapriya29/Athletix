import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AppLayout from '../../layouts/AppLayout'
import KpiCard from '../../components/common/KpiCard'
import AthleteCard from '../../components/common/AthleteCard'
import TrainingCard from '../../components/common/TrainingCard'
import EmptyState from '../../components/common/EmptyState'
import SkeletonLoader from '../../components/common/SkeletonLoader'
import {
  getCoachAnalyticsSummary,
  getCoachAthletesAnalytics,
} from '../../services/analyticsService'
import {
  getTrainingSessions,
  getCoachTrainingSummary,
} from '../../services/trainingService'
import SportsBanner from '../../components/common/SportsBanner'
import styles from './CoachDashboard.module.css'

export default function CoachDashboard() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [summary, setSummary] = useState(null)
  const [trainingSummary, setTrainingSummary] = useState(null)
  const [athletes, setAthletes] = useState([])
  const [sessions, setSessions] = useState([])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [sumRes, athRes, trainSumRes, sessRes] = await Promise.allSettled([
        getCoachAnalyticsSummary(),
        getCoachAthletesAnalytics(),
        getCoachTrainingSummary(),
        getTrainingSessions({ limit: 4 }),
      ])

      if (sumRes.status === 'fulfilled') setSummary(sumRes.value)
      if (trainSumRes.status === 'fulfilled') setTrainingSummary(trainSumRes.value)
      if (athRes.status === 'fulfilled' && Array.isArray(athRes.value)) {
        setAthletes(athRes.value)
      }
      if (sessRes.status === 'fulfilled' && Array.isArray(sessRes.value)) {
        setSessions(sessRes.value.slice(0, 4))
      }
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load coach dashboard')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const athletesAtRisk = summary?.athletes_below_attendance_threshold || 0

  return (
    <AppLayout title="Coach Command Center">
      <div className={styles.dashboard}>
        {/* Sports Hero Banner */}
        <SportsBanner
          image="/images/coach_tactical_training.jpg"
          alt="Coach Tactical Training"
          badge="COACH COMMAND CENTER"
          title="Coach Command Center"
          subtitle="Squad performance tracking, drills management & athlete readiness"
          actions={
            <div className={styles.actionRow}>
              <Link to="/coach/assessments" className={styles.primaryBtn}>
                <span>🎯</span> Conduct Assessment
              </Link>
              <Link to="/coach/attendance" className={styles.secondaryBtn}>
                <span>📋</span> Mark Attendance
              </Link>
              <Link to="/coach/training" className={styles.secondaryBtn}>
                <span>⏱️</span> Schedule Drills
              </Link>
              <Link to="/coach/reports" className={styles.secondaryBtn}>
                <span>📑</span> Squad Reports
              </Link>
            </div>
          }
          metrics={
            summary ? [
              { label: 'Assigned Squad', value: summary.total_athletes ?? '-' },
              { label: 'Avg Attendance', value: summary.average_attendance_percentage ? `${summary.average_attendance_percentage}%` : '-' },
              { label: 'Total Drills', value: trainingSummary?.total_sessions ?? '-' },
            ] : undefined
          }
        />

        {/* Attendance Risk Alert */}
        {athletesAtRisk > 0 && (
          <div className={styles.alertBanner}>
            <div className={styles.alertContent}>
              <span className={styles.alertIcon}>⚠️</span>
              <span className={styles.alertText}>
                <strong>{athletesAtRisk} athlete{athletesAtRisk > 1 ? 's' : ''}</strong> have attendance below the 75% threshold and require intervention.
              </span>
            </div>
            <Link to="/coach/attendance" className={styles.alertBtn}>
              Review Attendance
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
              title="Assigned Athletes"
              value={summary?.total_assigned_athletes ?? athletes.length}
              icon="🏃"
              variant="default"
            />
            <KpiCard
              title="Squad Attendance"
              value={
                summary?.average_attendance != null
                  ? `${Math.round(summary.average_attendance)}%`
                  : 'N/A'
              }
              icon="📋"
              trend={athletesAtRisk > 0 ? `${athletesAtRisk} below 75%` : 'Target met'}
              trendDirection={athletesAtRisk > 0 ? 'down' : 'up'}
              variant={(summary?.average_attendance ?? 100) < 75 ? 'danger' : 'default'}
            />
            <KpiCard
              title="Squad Performance"
              value={
                summary?.average_performance != null
                  ? summary.average_performance.toFixed(1)
                  : 'N/A'
              }
              icon="🎯"
              variant="accent"
            />
            <KpiCard
              title="Improving Athletes"
              value={summary?.improving_athletes_count ?? 0}
              icon="📈"
              trend="Positive trend"
              trendDirection="up"
              variant="accent"
            />
            <KpiCard
              title="Sessions Conducted"
              value={trainingSummary?.total_sessions ?? sessions.length}
              icon="⏱️"
              variant="default"
            />
          </div>
        )}

        {/* Assigned Athletes Section */}
        <div className={styles.sectionCard}>
          <div className={styles.sectionHeader}>
            <h2><span>🏃</span> Squad Athletes & Readiness</h2>
            <Link to="/coach/athletes" className={styles.viewAllLink}>
              View All Athletes ({athletes.length}) →
            </Link>
          </div>

          {loading ? (
            <SkeletonLoader count={3} height="160px" />
          ) : athletes.length === 0 ? (
            <EmptyState
              icon="🏃"
              title="No athletes assigned"
              description="Your academy administrator will assign athletes to your training squad."
              actionText="View Athletes Directory"
              onAction={() => navigate('/coach/athletes')}
            />
          ) : (
            <div className={styles.athleteGrid}>
              {athletes.map((ath) => (
                <AthleteCard
                  key={ath.athlete_id}
                  athlete={{
                    id: ath.athlete_id,
                    full_name: ath.athlete_name,
                    sport_name: ath.sport_name,
                    status: 'active',
                  }}
                  score={ath.current_score}
                  attendance={ath.attendance_percentage != null ? Math.round(ath.attendance_percentage) : null}
                  trend={ath.trend}
                  onView={() => navigate(`/coach/athletes`)}
                  onAssess={() => navigate(`/coach/assessments`)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Upcoming Training Sessions Section */}
        <div className={styles.sectionCard}>
          <div className={styles.sectionHeader}>
            <h2><span>⏱️</span> Upcoming Training & Drills</h2>
            <Link to="/coach/training" className={styles.viewAllLink}>
              Manage Sessions →
            </Link>
          </div>

          {loading ? (
            <SkeletonLoader count={2} height="120px" />
          ) : sessions.length === 0 ? (
            <EmptyState
              icon="⏱️"
              title="No training sessions scheduled"
              description="Plan tactical practice sessions and technical drills for your squad."
              actionText="Schedule Session"
              onAction={() => navigate('/coach/training')}
            />
          ) : (
            <div className={styles.sessionGrid}>
              {sessions.map((sess) => (
                <TrainingCard
                  key={sess.id || sess._id}
                  session={sess}
                  onAttendance={() => navigate('/coach/attendance')}
                  onSelect={() => navigate('/coach/training')}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
