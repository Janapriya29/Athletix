import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import { getAthletes } from '../../services/athletesService'
import { getSports } from '../../services/sportsService'

export default function CoachAthletesPage() {
  const [athletes, setAthletes] = useState([])
  const [sports, setSports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filters
  const [search, setSearch] = useState('')
  const [sportFilter, setSportFilter] = useState('all')

  // Selected athlete for details modal
  const [selectedAthlete, setSelectedAthlete] = useState(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {}
      if (search.trim()) params.search = search.trim()
      if (sportFilter !== 'all') params.sport_id = sportFilter

      const [athData, sportData] = await Promise.all([
        getAthletes(params),
        getSports(),
      ])
      setAthletes(athData)
      setSports(sportData)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load assigned athletes.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [sportFilter])

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    fetchData()
  }

  return (
    <AppLayout title="My Assigned Athletes">
      <div className={styles.container}>
        {error && <ErrorMessage message={error} />}

        <div className={styles.headerBar}>
          <form className={styles.controls} onSubmit={handleSearchSubmit}>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="Search your athletes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              className={styles.selectInput}
              value={sportFilter}
              onChange={(e) => setSportFilter(e.target.value)}
            >
              <option value="all">All Sports</option>
              {sports.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            <button type="submit" className={styles.secondaryBtn}>Search</button>
          </form>

          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
            Total Athletes: <strong>{athletes.length}</strong>
          </span>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Athlete Name</th>
                  <th>Sport</th>
                  <th>Contact Info</th>
                  <th>Gender / DOB</th>
                  <th>Emergency Contact</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {athletes.length === 0 ? (
                  <tr>
                    <td colSpan="7" className={styles.emptyState}>
                      No athletes currently assigned to you.
                    </td>
                  </tr>
                ) : (
                  athletes.map((ath) => (
                    <tr key={ath.id}>
                      <td>
                        <strong>{ath.full_name}</strong>
                      </td>
                      <td>
                        <span style={{ fontWeight: 600 }}>{ath.sport_name || '—'}</span>
                      </td>
                      <td style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-xs)' }}>
                        {ath.email}
                        {ath.phone && <div>{ath.phone}</div>}
                      </td>
                      <td style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                        <span style={{ textTransform: 'capitalize' }}>{ath.gender || '—'}</span>
                        {ath.date_of_birth && ` (${new Date(ath.date_of_birth).toLocaleDateString()})`}
                      </td>
                      <td style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                        {ath.emergency_contact || '—'}
                      </td>
                      <td>
                        <span
                          className={`${styles.badge} ${
                            ath.status === 'active' ? styles.badgeActive : styles.badgeInactive
                          }`}
                        >
                          {ath.status}
                        </span>
                      </td>
                      <td>
                        <button
                          className={styles.actionBtn}
                          onClick={() => setSelectedAthlete(ath)}
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Modal: Athlete Details */}
        {selectedAthlete && (
          <div className={styles.modalOverlay}>
            <div className={styles.modal} style={{ maxWidth: 540 }}>
              <div className={styles.modalHeader}>
                <h3 className={styles.modalTitle}>Athlete Profile</h3>
                <button className={styles.closeBtn} onClick={() => setSelectedAthlete(null)}>
                  ×
                </button>
              </div>

              <div className={styles.modalBody}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div
                    style={{
                      width: 56,
                      height: 56,
                      borderRadius: '50%',
                      backgroundColor: 'var(--color-surface-2)',
                      border: '2px solid var(--color-accent)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1.5rem',
                    }}
                  >
                    🏃
                  </div>
                  <div>
                    <h2 style={{ fontSize: 'var(--text-xl)', color: 'var(--color-text)' }}>
                      {selectedAthlete.full_name}
                    </h2>
                    <span
                      className={`${styles.badge} ${
                        selectedAthlete.status === 'active'
                          ? styles.badgeActive
                          : styles.badgeInactive
                      }`}
                    >
                      {selectedAthlete.status}
                    </span>
                  </div>
                </div>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: 12,
                    marginTop: 8,
                    background: 'var(--color-surface-2)',
                    padding: 16,
                    borderRadius: 'var(--radius)',
                  }}
                >
                  <div>
                    <span className={styles.formLabel}>Sport</span>
                    <p style={{ fontWeight: 600, color: 'var(--color-text)' }}>
                      {selectedAthlete.sport_name || 'Unassigned'}
                    </p>
                  </div>
                  <div>
                    <span className={styles.formLabel}>Gender</span>
                    <p style={{ textTransform: 'capitalize', color: 'var(--color-text)' }}>
                      {selectedAthlete.gender || '—'}
                    </p>
                  </div>
                  <div>
                    <span className={styles.formLabel}>Email</span>
                    <p style={{ color: 'var(--color-text)' }}>{selectedAthlete.email}</p>
                  </div>
                  <div>
                    <span className={styles.formLabel}>Phone</span>
                    <p style={{ color: 'var(--color-text)' }}>{selectedAthlete.phone || '—'}</p>
                  </div>
                  <div>
                    <span className={styles.formLabel}>Date of Birth</span>
                    <p style={{ color: 'var(--color-text)' }}>
                      {selectedAthlete.date_of_birth
                        ? new Date(selectedAthlete.date_of_birth).toLocaleDateString()
                        : '—'}
                    </p>
                  </div>
                  <div>
                    <span className={styles.formLabel}>Enrolled Date</span>
                    <p style={{ color: 'var(--color-text)' }}>
                      {selectedAthlete.joining_date
                        ? new Date(selectedAthlete.joining_date).toLocaleDateString()
                        : '—'}
                    </p>
                  </div>
                  <div style={{ gridColumn: 'span 2' }}>
                    <span className={styles.formLabel}>Emergency Contact</span>
                    <p style={{ color: 'var(--color-text)' }}>
                      {selectedAthlete.emergency_contact || 'None specified'}
                    </p>
                  </div>
                  <div style={{ gridColumn: 'span 2' }}>
                    <span className={styles.formLabel}>Residential Address</span>
                    <p style={{ color: 'var(--color-text)' }}>
                      {selectedAthlete.address || 'None specified'}
                    </p>
                  </div>
                </div>
              </div>

              <div className={styles.modalFooter}>
                <button
                  className={styles.secondaryBtn}
                  onClick={() => setSelectedAthlete(null)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
