import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import { getSports } from '../../services/sportsService'

export default function CoachSportsPage() {
  const [sports, setSports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        const data = await getSports()
        setSports(data)
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load sports.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <AppLayout title="Academy Sports Directory">
      <div className={styles.container}>
        {error && <ErrorMessage message={error} />}

        {loading ? (
          <LoadingSpinner />
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: 20,
            }}
          >
            {sports.map((sport) => (
              <div
                key={sport.id}
                style={{
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius)',
                  padding: 'var(--space-5)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: 'var(--text-lg)', color: 'var(--color-text)' }}>
                    {sport.name}
                  </h3>
                  <span className={`${styles.badge} ${styles.badgeActive}`}>Active</span>
                </div>
                <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)', flex: 1 }}>
                  {sport.description || 'Standard academy training program and curriculum.'}
                </p>

                <div>
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                    Tracked Metrics ({sport.categories?.length || 0})
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
                    {sport.categories?.map((cat) => (
                      <span
                        key={cat.id}
                        style={{
                          background: 'var(--color-surface-2)',
                          padding: '2px 8px',
                          borderRadius: 4,
                          fontSize: '0.75rem',
                          color: 'var(--color-text)',
                        }}
                      >
                        {cat.name}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
