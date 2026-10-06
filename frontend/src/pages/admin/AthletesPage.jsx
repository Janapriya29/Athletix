import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import {
  assignCoachToAthlete,
  createAthlete,
  getAthletes,
  setAthleteStatus,
  updateAthlete,
} from '../../services/athletesService'
import { getSports } from '../../services/sportsService'
import { getCoaches } from '../../services/coachesService'

export default function AthletesPage() {
  const [athletes, setAthletes] = useState([])
  const [sports, setSports] = useState([])
  const [coaches, setCoaches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [feedback, setFeedback] = useState(null)

  // Filters
  const [search, setSearch] = useState('')
  const [sportFilter, setSportFilter] = useState('all')
  const [coachFilter, setCoachFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingAthlete, setEditingAthlete] = useState(null)
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    phone: '',
    date_of_birth: '',
    gender: 'male',
    sport_id: '',
    coach_id: '',
    address: '',
    emergency_contact: '',
    status: 'active',
  })
  const [modalError, setModalError] = useState(null)
  const [saving, setSaving] = useState(false)

  // Quick coach assignment modal
  const [reassignModal, setReassignModal] = useState(null)
  const [newCoachId, setNewCoachId] = useState('')
  const [reassigning, setReassigning] = useState(false)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {}
      if (search.trim()) params.search = search.trim()
      if (sportFilter !== 'all') params.sport_id = sportFilter
      if (coachFilter !== 'all') params.coach_id = coachFilter
      if (statusFilter !== 'all') params.status = statusFilter

      const [athData, sportData, coachData] = await Promise.all([
        getAthletes(params),
        getSports(),
        getCoaches(),
      ])
      setAthletes(athData)
      setSports(sportData)
      setCoaches(coachData)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch athletes.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [sportFilter, coachFilter, statusFilter])

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    fetchData()
  }

  const openCreateModal = () => {
    setEditingAthlete(null)
    setFormData({
      full_name: '',
      email: '',
      password: '',
      phone: '',
      date_of_birth: '',
      gender: 'male',
      sport_id: sports.length > 0 ? sports[0].id : '',
      coach_id: '',
      address: '',
      emergency_contact: '',
      status: 'active',
    })
    setModalError(null)
    setIsModalOpen(true)
  }

  const openEditModal = (athlete) => {
    setEditingAthlete(athlete)
    setFormData({
      full_name: athlete.full_name,
      email: athlete.email,
      password: '',
      phone: athlete.phone || '',
      date_of_birth: athlete.date_of_birth ? athlete.date_of_birth.substring(0, 10) : '',
      gender: athlete.gender || 'male',
      sport_id: athlete.sport_id,
      coach_id: athlete.coach_id || '',
      address: athlete.address || '',
      emergency_contact: athlete.emergency_contact || '',
      status: athlete.status,
    })
    setModalError(null)
    setIsModalOpen(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (!formData.full_name.trim()) {
      setModalError('Full name is required.')
      return
    }
    if (!formData.sport_id) {
      setModalError('Please select a primary sport.')
      return
    }

    try {
      setSaving(true)
      setModalError(null)
      const payload = {
        ...formData,
        date_of_birth: formData.date_of_birth ? new Date(formData.date_of_birth).toISOString() : null,
        coach_id: formData.coach_id || null,
      }

      if (editingAthlete) {
        await updateAthlete(editingAthlete.id, payload)
        setFeedback(`Athlete "${formData.full_name}" updated successfully.`)
      } else {
        if (!formData.email.trim()) {
          setModalError('Email is required.')
          setSaving(false)
          return
        }
        await createAthlete(payload)
        setFeedback(`Athlete "${formData.full_name}" created successfully.`)
      }
      setIsModalOpen(false)
      fetchData()
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed to save athlete.')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleStatus = async (athlete) => {
    const nextStatus = athlete.status === 'active' ? 'inactive' : 'active'
    try {
      await setAthleteStatus(athlete.id, nextStatus)
      setFeedback(`Athlete "${athlete.full_name}" status set to ${nextStatus}.`)
      fetchData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update athlete status.')
    }
  }

  const handleReassignCoach = async () => {
    if (!reassignModal) return
    try {
      setReassigning(true)
      await assignCoachToAthlete(reassignModal.id, newCoachId || null)
      setFeedback(`Coach reassigned for "${reassignModal.full_name}".`)
      setReassignModal(null)
      fetchData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reassign coach.')
    } finally {
      setReassigning(false)
    }
  }

  return (
    <AppLayout title="Athlete Management">
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
              placeholder="Search by name, email, phone..."
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
              value={coachFilter}
              onChange={(e) => setCoachFilter(e.target.value)}
            >
              <option value="all">All Coaches</option>
              {coaches.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.full_name}
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
            + Add Athlete
          </button>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Athlete</th>
                  <th>Primary Sport</th>
                  <th>Assigned Coach</th>
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
                      No athletes found matching criteria.
                    </td>
                  </tr>
                ) : (
                  athletes.map((a) => (
                    <tr key={a.id}>
                      <td>
                        <strong>{a.full_name}</strong>
                        <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-xs)' }}>
                          {a.email} {a.phone && `• ${a.phone}`}
                        </div>
                      </td>
                      <td>
                        <span style={{ fontWeight: 600 }}>{a.sport_name || 'Unassigned'}</span>
                      </td>
                      <td>
                        {a.coach_name ? (
                          <span style={{ color: 'var(--color-accent)' }}>{a.coach_name}</span>
                        ) : (
                          <span style={{ color: 'var(--color-text-muted)' }}>Unassigned</span>
                        )}
                      </td>
                      <td style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                        <span style={{ textTransform: 'capitalize' }}>{a.gender || '—'}</span>
                        {a.date_of_birth && ` (${new Date(a.date_of_birth).toLocaleDateString()})`}
                      </td>
                      <td style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                        {a.emergency_contact || '—'}
                      </td>
                      <td>
                        <span
                          className={`${styles.badge} ${
                            a.status === 'active' ? styles.badgeActive : styles.badgeInactive
                          }`}
                        >
                          {a.status}
                        </span>
                      </td>
                      <td>
                        <div className={styles.actionsCell}>
                          <button className={styles.actionBtn} onClick={() => openEditModal(a)}>
                            Edit
                          </button>
                          <button
                            className={styles.actionBtn}
                            onClick={() => {
                              setReassignModal(a)
                              setNewCoachId(a.coach_id || '')
                            }}
                          >
                            Coach
                          </button>
                          <button className={styles.actionBtn} onClick={() => handleToggleStatus(a)}>
                            {a.status === 'active' ? 'Deactivate' : 'Activate'}
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

        {/* Modal: Create / Edit Athlete */}
        {isModalOpen && (
          <div className={styles.modalOverlay}>
            <div className={styles.modal} style={{ maxWidth: 640 }}>
              <div className={styles.modalHeader}>
                <h3 className={styles.modalTitle}>
                  {editingAthlete ? 'Edit Athlete Profile' : 'Register New Athlete'}
                </h3>
                <button className={styles.closeBtn} onClick={() => setIsModalOpen(false)}>
                  ×
                </button>
              </div>

              <form onSubmit={handleSave}>
                <div className={styles.modalBody}>
                  {modalError && <div className={styles.alertError}>{modalError}</div>}

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Full Name *</label>
                      <input
                        type="text"
                        className={styles.formInput}
                        value={formData.full_name}
                        onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                        placeholder="e.g. Rahul Sharma"
                        required
                      />
                    </div>

                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Email *</label>
                      <input
                        type="email"
                        className={styles.formInput}
                        value={formData.email}
                        disabled={!!editingAthlete}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        placeholder="athlete@athletix.dev"
                        required
                      />
                    </div>
                  </div>

                  {!editingAthlete && (
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Password (Default: Athlete@123)</label>
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
                      <label className={styles.formLabel}>Primary Sport *</label>
                      <select
                        className={styles.formSelect}
                        value={formData.sport_id}
                        onChange={(e) => setFormData({ ...formData, sport_id: e.target.value })}
                        required
                      >
                        <option value="">Select sport...</option>
                        {sports.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Assigned Coach</label>
                      <select
                        className={styles.formSelect}
                        value={formData.coach_id}
                        onChange={(e) => setFormData({ ...formData, coach_id: e.target.value })}
                      >
                        <option value="">No assigned coach</option>
                        {coaches.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.full_name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Phone</label>
                      <input
                        type="text"
                        className={styles.formInput}
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        placeholder="+91 98000 00000"
                      />
                    </div>

                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Date of Birth</label>
                      <input
                        type="date"
                        className={styles.formInput}
                        value={formData.date_of_birth}
                        onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Gender</label>
                      <select
                        className={styles.formSelect}
                        value={formData.gender}
                        onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                      >
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                        <option value="other">Other</option>
                      </select>
                    </div>

                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Status</label>
                      <select
                        className={styles.formSelect}
                        value={formData.status}
                        onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                      >
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                      </select>
                    </div>
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Residential Address</label>
                    <input
                      type="text"
                      className={styles.formInput}
                      value={formData.address}
                      onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                      placeholder="Street, City, Postal Code"
                    />
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Emergency Contact</label>
                    <input
                      type="text"
                      className={styles.formInput}
                      value={formData.emergency_contact}
                      onChange={(e) =>
                        setFormData({ ...formData, emergency_contact: e.target.value })
                      }
                      placeholder="e.g. Parent Name: +91 99000 00000"
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
                    {saving ? 'Saving...' : editingAthlete ? 'Save Changes' : 'Create Athlete'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Reassign Coach */}
        {reassignModal && (
          <div className={styles.modalOverlay}>
            <div className={styles.modal} style={{ maxWidth: 440 }}>
              <div className={styles.modalHeader}>
                <h3 className={styles.modalTitle}>Reassign Coach</h3>
                <button className={styles.closeBtn} onClick={() => setReassignModal(null)}>
                  ×
                </button>
              </div>

              <div className={styles.modalBody}>
                <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text)' }}>
                  Assign coach for <strong>{reassignModal.full_name}</strong>:
                </p>

                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Select Coach</label>
                  <select
                    className={styles.formSelect}
                    value={newCoachId}
                    onChange={(e) => setNewCoachId(e.target.value)}
                  >
                    <option value="">No Coach (Unassigned)</option>
                    {coaches.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.full_name} ({c.specialization || 'Coach'})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className={styles.modalFooter}>
                <button
                  type="button"
                  className={styles.secondaryBtn}
                  onClick={() => setReassignModal(null)}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className={styles.primaryBtn}
                  disabled={reassigning}
                  onClick={handleReassignCoach}
                >
                  {reassigning ? 'Saving...' : 'Update Coach'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
