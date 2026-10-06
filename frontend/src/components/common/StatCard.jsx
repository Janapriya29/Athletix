import React from 'react'
import styles from './StatCard.module.css'

/**
 * A simple metric card used in dashboards.
 */
export default function StatCard({ label, value, sub, accent = false }) {
  return (
    <div className={`${styles.card} ${accent ? styles.accent : ''}`}>
      <span className={styles.value}>{value ?? '—'}</span>
      <span className={styles.label}>{label}</span>
      {sub && <span className={styles.sub}>{sub}</span>}
    </div>
  )
}
