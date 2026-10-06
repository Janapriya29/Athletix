import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import {
  createUser,
  getUsers,
  setUserStatus,
  updateUser,
} from '../../services/usersService'

export default function UsersPage() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [feedback, setFeedback] = useState(null)

  // Filters
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    password: '',
    role: 'athlete',
    is_active: true,
  })
  const [modalError, setModalError] = useState(null)
  const [saving, setSaving] = useState(false)

  // Confirmation dialog
  const [confirmAction, setConfirmAction] = useState(null)

  const fetchUsers = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {}
      if (search.trim()) params.search = search.trim()
      if (roleFilter !== 'all') params.role = roleFilter
      if (statusFilter !== 'all') params.is_active = statusFilter === 'active'
      const data = await getUsers(params)
      setUsers(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch users.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [roleFilter, statusFilter])

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    fetchUsers()
  }

  const openCreateModal = () => {
    setEditingUser(null)
    setFormData({
      email: '',
      full_name: '',
      password: '',
      role: 'athlete',
      is_active: true,
    })
    setModalError(null)
    setIsModalOpen(true)
  }

  const openEditModal = (user) => {
    setEditingUser(user)
    setFormData({
      email: user.email,
      full_name: user.full_name,
      password: '',
      role: user.role,
      is_active: user.is_active,
    })
    setModalError(null)
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingUser(null)
    setModalError(null)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (!formData.full_name.trim()) {
      setModalError('Full name is required.')
      return
    }

    try {
      setSaving(true)
      setModalError(null)
      if (editingUser) {
        await updateUser(editingUser.id, {
          full_name: formData.full_name,
          role: formData.role,
          is_active: formData.is_active,
        })
        setFeedback(`User "${formData.full_name}" updated successfully.`)
      } else {
        if (!formData.email.trim() || !formData.password) {
          setModalError('Email and Password (min 8 chars) are required.')
          setSaving(false)
          return
        }
        await createUser({
          email: formData.email,
          full_name: formData.full_name,
          password: formData.password,
          role: formData.role,
        })
        setFeedback(`User "${formData.full_name}" created successfully.`)
      }
      closeModal()
      fetchUsers()
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed to save user.')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleStatus = async (user) => {
    try {
      await setUserStatus(user.id, !user.is_active)
      setFeedback(`User "${user.full_name}" status updated.`)
      fetchUsers()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update user status.')
    }
  }

  const getRoleBadgeClass = (role) => {
    if (role === 'admin') return styles.badgeAdmin
    if (role === 'coach') return styles.badgeCoach
    return styles.badgeAthlete
  }

  return (
    <AppLayout title="User Management">
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
              placeholder="Search by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              className={styles.selectInput}
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
            >
              <option value="all">All Roles</option>
              <option value="admin">Admin</option>
              <option value="coach">Coach</option>
              <option value="athlete">Athlete</option>
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
            + Add User
          </button>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 ? (
                  <tr>
                    <td colSpan="6" className={styles.emptyState}>
                      No users found matching criteria.
                    </td>
                  </tr>
                ) : (
                  users.map((user) => (
                    <tr key={user.id}>
                      <td>
                        <strong>{user.full_name}</strong>
                      </td>
                      <td style={{ color: 'var(--color-text-muted)' }}>{user.email}</td>
                      <td>
                        <span className={`${styles.badge} ${getRoleBadgeClass(user.role)}`}>
                          {user.role}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`${styles.badge} ${
                            user.is_active ? styles.badgeActive : styles.badgeInactive
                          }`}
                        >
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-xs)' }}>
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td>
                        <div className={styles.actionsCell}>
                          <button
                            className={styles.actionBtn}
                            onClick={() => openEditModal(user)}
                          >
                            Edit
                          </button>
                          <button
                            className={styles.actionBtn}
                            onClick={() => handleToggleStatus(user)}
                          >
                            {user.is_active ? 'Deactivate' : 'Activate'}
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

        {/* Modal: Create / Edit User */}
        {isModalOpen && (
          <div className={styles.modalOverlay}>
            <div className={styles.modal}>
              <div className={styles.modalHeader}>
                <h3 className={styles.modalTitle}>
                  {editingUser ? 'Edit User Details' : 'Create New User'}
                </h3>
                <button className={styles.closeBtn} onClick={closeModal}>
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
                    <label className={styles.formLabel}>Email Address *</label>
                    <input
                      type="email"
                      className={styles.formInput}
                      value={formData.email}
                      disabled={!!editingUser}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="e.g. sarah@athletix.dev"
                      required
                    />
                  </div>

                  {!editingUser && (
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Password (min 8 chars) *</label>
                      <input
                        type="password"
                        className={styles.formInput}
                        value={formData.password}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        placeholder="••••••••"
                        minLength={8}
                        required
                      />
                    </div>
                  )}

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Role *</label>
                    <select
                      className={styles.formSelect}
                      value={formData.role}
                      onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    >
                      <option value="athlete">Athlete</option>
                      <option value="coach">Coach</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>

                  {editingUser && (
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Account Status</label>
                      <select
                        className={styles.formSelect}
                        value={formData.is_active}
                        onChange={(e) =>
                          setFormData({ ...formData, is_active: e.target.value === 'true' })
                        }
                      >
                        <option value="true">Active</option>
                        <option value="false">Inactive</option>
                      </select>
                    </div>
                  )}
                </div>

                <div className={styles.modalFooter}>
                  <button type="button" className={styles.secondaryBtn} onClick={closeModal}>
                    Cancel
                  </button>
                  <button type="submit" className={styles.primaryBtn} disabled={saving}>
                    {saving ? 'Saving...' : editingUser ? 'Save Changes' : 'Create User'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
