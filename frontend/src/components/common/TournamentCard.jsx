import React from 'react'
import styles from './TournamentCard.module.css'

export default function TournamentCard({ tournament, onRegister, onSelect }) {
  const startStr = tournament?.start_date
    ? new Date(tournament.start_date).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
      })
    : ''
  const endStr = tournament?.end_date
    ? new Date(tournament.end_date).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : ''
  const dateRange = startStr && endStr ? `${startStr} – ${endStr}` : startStr || 'Dates TBD'

  const status = tournament?.status || 'upcoming'
  const participantsCount = tournament?.participant_count ?? tournament?.participants?.length ?? 0
  const maxParts = tournament?.max_participants

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.titleArea}>
          <h4 className={styles.title}>{tournament?.name || 'Tournament'}</h4>
          <span className={styles.sport}>{tournament?.sport_name || 'All Sports'}</span>
        </div>
        <span className={`${styles.badge} ${styles[status] || styles.upcoming}`}>
          {status}
        </span>
      </div>

      <div className={styles.details}>
        <div className={styles.detailRow}>
          <span className={styles.icon}>🏆</span>
          <span>{dateRange}</span>
        </div>
        {tournament?.location && (
          <div className={styles.detailRow}>
            <span className={styles.icon}>📍</span>
            <span>{tournament.location}</span>
          </div>
        )}
      </div>

      <div className={styles.footer}>
        <span className={styles.participants}>
          👥 <strong>{participantsCount}</strong>
          {maxParts ? ` / ${maxParts}` : ''} Participants
        </span>
        <div className={styles.actions}>
          {onRegister && status === 'upcoming' && (
            <button
              type="button"
              className={styles.btnAction}
              onClick={() => onRegister(tournament)}
            >
              Register
            </button>
          )}
          {onSelect && (
            <button
              type="button"
              className={styles.btnSecondary}
              onClick={() => onSelect(tournament)}
            >
              Details
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
