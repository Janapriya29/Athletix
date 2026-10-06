import React from 'react'
import styles from './EmptyState.module.css'

export default function EmptyState({
  icon = '📋',
  title = 'No items found',
  description = 'There are no records to display at this time.',
  actionLabel,
  onAction,
}) {
  return (
    <div className={styles.wrapper}>
      <div className={styles.icon}>{icon}</div>
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.desc}>{description}</p>
      {actionLabel && onAction && (
        <button type="button" className={styles.btn} onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  )
}
