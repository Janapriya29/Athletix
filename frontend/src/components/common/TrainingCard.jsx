import React from 'react'
import styles from './TrainingCard.module.css'

export default function TrainingCard({ session, onSelect, onAttendance }) {
  const dateStr = session?.session_date
    ? new Date(session.session_date).toLocaleDateString(undefined, {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      })
    : 'Date TBD'

  const timeStr =
    session?.start_time && session?.end_time
      ? `${session.start_time} - ${session.end_time}`
      : session?.start_time || ''

  const status = session?.status || 'scheduled'
  const attendeesCount = session?.athlete_ids?.length || 0

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.titleArea}>
          <h4 className={styles.title}>{session?.title || 'Training Session'}</h4>
          <span className={styles.sport}>{session?.sport_name || 'Academy Sport'}</span>
        </div>
        <span className={`${styles.badge} ${styles[status] || styles.scheduled}`}>
          {status}
        </span>
      </div>

      <div className={styles.details}>
        <div className={styles.detailRow}>
          <span className={styles.icon}>📅</span>
          <span>{dateStr}</span>
          {timeStr && <span className={styles.timePill}>{timeStr}</span>}
        </div>
        {session?.location && (
          <div className={styles.detailRow}>
            <span className={styles.icon}>📍</span>
            <span>{session.location}</span>
          </div>
        )}
        {session?.coach_name && (
          <div className={styles.detailRow}>
            <span className={styles.icon}>🧢</span>
            <span>Coach: {session.coach_name}</span>
          </div>
        )}
      </div>

      <div className={styles.footer}>
        <span className={styles.participants}>
          👥 <strong>{attendeesCount}</strong> Athletes
        </span>
        <div className={styles.actions}>
          {onAttendance && status !== 'cancelled' && (
            <button
              type="button"
              className={styles.btnAction}
              onClick={() => onAttendance(session)}
            >
              Attendance
            </button>
          )}
          {onSelect && (
            <button
              type="button"
              className={styles.btnSecondary}
              onClick={() => onSelect(session)}
            >
              Details
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
