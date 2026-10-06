import React from 'react'
import styles from './SportCard.module.css'

const SPORT_ICONS = {
  football: '⚽',
  soccer: '⚽',
  cricket: '🏏',
  badminton: '🏸',
  basketball: '🏀',
  athletics: '🏃',
  tennis: '🎾',
  swimming: '🏊',
}

export function getSportIcon(name = '') {
  const key = name.toLowerCase().trim()
  return SPORT_ICONS[key] || '🏅'
}

export default function SportCard({ sport, athleteCount, coachCount, onClick }) {
  const icon = getSportIcon(sport?.name)
  const category = sport?.category || 'Academy Sport'
  const isActive = sport?.is_active ?? true

  return (
    <div
      className={`${styles.card} ${onClick ? styles.clickable : ''}`}
      onClick={onClick}
    >
      <div className={styles.top}>
        <div className={styles.iconWrapper}>{icon}</div>
        <div className={styles.headerInfo}>
          <h3 className={styles.name}>{sport?.name || 'Sport'}</h3>
          <span className={styles.category}>{category}</span>
        </div>
        <span
          className={`${styles.badge} ${isActive ? styles.active : styles.inactive}`}
        >
          {isActive ? 'Active' : 'Inactive'}
        </span>
      </div>

      {sport?.description && (
        <p className={styles.description}>{sport.description}</p>
      )}

      {(athleteCount !== undefined || coachCount !== undefined) && (
        <div className={styles.footer}>
          {athleteCount !== undefined && (
            <span className={styles.stat}>
              <strong>{athleteCount}</strong> Athletes
            </span>
          )}
          {coachCount !== undefined && (
            <span className={styles.stat}>
              <strong>{coachCount}</strong> Coaches
            </span>
          )}
        </div>
      )}
    </div>
  )
}
