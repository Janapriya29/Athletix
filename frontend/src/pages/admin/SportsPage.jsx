import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import {
  createSport,
  deleteSport,
  getSports,
  setSportStatus,
  updateSport,
} from '../../services/sportsService'

export default function SportsPage() {
  const [sports, setSports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [feedback, setFeedback] = useState(null)

  // Filters
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingSport, setEditingSport] = useState(null)
  const [formData, setFormData] = useState({ name: '', description: '', is_active: true })
  const [modalError, setModalError] = useState(null)
  const [saving, setSaving] = useState(false)

  // Confirmation dialog
  const [confirmAction, setConfirmAction] = useState(null)

  const fetchSports = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {}
      if (search.trim()) params.search = search.trim()
      if (statusFilter !== 'all') params.is_active = statusFilter === 'active'
      const data = await getSports(params)
      setSports(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch sports.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSports()
  }, [statusFilter])

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    fetchSports()
  }

  const openCreateModal = () => {
    setEditingSport(null)
    setFormData({ name: '', description: '', is_active: true })
    setModalError(null)
    setIsModalOpen(true)
  }

  const openEditModal = (sport) => {
    setEditingSport(sport)
    setFormData({
      name: sport.name,
      description: sport.description || '',
      is_active: sport.is_active,
    })
    setModalError(null)
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingSport(null)
    setModalError(null)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (!formData.name.trim()) {
      setModalError('Sport name is required.')
      return
    }

    try {
      setSaving(true)
      setModalError(null)
      if (editingSport) {
        await updateSport(editingSport.id, formData)
        setFeedback(`Sport "${formData.name}" updated successfully.`)
      } else {
        await createSport(formData)
        setFeedback(`Sport "${formData.name}" created successfully.`)
      }
      closeModal()
      fetchSports()
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed to save sport.')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleStatus = async (sport) => {
    try {
      await setSportStatus(sport.id, !sport.is_active)
      setFeedback(`Sport "${sport.name}" status updated.`)
      fetchSports()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to change sport status.')
    }
  }

  const handleDelete = async (sport) => {
    try {
      const res = await deleteSport(sport.id)
      setFeedback(res.message || `Sport "${sport.name}" removed.`)
      fetchSports()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete sport.')
    } finally {
      setConfirmAction(null)
    }
  }

  return (
    <AppLayout title="Sports Management">
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
              placeholder="Search sports..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              className={styles.selectInput}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="active">Active Only</option>
              <option value="inactive">Inactive Only</option>
            </select>
            <button type="submit" className={styles.secondaryBtn}>Search</button>
          </form>

          <button className={styles.primaryBtn} onClick={openCreateModal}>
            + Add Sport
          </button>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Sport Name</th>
                  <th>Description</th>
                  <th>Athletes</th>
                  <th>Metrics</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sports.length === 0 ? (
                  <tr>
                    <td colSpan="6" className={styles.emptyState}>
                      No sports found.
                    </td>
                  </tr>
                ) : (
                  sports.map((sport) => (
                    <tr key={sport.id}>
                      <td>
                        <strong>{sport.name}</strong>
                      </td>
                      <td style={{ maxWidth: 300, color: 'var(--color-text-muted)' }}>
                        {sport.description || '—'}
                      </td>
                      <td>{sport.athlete_count ?? 0}</td>
                      <td>{sport.categories?.length || 0}</td>
                      <td>
                        <span
                          className={`${styles.badge} ${
                            sport.is_active ? styles.badgeActive : styles.badgeInactive
                          }`}
                        >
                          {sport.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>
                        <div className={styles.actionsCell}>
                          <button
                            className={styles.actionBtn}
                            onClick={() => openEditModal(sport)}
                          >
                            Edit
                          </button>
                          <button
                            className={styles.actionBtn}
                            onClick={() => handleToggleStatus(sport)}
                          >
                            {sport.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                          <button
                            className={styles.dangerBtn}
                            onClick={() =>
                              setConfirmAction({
                                title: `Delete "${sport.name}"?`,
                                message:
                                  sport.athlete_count > 0
                                    ? `This sport has ${sport.athlete_count} assigned athlete(s). Proceeding will safely deactivate it.`
                                    : 'Are you sure you want to permanently delete this sport?',
                                onConfirm: () => handleDelete(sport),
                              })
                            }
                          >
                            Delete
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

        {/* Modal: Create / Edit Sport */}
        {isModalOpen && (
          <div className={styles.modalOverlay}>
            <div className={styles.modal}>
              <div className={styles.modalHeader}>
                <h3 className={styles.modalTitle}>
                  {editingSport ? 'Edit Sport' : 'Create Sport'}
                </h3>
                <button className={styles.closeBtn} onClick={closeModal}>
                  ×
                </button>
              </div>

              <form onSubmit={handleSave}>
                <div className={styles.modalBody}>
                  {modalError && <div className={styles.alertError}>{modalError}</div>}

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Sport Name *</label>
                    <input
                      type="text"
                      className={styles.formInput}
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="e.g. Football"
                      required
                    />
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Description</label>
                    <textarea
                      rows="3"
                      className={styles.formTextarea}
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Short overview of the sport and academy curriculum..."
                    />
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Status</label>
                    <select
                      className={styles.formSelect}
                      value={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.value === 'true' })}
                    >
                      <option value="true">Active</option>
                      <option value="false">Inactive</option>
                    </select>
                  </div>
                </div>

                <div className={styles.modalFooter}>
                  <button type="button" className={styles.secondaryBtn} onClick={closeModal}>
                    Cancel
                  </button>
                  <button type="submit" className={styles.primaryBtn} disabled={saving}>
                    {saving ? 'Saving...' : editingSport ? 'Save Changes' : 'Create Sport'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Confirmation Modal */}
        {confirmAction && (
          <div className={styles.modalOverlay}>
            <div className={styles.modal} style={{ maxWidth: 440 }}>
              <div className={styles.modalHeader}>
                <h3 className={styles.modalTitle}>{confirmAction.title}</h3>
                <button className={styles.closeBtn} onClick={() => setConfirmAction(null)}>
                  ×
                </button>
              </div>
              <div className={styles.modalBody}>
                <p style={{ color: 'var(--color-text)' }}>{confirmAction.message}</p>
              </div>
              <div className={styles.modalFooter}>
                <button
                  className={styles.secondaryBtn}
                  onClick={() => setConfirmAction(null)}
                >
                  Cancel
                </button>
                <button
                  className={styles.dangerBtn}
                  style={{ padding: '8px 16px', fontSize: 'var(--text-sm)' }}
                  onClick={confirmAction.onConfirm}
                >
                  Confirm
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
