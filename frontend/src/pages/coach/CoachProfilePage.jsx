import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import { getMyCoachProfile, updateCoach } from '../../services/coachesService'

export default function CoachProfilePage() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [feedback, setFeedback] = useState(null)

  // Edit fields
  const [phone, setPhone] = useState('')
  const [bio, setBio] = useState('')
  const [saving, setSaving] = useState(false)

  const fetchProfile = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getMyCoachProfile()
      setProfile(data)
      setPhone(data.phone || '')
      setBio(data.bio || '')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load coach profile.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProfile()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!profile) return
    try {
      setSaving(true)
      setError(null)
      await updateCoach(profile.id, { phone, bio })
      setFeedback('Profile updated successfully.')
      fetchProfile()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <AppLayout title="My Coach Profile">
      <div className={styles.container} style={{ maxWidth: 800 }}>
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

        {loading ? (
          <LoadingSpinner />
        ) : profile ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* Header Card */}
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
                📋
              </div>
              <div style={{ flex: 1 }}>
                <h2 style={{ fontSize: 'var(--text-xl)', color: 'var(--color-text)' }}>
                  {profile.full_name}
                </h2>
                <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)', marginTop: 2 }}>
                  {profile.email} • {profile.specialization || 'Academy Coach'}
                </div>
                <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span className={`${styles.badge} ${styles.badgeActive}`}>
                    {profile.status}
                  </span>
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                    Experience: <strong>{profile.experience_years} yrs</strong>
                  </span>
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                    Assigned Athletes: <strong>{profile.athlete_count}</strong>
                  </span>
                </div>
              </div>
            </div>

            {/* Sports Coached */}
            <div
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius)',
                padding: 'var(--space-6)',
              }}
            >
              <h3 style={{ fontSize: 'var(--text-md)', marginBottom: 12, color: 'var(--color-text)' }}>
                Assigned Sports
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {profile.sports?.length > 0 ? (
                  profile.sports.map((s) => (
                    <span
                      key={s.id}
                      style={{
                        backgroundColor: 'var(--color-surface-2)',
                        border: '1px solid var(--color-border)',
                        color: 'var(--color-accent)',
                        padding: '6px 14px',
                        borderRadius: 'var(--radius-sm)',
                        fontWeight: 600,
                        fontSize: 'var(--text-sm)',
                      }}
                    >
                      ⚽ {s.name}
                    </span>
                  ))
                ) : (
                  <p style={{ color: 'var(--color-text-muted)' }}>No sports currently assigned.</p>
                )}
              </div>
            </div>

            {/* Editable Profile Form */}
            <form
              onSubmit={handleSubmit}
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
                Contact & Background
              </h3>

              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Phone Number</label>
                <input
                  type="text"
                  className={styles.formInput}
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+1 555-0100"
                />
              </div>

              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Bio & Coaching Experience</label>
                <textarea
                  rows="4"
                  className={styles.formTextarea}
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  placeholder="Share details about your certifications, specialties, and coaching philosophy..."
                />
              </div>

              <div>
                <button type="submit" className={styles.primaryBtn} disabled={saving}>
                  {saving ? 'Saving...' : 'Save Profile Changes'}
                </button>
              </div>
            </form>
          </div>
        ) : null}
      </div>
    </AppLayout>
  )
}
