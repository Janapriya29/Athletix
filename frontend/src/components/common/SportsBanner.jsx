import React, { useState } from 'react'
import styles from './SportsBanner.module.css'

/**
 * Reusable SportsBanner Component
 * Renders an attractive sports hero or dashboard banner with responsive image,
 * high-contrast accessible text overlay, and optional action buttons/metrics.
 */
export default function SportsBanner({
  image = '/images/hero_sports_collage.jpg',
  alt = 'Athletix Sports Academy',
  badge,
  title,
  subtitle,
  actions,
  metrics,
  minHeight,
  className = '',
}) {
  const [imgLoaded, setImgLoaded] = useState(false)
  const [imgError, setImgError] = useState(false)

  return (
    <div
      className={`${styles.banner} ${className}`}
      style={minHeight ? { minHeight } : undefined}
    >
      {/* Background Image with Fallback */}
      {!imgError && (
        <img
          src={image}
          alt={alt}
          className={`${styles.bgImage} ${imgLoaded ? styles.loaded : ''}`}
          onLoad={() => setImgLoaded(true)}
          onError={() => setImgError(true)}
          loading="eager"
        />
      )}

      {/* Dynamic Gradient Overlay */}
      <div className={styles.overlay} />

      {/* Content Container */}
      <div className={styles.content}>
        <div className={styles.textColumn}>
          {badge && (
            <div className={styles.badge}>
              <span className={styles.badgeDot} />
              <span>{badge}</span>
            </div>
          )}

          {title && <h1 className={styles.title}>{title}</h1>}
          {subtitle && <p className={styles.subtitle}>{subtitle}</p>}

          {/* Metrics bar if provided */}
          {metrics && metrics.length > 0 && (
            <div className={styles.metricsRow}>
              {metrics.map((m, idx) => (
                <div key={idx} className={styles.metricItem}>
                  {m.icon && <span className={styles.metricIcon}>{m.icon}</span>}
                  <div>
                    <div className={styles.metricValue}>{m.value}</div>
                    <div className={styles.metricLabel}>{m.label}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Action Controls */}
        {actions && <div className={styles.actionsColumn}>{actions}</div>}
      </div>
    </div>
  )
}
