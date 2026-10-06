import React from 'react'
import styles from './AthleteCard.module.css'

export default function AthleteCard({
  athlete,
  score,
  attendance,
  trend,
  onView,
  onAssess,
}) {
  const name = athlete?.full_name || athlete?.name || 'Athlete'
  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase()

  const sport = athlete?.sport_name || athlete?.sport || 'General'

  return (
    <div className={styles.card}>
      <div className={styles.top}>
        <div className={styles.avatar}>{initials}</div>
        <div className={styles.meta}>
          <h4 className={styles.name}>{name}</h4>
          <span className={styles.sport}>{sport}</span>
        </div>
        {athlete?.status && (
          <span
            className={`${styles.statusBadge} ${
              athlete.status === 'active' ? styles.active : styles.inactive
            }`}
          >
            {athlete.status}
          </span>
        )}
      </div>

      <div className={styles.stats}>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Score</span>
          <span className={styles.statValue}>
            {score !== undefined && score !== null ? `${score}/100` : '—'}
          </span>
        </div>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Attendance</span>
          <span
            className={`${styles.statValue} ${
              attendance !== undefined && attendance !== null && attendance < 75
                ? styles.warn
                : ''
            }`}
          >
            {attendance !== undefined && attendance !== null ? `${attendance}%` : '—'}
          </span>
        </div>
        {trend && (
          <div className={styles.statItem}>
            <span className={styles.statLabel}>Trend</span>
            <span
              className={`${styles.trendPill} ${
                trend === 'Improving'
                  ? styles.trendUp
                  : trend === 'Declining'
                  ? styles.trendDown
                  : styles.trendNeutral
              }`}
            >
              {trend}
            </span>
          </div>
        )}
      </div>

      {(onView || onAssess) && (
        <div className={styles.actions}>
          {onView && (
            <button
              type="button"
              className={styles.btnSecondary}
              onClick={() => onView(athlete)}
            >
              View Profile
            </button>
          )}
          {onAssess && (
            <button
              type="button"
              className={styles.btnPrimary}
              onClick={() => onAssess(athlete)}
            >
              Record Assessment
            </button>
          )}
        </div>
      )}
    </div>
  )
}
