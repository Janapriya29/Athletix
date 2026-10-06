import React from 'react'
import styles from './PagePlaceholder.module.css'

/**
 * Temporary placeholder shown for pages not yet implemented.
 * Replaced with real content in subsequent phases.
 */
export default function PagePlaceholder({ title }) {
  return (
    <div className={styles.container}>
      <div className={styles.badge}>Coming in next phase</div>
      <h2 className={styles.title}>{title}</h2>
      <p className={styles.note}>This page will be implemented in its designated phase.</p>
    </div>
  )
}
