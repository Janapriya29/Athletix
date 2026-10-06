import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import AppLayout from '../../layouts/AppLayout'
import KpiCard from '../../components/common/KpiCard'
import TrainingCard from '../../components/common/TrainingCard'
import EmptyState from '../../components/common/EmptyState'
import SkeletonLoader from '../../components/common/SkeletonLoader'
import reportService from '../../services/reportService'
import { getAdminAnalyticsSummary, getAdminSportsAnalytics } from '../../services/analyticsService'
import { getTournamentRankings } from '../../services/rankingService'
import { getTrainingSessions } from '../../services/trainingService'
import notificationService from '../../services/notificationService'
import styles from './AdminDashboard.module.css'

export default function AdminDashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [summary, setSummary] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [sportsAnalytics, setSportsAnalytics] = useState([])
  const [rankings, setRankings] = useState([])
  const [sessions, setSessions] = useState([])
  const [notifications, setNotifications] = useState([])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [sumRes, anaRes, sportRes, rankRes, sessRes, notifRes] = await Promise.allSettled([
        reportService.getAcademySummaryReport(),
        getAdminAnalyticsSummary(),
        getAdminSportsAnalytics(),
        getTournamentRankings(),
        getTrainingSessions({ limit: 4 }),
        notificationService.getNotifications({ limit: 4 }),
      ])

      if (sumRes.status === 'fulfilled') setSummary(sumRes.value)
      if (anaRes.status === 'fulfilled') setAnalytics(anaRes.value)
      if (sportRes.status === 'fulfilled' && sportRes.value?.sports) {
        setSportsAnalytics(sportRes.value.sports)
      }
      if (rankRes.status === 'fulfilled' && Array.isArray(rankRes.value)) {
        setRankings(rankRes.value.slice(0, 5))
      }
      if (sessRes.status === 'fulfilled' && Array.isArray(sessRes.value)) {
        setSessions(sessRes.value.slice(0, 4))
      }
      if (notifRes.status === 'fulfilled' && Array.isArray(notifRes.value)) {
        setNotifications(notifRes.value.slice(0, 4))
      }
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  return (
    <AppLayout title="Academy Control Center">
      <div className={styles.dashboard}>
        {/* Header Bar */}
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <h1>Academy Control Center</h1>
            <p>High-performance athlete monitoring, coaching operations & academy insights</p>
          </div>
          <div className={styles.actionRow}>
            <Link to="/admin/athletes" className={styles.primaryBtn}>
              <span>+</span> Register Athlete
            </Link>
            <Link to="/admin/training" className={styles.secondaryBtn}>
              <span>⏱️</span> Schedule Training
            </Link>
            <Link to="/admin/tournaments" className={styles.secondaryBtn}>
              <span>🏆</span> Tournaments
            </Link>
            <Link to="/admin/reports" className={styles.secondaryBtn}>
              <span>📑</span> Full Reports
            </Link>
          </div>
        </div>

        {error && (
          <div className={styles.errorBox}>
            <span>{error}</span>
            <button className={styles.retryBtn} onClick={loadData}>Retry</button>
          </div>
        )}

        {/* Top KPI Cards Grid */}
        {loading ? (
          <SkeletonLoader count={6} height="120px" />
        ) : (
          <div className={styles.kpiGrid}>
            <KpiCard
              title="Total Athletes"
              value={summary?.total_athletes ?? analytics?.total_athletes ?? 0}
              icon="🏃"
              trend={analytics?.improving_athletes_count ? `+${analytics.improving_athletes_count} improving` : null}
              trendDirection="up"
              variant="default"
            />
            <KpiCard
              title="Active Coaches"
              value={summary?.total_coaches ?? analytics?.total_coaches ?? 0}
              icon="🧑‍🏫"
              variant="accent"
            />
            <KpiCard
              title="Active Sports"
              value={summary?.total_sports ?? analytics?.total_active_sports ?? sportsAnalytics.length}
              icon="🏅"
              variant="default"
            />
            <KpiCard
              title="Academy Attendance"
              value={
                summary?.average_attendance_percentage != null
                  ? `${Math.round(summary.average_attendance_percentage)}%`
                  : analytics?.average_attendance != null
                  ? `${Math.round(analytics.average_attendance)}%`
                  : 'N/A'
              }
              icon="📋"
              trend={
                analytics?.athletes_below_attendance_threshold
                  ? `${analytics.athletes_below_attendance_threshold} need attention`
                  : null
              }
              trendDirection={analytics?.athletes_below_attendance_threshold ? 'down' : 'up'}
              variant={
                (summary?.average_attendance_percentage ?? 100) < 75 ? 'danger' : 'default'
              }
            />
            <KpiCard
              title="Avg Performance"
              value={
                summary?.average_performance_score != null
                  ? summary.average_performance_score.toFixed(1)
                  : analytics?.average_performance != null
                  ? analytics.average_performance.toFixed(1)
                  : 'N/A'
              }
              icon="🎯"
              trend={analytics?.total_assessments ? `${analytics.total_assessments} assessed` : null}
              trendDirection="up"
              variant="accent"
            />
            <KpiCard
              title="Tournaments & Medals"
              value={summary?.total_medals_awarded ?? 0}
              icon="🏆"
              trend={summary?.total_tournaments ? `${summary.total_tournaments} events` : null}
              trendDirection="up"
              variant="default"
            />
          </div>
        )}

        {/* 2-Column Content Section */}
        <div className={styles.twoColGrid}>
          {/* Left Column: Sports Disciplines Performance */}
          <div className={styles.sectionCard}>
            <div className={styles.sectionHeader}>
              <h2><span>🏅</span> Sport Disciplines & Performance</h2>
              <Link to="/admin/analytics" className={styles.viewAllLink}>
                View Analytics →
              </Link>
            </div>

            {loading ? (
              <SkeletonLoader count={3} height="60px" />
            ) : sportsAnalytics.length === 0 ? (
              <EmptyState
                icon="🏅"
                title="No sport analytics available"
                description="Sports and athlete assessments will show disciplinary performance here."
                actionText="Manage Sports"
                onAction={() => window.location.href = '/admin/sports'}
              />
            ) : (
              <div className={styles.sportList}>
                {sportsAnalytics.map((sp) => {
                  const perf = sp.average_performance != null ? Number(sp.average_performance) : 0
                  const att = sp.average_attendance != null ? Math.round(Number(sp.average_attendance)) : 0
                  return (
                    <div key={sp.sport_id} className={styles.sportRow}>
                      <div className={styles.sportMeta}>
                        <span className={styles.sportName}>{sp.sport_name}</span>
                        <div className={styles.sportStats}>
                          <span>{sp.athlete_count} athletes</span>
                          <span>Score: {perf ? perf.toFixed(1) : 'N/A'}</span>
                          <span>Att: {att ? `${att}%` : 'N/A'}</span>
                        </div>
                      </div>
                      <div className={styles.barContainer}>
                        <div
                          className={styles.barFill}
                          style={{ width: `${Math.min(100, Math.max(5, perf))}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Right Column: Top Podium Athletes */}
          <div className={styles.sectionCard}>
            <div className={styles.sectionHeader}>
              <h2><span>🥇</span> Top Academy Performers</h2>
              <Link to="/admin/rankings" className={styles.viewAllLink}>
                All Rankings →
              </Link>
            </div>

            {loading ? (
              <SkeletonLoader count={4} height="45px" />
            ) : rankings.length === 0 ? (
              <EmptyState
                icon="🥇"
                title="No rankings calculated"
                description="Complete tournament results and performance assessments to generate rankings."
              />
            ) : (
              <div className={styles.podiumList}>
                {rankings.map((item, idx) => {
                  const rankClass =
                    idx === 0
                      ? styles.rank1
                      : idx === 1
                      ? styles.rank2
                      : idx === 2
                      ? styles.rank3
                      : styles.rankOther
                  return (
                    <div key={item.athlete_id || idx} className={styles.podiumItem}>
                      <div className={`${styles.podiumRank} ${rankClass}`}>
                        {idx + 1}
                      </div>
                      <div className={styles.podiumInfo}>
                        <div className={styles.podiumName}>
                          {item.athlete_name || item.name || 'Athlete'}
                        </div>
                        <div className={styles.podiumSport}>
                          {item.sport_name || 'All Sports'}
                        </div>
                      </div>
                      <div className={styles.podiumPoints}>
                        {item.points != null ? `${item.points} pts` : item.score != null ? `${item.score}` : '★'}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Recent Training Sessions Section */}
        <div className={styles.sectionCard}>
          <div className={styles.sectionHeader}>
            <h2><span>⏱️</span> Recent & Upcoming Training Sessions</h2>
            <Link to="/admin/training" className={styles.viewAllLink}>
              Manage Sessions →
            </Link>
          </div>

          {loading ? (
            <SkeletonLoader count={3} height="120px" />
          ) : sessions.length === 0 ? (
            <EmptyState
              icon="⏱️"
              title="No training sessions scheduled"
              description="Schedule high-performance drills and tactical sessions for academy athletes."
              actionText="Schedule Session"
              onAction={() => window.location.href = '/admin/training'}
            />
          ) : (
            <div className={styles.sessionGrid}>
              {sessions.map((sess) => (
                <TrainingCard
                  key={sess.id || sess._id}
                  session={sess}
                  canManage={true}
                  onView={() => window.location.href = `/admin/training`}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
