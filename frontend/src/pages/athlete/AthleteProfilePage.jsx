import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import {
  getMyAthleteProfile,
  getMyCoach,
  updateAthlete,
} from '../../services/athletesService'
import { getSport } from '../../services/sportsService'

export default function AthleteProfilePage() {
  const [activeTab, setActiveTab] = useState('profile') // 'profile' | 'coach' | 'sports'
  const [profile, setProfile] = useState(null)
  const [coach, setCoach] = useState(null)
  const [sportDetails, setSportDetails] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [feedback, setFeedback] = useState(null)

  // Editable fields for athlete
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [emergencyContact, setEmergencyContact] = useState('')
  const [saving, setSaving] = useState(false)

  const loadAthleteData = async () => {
    try {
      setLoading(true)
      setError(null)
      const ath = await getMyAthleteProfile()
      setProfile(ath)
      setPhone(ath.phone || '')
      setAddress(ath.address || '')
      setEmergencyContact(ath.emergency_contact || '')

      // Try loading assigned coach
      try {
        const coachData = await getMyCoach()
        setCoach(coachData)
      } catch (cErr) {
        // Coach might not be assigned yet
        setCoach(null)
      }

      // Try loading primary sport
      if (ath.sport_id) {
        try {
          const sData = await getSport(ath.sport_id)
          setSportDetails(sData)
        } catch (sErr) {
          setSportDetails(null)
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load athlete profile.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAthleteData()
  }, [])

  const handleUpdateContact = async (e) => {
    e.preventDefault()
    if (!profile) return
    try {
      setSaving(true)
      setError(null)
      await updateAthlete(profile.id, {
        phone,
        address,
        emergency_contact: emergencyContact,
      })
      setFeedback('Contact information updated successfully.')
      loadAthleteData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update contact info.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <AppLayout title="Athlete Center">
      <div className={styles.container} style={{ maxWidth: 840 }}>
        {feedback && (
          <div className={styles.alertSuccess} role="alert">
            {feedback}
            <button
              style={{ float: 'right', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
              onClick={() => setFeedback(null)}
            >
              ×
            </button>
          </div>
        )}
        {error && <ErrorMessage message={error} />}

        {/* Tab Navigation */}
        <div
          style={{
            display: 'flex',
            gap: 8,
            borderBottom: '1px solid var(--color-border)',
            paddingBottom: 8,
          }}
        >
          <button
            className={activeTab === 'profile' ? styles.primaryBtn : styles.secondaryBtn}
            onClick={() => setActiveTab('profile')}
          >
            👤 My Profile
          </button>
          <button
            className={activeTab === 'coach' ? styles.primaryBtn : styles.secondaryBtn}
            onClick={() => setActiveTab('coach')}
          >
            📋 My Coach
          </button>
          <button
            className={activeTab === 'sports' ? styles.primaryBtn : styles.secondaryBtn}
            onClick={() => setActiveTab('sports')}
          >
            ⚽ My Sports
          </button>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : profile ? (
          <div>
            {/* TAB 1: MY PROFILE */}
            {activeTab === 'profile' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                {/* Header card */}
                <div
                  style={{
                    backgroundColor: 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius)',
                    padding: 'var(--space-6)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 20,
                  }}
                >
                  <div
                    style={{
                      width: 72,
                      height: 72,
                      borderRadius: '50%',
                      backgroundColor: 'var(--color-surface-2)',
                      border: '3px solid var(--color-accent)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '2rem',
                    }}
                  >
                    🏅
                  </div>
                  <div>
                    <h2 style={{ fontSize: 'var(--text-xl)', color: 'var(--color-text)' }}>
                      {profile.full_name}
                    </h2>
                    <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)', marginTop: 2 }}>
                      {profile.email} • Primary Sport: <strong>{profile.sport_name || 'Unassigned'}</strong>
                    </div>
                    <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
                      <span className={`${styles.badge} ${styles.badgeActive}`}>
                        {profile.status}
                      </span>
                      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                        Coach: <strong>{profile.coach_name || 'Unassigned'}</strong>
                      </span>
                      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                        Joined:{' '}
                        <strong>
                          {profile.joining_date
                            ? new Date(profile.joining_date).toLocaleDateString()
                            : '—'}
                        </strong>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Read-only Academy Details */}
                <div
                  style={{
                    backgroundColor: 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius)',
                    padding: 'var(--space-5)',
                  }}
                >
                  <h3 style={{ fontSize: 'var(--text-md)', marginBottom: 12, color: 'var(--color-text)' }}>
                    Academy Information
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div>
                      <span className={styles.formLabel}>Gender</span>
                      <p style={{ textTransform: 'capitalize', color: 'var(--color-text)' }}>
                        {profile.gender || '—'}
                      </p>
                    </div>
                    <div>
                      <span className={styles.formLabel}>Date of Birth</span>
                      <p style={{ color: 'var(--color-text)' }}>
                        {profile.date_of_birth
                          ? new Date(profile.date_of_birth).toLocaleDateString()
                          : '—'}
                      </p>
                    </div>
                    <div>
                      <span className={styles.formLabel}>Sport Discipline</span>
                      <p style={{ color: 'var(--color-text)' }}>{profile.sport_name || '—'}</p>
                    </div>
                    <div>
                      <span className={styles.formLabel}>Assigned Coach</span>
                      <p style={{ color: 'var(--color-accent)' }}>{profile.coach_name || 'None'}</p>
                    </div>
                  </div>
                </div>

                {/* Editable Personal Contact Info */}
                <form
                  onSubmit={handleUpdateContact}
                  style={{
                    backgroundColor: 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius)',
                    padding: 'var(--space-6)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 16,
                  }}
                >
                  <h3 style={{ fontSize: 'var(--text-md)', color: 'var(--color-text)' }}>
                    Contact & Emergency Information
                  </h3>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Contact Phone</label>
                    <input
                      type="text"
                      className={styles.formInput}
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+91 98000 00000"
                    />
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Emergency Contact</label>
                    <input
                      type="text"
                      className={styles.formInput}
                      value={emergencyContact}
                      onChange={(e) => setEmergencyContact(e.target.value)}
                      placeholder="Parent/Guardian Name & Phone Number"
                    />
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Residential Address</label>
                    <input
                      type="text"
                      className={styles.formInput}
                      value={address}
                      onChange={(e) => setAddress(e.target.value)}
                      placeholder="Home Address, City, Zip"
                    />
                  </div>

                  <div>
                    <button type="submit" className={styles.primaryBtn} disabled={saving}>
                      {saving ? 'Saving...' : 'Update Contact Info'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* TAB 2: MY COACH */}
            {activeTab === 'coach' && (
              <div
                style={{
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius)',
                  padding: 'var(--space-6)',
                }}
              >
                {coach ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                      <div
                        style={{
                          width: 60,
                          height: 60,
                          borderRadius: '50%',
                          backgroundColor: 'var(--color-surface-2)',
                          border: '2px solid var(--color-accent)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '1.8rem',
                        }}
                      >
                        🧑‍🏫
                      </div>
                      <div>
                        <h2 style={{ fontSize: 'var(--text-lg)', color: 'var(--color-text)' }}>
                          {coach.full_name}
                        </h2>
                        <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)' }}>
                          {coach.email}
                        </div>
                      </div>
                    </div>

                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: 12,
                        background: 'var(--color-surface-2)',
                        padding: 16,
                        borderRadius: 'var(--radius)',
                      }}
                    >
                      <div>
                        <span className={styles.formLabel}>Specialization</span>
                        <p style={{ color: 'var(--color-text)', fontWeight: 600 }}>
                          {coach.specialization || 'Head Coach'}
                        </p>
                      </div>
                      <div>
                        <span className={styles.formLabel}>Direct Phone</span>
                        <p style={{ color: 'var(--color-text)' }}>{coach.phone || '—'}</p>
                      </div>
                      <div style={{ gridColumn: 'span 2' }}>
                        <span className={styles.formLabel}>Coach Bio</span>
                        <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)', marginTop: 4 }}>
                          {coach.bio || 'Experienced sports academy coach dedicated to athlete excellence.'}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className={styles.emptyState}>
                    <h3>No Coach Assigned</h3>
                    <p style={{ marginTop: 8 }}>
                      You have not been assigned to a specific coach yet. Please contact the academy administrator.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: MY SPORTS */}
            {activeTab === 'sports' && (
              <div
                style={{
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius)',
                  padding: 'var(--space-6)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16,
                }}
              >
                {sportDetails ? (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <h2 style={{ fontSize: 'var(--text-xl)', color: 'var(--color-text)' }}>
                        ⚽ {sportDetails.name}
                      </h2>
                      <span className={`${styles.badge} ${styles.badgeActive}`}>Primary Sport</span>
                    </div>

                    <p style={{ color: 'var(--color-text-muted)', marginTop: 8 }}>
                      {sportDetails.description || 'Core academy training discipline.'}
                    </p>

                    <div style={{ marginTop: 20 }}>
                      <h3 style={{ fontSize: 'var(--text-md)', color: 'var(--color-text)', marginBottom: 8 }}>
                        Performance Assessment Metrics
                      </h3>
                      <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginBottom: 12 }}>
                        Coaches evaluate your progress across these skill dimensions:
                      </p>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 10 }}>
                        {sportDetails.categories?.map((cat) => (
                          <div
                            key={cat.id}
                            style={{
                              background: 'var(--color-surface-2)',
                              border: '1px solid var(--color-border)',
                              borderRadius: 'var(--radius-sm)',
                              padding: '10px 14px',
                            }}
                          >
                            <strong style={{ color: 'var(--color-accent)', fontSize: 'var(--text-sm)' }}>
                              {cat.name}
                            </strong>
                            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginTop: 2 }}>
                              {cat.description || 'Scored 0–100'}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className={styles.emptyState}>
                    <h3>No Sport Assigned</h3>
                    <p style={{ marginTop: 8 }}>
                      You currently have no primary sport assigned. Please consult academy staff.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : null}
      </div>
    </AppLayout>
  )
}
