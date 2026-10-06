import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import {
  assignAthletesToCoach,
  createCoach,
  getCoaches,
  removeAthleteFromCoach,
  setCoachStatus,
  updateCoach,
} from '../../services/coachesService'
import { getSports } from '../../services/sportsService'
import { getAthletes } from '../../services/athletesService'

export default function CoachesPage() {
  const [coaches, setCoaches] = useState([])
  const [sports, setSports] = useState([])
  const [allAthletes, setAllAthletes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [feedback, setFeedback] = useState(null)

  // Filters
  const [search, setSearch] = useState('')
  const [sportFilter, setSportFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  // Create/Edit Modal
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingCoach, setEditingCoach] = useState(null)
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    phone: '',
    specialization: '',
    experience_years: 0,
    sport_ids: [],
    bio: '',
    status: 'active',
  })
  const [modalError, setModalError] = useState(null)
  const [saving, setSaving] = useState(false)

  // Assign Athletes Modal
  const [assignModalCoach, setAssignModalCoach] = useState(null)
  const [selectedAthleteIds, setSelectedAthleteIds] = useState([])
  const [assigning, setAssigning] = useState(false)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {}
      if (search.trim()) params.search = search.trim()
      if (sportFilter !== 'all') params.sport_id = sportFilter
      if (statusFilter !== 'all') params.status = statusFilter

      const [coachData, sportData, athleteData] = await Promise.all([
        getCoaches(params),
        getSports(),
        getAthletes(),
      ])
      setCoaches(coachData)
      setSports(sportData)
      setAllAthletes(athleteData)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load coaches.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [sportFilter, statusFilter])

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    fetchData()
  }

  const openCreateModal = () => {
    setEditingCoach(null)
    setFormData({
      full_name: '',
      email: '',
      password: '',
      phone: '',
      specialization: '',
      experience_years: 0,
      sport_ids: [],
      bio: '',
      status: 'active',
    })
    setModalError(null)
    setIsModalOpen(true)
  }

  const openEditModal = (coach) => {
    setEditingCoach(coach)
    setFormData({
      full_name: coach.full_name,
      email: coach.email,
      password: '',
      phone: coach.phone || '',
      specialization: coach.specialization || '',
      experience_years: coach.experience_years || 0,
      sport_ids: coach.sport_ids || [],
      bio: coach.bio || '',
      status: coach.status,
    })
    setModalError(null)
    setIsModalOpen(true)
  }

  const handleSportCheckbox = (sportId) => {
    const current = [...formData.sport_ids]
    const idx = current.indexOf(sportId)
    if (idx > -1) {
      current.splice(idx, 1)
    } else {
      current.push(sportId)
    }
    setFormData({ ...formData, sport_ids: current })
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (!formData.full_name.trim()) {
      setModalError('Coach name is required.')
      return
    }

    try {
      setSaving(true)
      setModalError(null)
      if (editingCoach) {
        await updateCoach(editingCoach.id, {
          full_name: formData.full_name,
          phone: formData.phone,
          specialization: formData.specialization,
          experience_years: Number(formData.experience_years),
          sport_ids: formData.sport_ids,
          bio: formData.bio,
          status: formData.status,
        })
        setFeedback(`Coach "${formData.full_name}" updated successfully.`)
      } else {
        if (!formData.email.trim()) {
          setModalError('Email is required.')
          setSaving(false)
          return
        }
        await createCoach({
          ...formData,
          experience_years: Number(formData.experience_years),
        })
        setFeedback(`Coach "${formData.full_name}" created successfully.`)
      }
      setIsModalOpen(false)
      fetchData()
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed to save coach.')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleStatus = async (coach) => {
    const nextStatus = coach.status === 'active' ? 'inactive' : 'active'
    try {
      await setCoachStatus(coach.id, nextStatus)
      setFeedback(`Coach "${coach.full_name}" status set to ${nextStatus}.`)
      fetchData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update coach status.')
    }
  }

  const openAssignModal = (coach) => {
    setAssignModalCoach(coach)
    // Find athletes currently assigned to this coach
    const assigned = allAthletes
      .filter((a) => a.coach_id === coach.id)
      .map((a) => a.id)
    setSelectedAthleteIds(assigned)
  }

  const handleSaveAssignments = async () => {
    if (!assignModalCoach) return
    try {
      setAssigning(true)
      await assignAthletesToCoach(assignModalCoach.id, selectedAthleteIds)
      setFeedback(`Athletes assigned to Coach "${assignModalCoach.full_name}".`)
      setAssignModalCoach(null)
      fetchData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to assign athletes.')
    } finally {
      setAssigning(false)
    }
  }

  return (
    <AppLayout title="Coach Management">
      <div className={styles.container}>
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

        <div className={styles.headerBar}>
          <form className={styles.controls} onSubmit={handleSearchSubmit}>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="Search by name or specialization..."
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
            <select
              className={styles.selectInput}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
            <button type="submit" className={styles.secondaryBtn}>Search</button>
          </form>

          <button className={styles.primaryBtn} onClick={openCreateModal}>
            + Add Coach
          </button>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Coach</th>
                  <th>Specialization</th>
                  <th>Sports</th>
                  <th>Athletes</th>
                  <th>Phone</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {coaches.length === 0 ? (
                  <tr>
                    <td colSpan="7" className={styles.emptyState}>
                      No coaches found matching criteria.
                    </td>
                  </tr>
                ) : (
                  coaches.map((c) => (
                    <tr key={c.id}>
                      <td>
                        <strong>{c.full_name}</strong>
                        <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-xs)' }}>
                          {c.email}
                        </div>
                      </td>
                      <td>{c.specialization || 'General Coach'}</td>
                      <td>
                        {c.sports?.length > 0
                          ? c.sports.map((s) => (
                              <span key={s.id} style={{ display: 'inline-block', marginRight: 4, background: 'var(--color-surface-2)', padding: '2px 6px', borderRadius: 4, fontSize: '0.75rem' }}>
                                {s.name}
                              </span>
                            ))
                          : '—'}
                      </td>
                      <td>
                        <strong>{c.athlete_count ?? 0}</strong>
                      </td>
                      <td style={{ color: 'var(--color-text-muted)' }}>{c.phone || '—'}</td>
                      <td>
                        <span
                          className={`${styles.badge} ${
                            c.status === 'active' ? styles.badgeActive : styles.badgeInactive
                          }`}
                        >
                          {c.status}
                        </span>
                      </td>
                      <td>
                        <div className={styles.actionsCell}>
                          <button className={styles.actionBtn} onClick={() => openEditModal(c)}>
                            Edit
                          </button>
                          <button className={styles.actionBtn} onClick={() => openAssignModal(c)}>
                            Assign Athletes
                          </button>
                          <button className={styles.actionBtn} onClick={() => handleToggleStatus(c)}>
                            {c.status === 'active' ? 'Deactivate' : 'Activate'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Modal: Create / Edit Coach */}
        {isModalOpen && (
          <div className={styles.modalOverlay}>
            <div className={styles.modal} style={{ maxWidth: 600 }}>
              <div className={styles.modalHeader}>
                <h3 className={styles.modalTitle}>
                  {editingCoach ? 'Edit Coach Profile' : 'Add New Coach'}
                </h3>
                <button className={styles.closeBtn} onClick={() => setIsModalOpen(false)}>
                  ×
                </button>
              </div>

              <form onSubmit={handleSave}>
                <div className={styles.modalBody}>
                  {modalError && <div className={styles.alertError}>{modalError}</div>}

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Full Name *</label>
                    <input
                      type="text"
                      className={styles.formInput}
                      value={formData.full_name}
                      onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                      placeholder="e.g. Sarah Mitchell"
                      required
                    />
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Email *</label>
                    <input
                      type="email"
                      className={styles.formInput}
                      value={formData.email}
                      disabled={!!editingCoach}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="coach@athletix.dev"
                      required
                    />
                  </div>

                  {!editingCoach && (
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Password (Default: Coach@123)</label>
                      <input
                        type="password"
                        className={styles.formInput}
                        value={formData.password}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        placeholder="••••••••"
                      />
                    </div>
                  )}

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Specialization</label>
                      <input
                        type="text"
                        className={styles.formInput}
                        value={formData.specialization}
                        onChange={(e) =>
                          setFormData({ ...formData, specialization: e.target.value })
                        }
                        placeholder="e.g. Tactical Training"
                      />
                    </div>

                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Years of Experience</label>
                      <input
                        type="number"
                        min="0"
                        max="70"
                        className={styles.formInput}
                        value={formData.experience_years}
                        onChange={(e) =>
                          setFormData({ ...formData, experience_years: e.target.value })
                        }
                      />
                    </div>
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Phone</label>
                    <input
                      type="text"
                      className={styles.formInput}
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder="+1 555-0100"
                    />
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Assigned Sports</label>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 4 }}>
                      {sports.map((s) => (
                        <label
                          key={s.id}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 6,
                            background: 'var(--color-surface-2)',
                            padding: '4px 10px',
                            borderRadius: 4,
                            cursor: 'pointer',
                            fontSize: 'var(--text-sm)',
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={formData.sport_ids.includes(s.id)}
                            onChange={() => handleSportCheckbox(s.id)}
                          />
                          {s.name}
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Bio</label>
                    <textarea
                      rows="2"
                      className={styles.formTextarea}
                      value={formData.bio}
                      onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                      placeholder="Qualifications, certifications, coaching history..."
                    />
                  </div>
                </div>

                <div className={styles.modalFooter}>
                  <button
                    type="button"
                    className={styles.secondaryBtn}
                    onClick={() => setIsModalOpen(false)}
                  >
                    Cancel
                  </button>
                  <button type="submit" className={styles.primaryBtn} disabled={saving}>
                    {saving ? 'Saving...' : editingCoach ? 'Save Changes' : 'Create Coach'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Assign Athletes */}
        {assignModalCoach && (
          <div className={styles.modalOverlay}>
            <div className={styles.modal} style={{ maxWidth: 520 }}>
              <div className={styles.modalHeader}>
                <h3 className={styles.modalTitle}>
                  Assign Athletes to {assignModalCoach.full_name}
                </h3>
                <button className={styles.closeBtn} onClick={() => setAssignModalCoach(null)}>
                  ×
                </button>
              </div>

              <div className={styles.modalBody}>
                <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
                  Select the athletes who will be coached by {assignModalCoach.full_name}:
                </p>

                <div style={{ maxHeight: 300, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {allAthletes.map((ath) => (
                    <label
                      key={ath.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 12px',
                        backgroundColor: 'var(--color-surface-2)',
                        borderRadius: 4,
                        cursor: 'pointer',
                      }}
                    >
                      <div>
                        <strong>{ath.full_name}</strong>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                          {ath.sport_name || 'No sport'} • {ath.email}
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        checked={selectedAthleteIds.includes(ath.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedAthleteIds([...selectedAthleteIds, ath.id])
                          } else {
                            setSelectedAthleteIds(selectedAthleteIds.filter((id) => id !== ath.id))
                          }
                        }}
                      />
                    </label>
                  ))}
                </div>
              </div>

              <div className={styles.modalFooter}>
                <button
                  type="button"
                  className={styles.secondaryBtn}
                  onClick={() => setAssignModalCoach(null)}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className={styles.primaryBtn}
                  disabled={assigning}
                  onClick={handleSaveAssignments}
                >
                  {assigning ? 'Saving...' : 'Save Assignments'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
