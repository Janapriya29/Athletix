import React from 'react'
import styles from './KpiCard.module.css'

export default function KpiCard({
  icon,
  label,
  value,
  sub,
  trend,
  trendValue,
  variant = 'default',
  onClick,
}) {
  return (
    <div
      className={`${styles.card} ${styles[variant] || ''} ${onClick ? styles.clickable : ''}`}
      onClick={onClick}
    >
      <div className={styles.header}>
        <span className={styles.label}>{label}</span>
        {icon && <span className={styles.icon}>{icon}</span>}
      </div>
      <div className={styles.body}>
        <span className={styles.value}>{value ?? '—'}</span>
        {trendValue && (
          <span
            className={`${styles.trend} ${
              trend === 'up'
                ? styles.trendUp
                : trend === 'down'
                ? styles.trendDown
                : styles.trendNeutral
            }`}
          >
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '•'} {trendValue}
          </span>
        )}
      </div>
      {sub && <p className={styles.sub}>{sub}</p>}
    </div>
  )
}
