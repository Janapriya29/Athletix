import React from 'react'
import styles from './ErrorMessage.module.css'

export default function ErrorMessage({ message, onRetry }) {
  return (
    <div className={styles.container} role="alert">
      <span className={styles.icon}>⚠</span>
      <p className={styles.message}>{message || 'Something went wrong.'}</p>
      {onRetry && (
        <button className={styles.retryBtn} onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  )
}
