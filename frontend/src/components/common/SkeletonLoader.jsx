import React from 'react'
import styles from './SkeletonLoader.module.css'

export default function SkeletonLoader({
  count = 3,
  height = '48px',
  width = '100%',
  className = '',
}) {
  return (
    <div className={`${styles.container} ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={styles.skeleton}
          style={{ height, width }}
        />
      ))}
    </div>
  )
}
