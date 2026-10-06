import React from 'react'
import styles from './LoadingSpinner.module.css'

export default function LoadingSpinner({ message = 'Loading…' }) {
  return (
    <div className={styles.container} role="status" aria-live="polite">
      <div className={styles.spinner} aria-hidden="true" />
      <span className={styles.message}>{message}</span>
    </div>
  )
}
