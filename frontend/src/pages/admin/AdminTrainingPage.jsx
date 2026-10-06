import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import {
  addSessionParticipant,
  createTrainingSession,
  getAdminTrainingSummary,
  getTrainingSessions,
  recordAttendance,
  removeSessionParticipant,
  setTrainingSessionStatus,
  updateTrainingSession,
} from '../../services/trainingService'
import { getSports } from '../../services/sportsService'
import { getCoaches } from '../../services/coachesService'
import { getAthletes } from '../../services/athletesService'

export default function AdminTrainingPage() {
  const [sessions, setSessions] = useState([])
  const [summary, setSummary] = useState(null)
  const [sports, setSports] = useState([])
  const [coaches, setCoaches] = useState([])
  const [allAthletes, setAllAthletes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [feedback, setFeedback] = useState(null)

  // Filters
  const [search, setSearch] = useState('')
  const [sportFilter, setSportFilter] = useState('all')
  const [coachFilter, setCoachFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  // Create / Edit Session Modal
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingSession, setEditingSession] = useState(null)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    sport_id: '',
    coach_id: '',
    session_date: '',
    start_time: '09:00',
    end_time: '11:00',
    location: 'Academy Main Ground',
    status: 'scheduled',
    athlete_ids: [],
  })
  const [modalError, setModalError] = useState(null)
  const [saving, setSaving] = useState(false)

  // View / Attendance Modal
  const [activeSession, setActiveSession] = useState(null)
  const [activeTab, setActiveTab] = useState('participants') // 'participants' | 'attendance'
  const [newParticipantId, setNewParticipantId] = useState('')
  const [attRemarks, setAttRemarks] = useState({})
  const [attStatuses, setAttStatuses] = useState({})
  const [attSaving, setAttSaving] = useState(false)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {}
      if (search.trim()) params.search = search.trim()
      if (sportFilter !== 'all') params.sport_id = sportFilter
      if (coachFilter !== 'all') params.coach_id = coachFilter
      if (statusFilter !== 'all') params.status = statusFilter

      const [sessData, summData, sportsData, coachesData, athletesData] = await Promise.all([
        getTrainingSessions(params),
        getAdminTrainingSummary(),
        getSports(),
        getCoaches(),
        getAthletes(),
      ])
      setSessions(sessData)
      setSummary(summData)
      setSports(sportsData)
      setCoaches(coachesData)
      setAllAthletes(athletesData)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load training sessions.')
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
    setEditingSession(null)
    setFormData({
      title: '',
      description: '',
      sport_id: sports.length > 0 ? sports[0].id : '',
      coach_id: coaches.length > 0 ? coaches[0].id : '',
      session_date: new Date().toISOString().substring(0, 10),
      start_time: '09:00',
      end_time: '11:00',
      location: 'Academy Main Ground',
      status: 'scheduled',
      athlete_ids: [],
    })
    setModalError(null)
    setIsModalOpen(true)
  }

  const openEditModal = (sess) => {
    setEditingSession(sess)
    setFormData({
      title: sess.title,
      description: sess.description || '',
      sport_id: sess.sport_id,
      coach_id: sess.coach_id,
      session_date: sess.session_date ? sess.session_date.substring(0, 10) : '',
      start_time: sess.start_time || '09:00',
      end_time: sess.end_time || '11:00',
      location: sess.location || 'Academy Main Ground',
      status: sess.status,
      athlete_ids: sess.athlete_ids || [],
    })
    setModalError(null)
    setIsModalOpen(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (!formData.title.trim()) {
      setModalError('Title is required.')
      return
    }
    if (!formData.sport_id || !formData.coach_id) {
      setModalError('Please select both a sport and coach.')
      return
    }

    try {
      setSaving(true)
      setModalError(null)
      const payload = {
        ...formData,
        session_date: new Date(formData.session_date).toISOString(),
      }

      if (editingSession) {
        await updateTrainingSession(editingSession.id, payload)
        setFeedback(`Session "${formData.title}" updated successfully.`)
      } else {
        await createTrainingSession(payload)
        setFeedback(`Session "${formData.title}" scheduled successfully.`)
      }
      setIsModalOpen(false)
      fetchData()
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed to save session.')
    } finally {
      setSaving(false)
    }
  }

  const handleStatusChange = async (sessionId, newStatus) => {
    try {
      await setTrainingSessionStatus(sessionId, newStatus)
      setFeedback(`Session status updated to ${newStatus}.`)
      fetchData()
      if (activeSession && activeSession.id === sessionId) {
        setActiveSession({ ...activeSession, status: newStatus })
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update status.')
    }
  }

  const openSessionDetails = (sess, tab = 'participants') => {
    setActiveSession(sess)
    setActiveTab(tab)
    setNewParticipantId('')
    // Initialize attendance inputs
    const initialStatuses = {}
    const initialRemarks = {}
    sess.participants?.forEach((p) => {
      initialStatuses[p.athlete_id] = p.attendance_status || 'present'
      initialRemarks[p.athlete_id] = p.remarks || ''
    })
    setAttStatuses(initialStatuses)
    setAttRemarks(initialRemarks)
  }

  const handleAddParticipant = async () => {
    if (!activeSession || !newParticipantId) return
    try {
      const updated = await addSessionParticipant(activeSession.id, newParticipantId)
      setActiveSession(updated)
      setNewParticipantId('')
      setFeedback('Athlete added to session.')
      fetchData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add athlete.')
    }
  }

  const handleRemoveParticipant = async (athleteId) => {
    if (!activeSession) return
    try {
      const updated = await removeSessionParticipant(activeSession.id, athleteId)
      setActiveSession(updated)
      setFeedback('Athlete removed from session.')
      fetchData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove athlete.')
    }
  }

  const handleRecordAttendance = async (athleteId) => {
    if (!activeSession) return
    try {
      setAttSaving(true)
      const st = attStatuses[athleteId] || 'present'
      const rem = attRemarks[athleteId] || null
      await recordAttendance(activeSession.id, athleteId, st, rem)
      setFeedback('Attendance recorded.')
      // Refresh session data
      const updated = await getTrainingSessions({ search: activeSession.title })
      const found = updated.find((s) => s.id === activeSession.id)
      if (found) setActiveSession(found)
      fetchData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to record attendance.')
    } finally {
      setAttSaving(false)
    }
  }

  const getStatusBadge = (st) => {
    const s = st?.toLowerCase()
    if (s === 'completed') return styles.badgeCompleted
    if (s === 'cancelled') return styles.badgeCancelled
    return styles.badgeScheduled
  }

  const getAttBadge = (st) => {
    const s = st?.toLowerCase()
    if (s === 'present') return styles.badgePresent
    if (s === 'late') return styles.badgeLate
    if (s === 'absent') return styles.badgeAbsent
    return styles.badgeInactive
  }

  return (
    <AppLayout title="Training & Attendance Management">
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

        {/* Summary Cards */}
        {summary && (
          <div className={styles.statsGrid}>
            <div className={styles.statCard}>
              <span className={styles.statValue}>{summary.total_sessions}</span>
              <span className={styles.statLabel}>Total Sessions</span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: '#60a5fa' }}>
                {summary.scheduled_count}
              </span>
              <span className={styles.statLabel}>Scheduled</span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: '#22c55e' }}>
                {summary.completed_count}
              </span>
              <span className={styles.statLabel}>Completed</span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: '#94a3b8' }}>
                {summary.cancelled_count}
              </span>
              <span className={styles.statLabel}>Cancelled</span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: 'var(--color-accent)' }}>
                {summary.average_attendance_percentage}%
              </span>
              <span className={styles.statLabel}>Avg Attendance</span>
            </div>
          </div>
        )}

        {/* Filter Controls */}
        <div className={styles.headerBar}>
          <form className={styles.controls} onSubmit={handleSearchSubmit}>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="Search by title, venue..."
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
              <option value="scheduled">Scheduled</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
            <button type="submit" className={styles.secondaryBtn}>Search</button>
          </form>

          <button className={styles.primaryBtn} onClick={openCreateModal}>
            + Schedule Session
          </button>
        </div>

        {/* Sessions Table */}
        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Session Title</th>
                  <th>Sport</th>
                  <th>Coach</th>
                  <th>Date & Time</th>
                  <th>Location</th>
                  <th>Athletes</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sessions.length === 0 ? (
                  <tr>
                    <td colSpan="8" className={styles.emptyState}>
                      No training sessions found matching criteria.
                    </td>
                  </tr>
                ) : (
                  sessions.map((sess) => (
                    <tr key={sess.id}>
                      <td>
                        <strong>{sess.title}</strong>
                        {sess.description && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', maxWidth: 220, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {sess.description}
                          </div>
                        )}
                      </td>
                      <td>{sess.sport_name || '—'}</td>
                      <td>{sess.coach_name || '—'}</td>
                      <td style={{ fontSize: 'var(--text-xs)' }}>
                        <div>{new Date(sess.session_date).toLocaleDateString()}</div>
                        <div style={{ color: 'var(--color-text-muted)' }}>
                          {sess.start_time} – {sess.end_time}
                        </div>
                      </td>
                      <td style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-xs)' }}>
                        {sess.location || '—'}
                      </td>
                      <td>
                        <strong style={{ color: 'var(--color-accent)' }}>
                          {sess.participant_count ?? 0}
                        </strong>
                      </td>
                      <td>
                        <span className={`${styles.badge} ${getStatusBadge(sess.status)}`}>
                          {sess.status}
                        </span>
                      </td>
                      <td>
                        <div className={styles.actionsCell}>
                          <button
                            className={styles.actionBtn}
                            onClick={() => openSessionDetails(sess, 'participants')}
                          >
                            Athletes
                          </button>
                          <button
                            className={styles.actionBtn}
                            onClick={() => openSessionDetails(sess, 'attendance')}
                          >
                            Attendance
                          </button>
                          <button className={styles.actionBtn} onClick={() => openEditModal(sess)}>
                            Edit
                          </button>
                          {sess.status === 'scheduled' && (
                            <button
                              className={styles.actionBtn}
                              style={{ color: '#22c55e' }}
                              onClick={() => handleStatusChange(sess.id, 'completed')}
                            >
                              Complete
                            </button>
                          )}
                          {sess.status !== 'cancelled' && (
                            <button
                              className={styles.dangerBtn}
                              onClick={() => handleStatusChange(sess.id, 'cancelled')}
                            >
                              Cancel
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Modal: Schedule / Edit Training Session */}
        {isModalOpen && (
          <div className={styles.modalOverlay}>
            <div className={styles.modal} style={{ maxWidth: 600 }}>
              <div className={styles.modalHeader}>
                <h3 className={styles.modalTitle}>
                  {editingSession ? 'Edit Training Session' : 'Schedule Training Session'}
                </h3>
                <button className={styles.closeBtn} onClick={() => setIsModalOpen(false)}>
                  ×
                </button>
              </div>

              <form onSubmit={handleSave}>
                <div className={styles.modalBody}>
                  {modalError && <div className={styles.alertError}>{modalError}</div>}

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Session Title *</label>
                    <input
                      type="text"
                      className={styles.formInput}
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      placeholder="e.g. Tactical Defense & Passing Drills"
                      required
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Sport *</label>
                      <select
                        className={styles.formSelect}
                        value={formData.sport_id}
                        onChange={(e) => setFormData({ ...formData, sport_id: e.target.value })}
                        required
                      >
                        <option value="">Select Sport...</option>
                        {sports.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Lead Coach *</label>
                      <select
                        className={styles.formSelect}
                        value={formData.coach_id}
                        onChange={(e) => setFormData({ ...formData, coach_id: e.target.value })}
                        required
                      >
                        <option value="">Select Coach...</option>
                        {coaches.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.full_name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 'var(--space-3)' }}>
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Date *</label>
                      <input
                        type="date"
                        className={styles.formInput}
                        value={formData.session_date}
                        onChange={(e) => setFormData({ ...formData, session_date: e.target.value })}
                        required
                      />
                    </div>
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Start Time *</label>
                      <input
                        type="time"
                        className={styles.formInput}
                        value={formData.start_time}
                        onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                        required
                      />
                    </div>
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>End Time *</label>
                      <input
                        type="time"
                        className={styles.formInput}
                        value={formData.end_time}
                        onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                        required
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Location / Venue</label>
                      <input
                        type="text"
                        className={styles.formInput}
                        value={formData.location}
                        onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                        placeholder="Ground A, Court 2, etc."
                      />
                    </div>

                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Status</label>
                      <select
                        className={styles.formSelect}
                        value={formData.status}
                        onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                      >
                        <option value="scheduled">Scheduled</option>
                        <option value="completed">Completed</option>
                        <option value="cancelled">Cancelled</option>
                      </select>
                    </div>
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Session Objectives & Notes</label>
                    <textarea
                      rows="3"
                      className={styles.formTextarea}
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Focus areas, drills, equipment requirements..."
                    />
                  </div>
                </div>

                <div className={styles.modalFooter}>
                  <button type="button" className={styles.secondaryBtn} onClick={() => setIsModalOpen(false)}>
                    Cancel
                  </button>
                  <button type="submit" className={styles.primaryBtn} disabled={saving}>
                    {saving ? 'Saving...' : editingSession ? 'Save Changes' : 'Schedule Session'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: View Participants & Attendance Hub */}
        {activeSession && (
          <div className={styles.modalOverlay}>
            <div className={styles.modal} style={{ maxWidth: 640 }}>
              <div className={styles.modalHeader}>
                <div>
                  <h3 className={styles.modalTitle}>{activeSession.title}</h3>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {activeSession.sport_name} • {new Date(activeSession.session_date).toLocaleDateString()} ({activeSession.start_time} - {activeSession.end_time})
                  </div>
                </div>
                <button className={styles.closeBtn} onClick={() => setActiveSession(null)}>
                  ×
                </button>
              </div>

              {/* Tabs inside modal */}
              <div style={{ display: 'flex', gap: 8, padding: '12px 20px', borderBottom: '1px solid var(--color-border)' }}>
                <button
                  className={activeTab === 'participants' ? styles.primaryBtn : styles.secondaryBtn}
                  style={{ padding: '4px 12px', fontSize: '0.8rem' }}
                  onClick={() => setActiveTab('participants')}
                >
                  Participants ({activeSession.participants?.length || 0})
                </button>
                <button
                  className={activeTab === 'attendance' ? styles.primaryBtn : styles.secondaryBtn}
                  style={{ padding: '4px 12px', fontSize: '0.8rem' }}
                  onClick={() => setActiveTab('attendance')}
                >
                  Record Attendance
                </button>
              </div>

              <div className={styles.modalBody}>
                {activeTab === 'participants' ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {/* Add Participant row */}
                    <div style={{ display: 'flex', gap: 8 }}>
                      <select
                        className={styles.formSelect}
                        style={{ flex: 1 }}
                        value={newParticipantId}
                        onChange={(e) => setNewParticipantId(e.target.value)}
                      >
                        <option value="">Select athlete to add...</option>
                        {allAthletes
                          .filter((a) => !activeSession.athlete_ids?.includes(a.id))
                          .map((a) => (
                            <option key={a.id} value={a.id}>
                              {a.full_name} ({a.sport_name || 'No sport'})
                            </option>
                          ))}
                      </select>
                      <button className={styles.primaryBtn} onClick={handleAddParticipant}>
                        + Add
                      </button>
                    </div>

                    {/* Participant List */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 300, overflowY: 'auto' }}>
                      {activeSession.participants?.length === 0 ? (
                        <p className={styles.emptyState}>No athletes registered in this session yet.</p>
                      ) : (
                        activeSession.participants?.map((p) => (
                          <div
                            key={p.athlete_id}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              padding: '8px 12px',
                              backgroundColor: 'var(--color-surface-2)',
                              borderRadius: 4,
                            }}
                          >
                            <div>
                              <strong>{p.full_name}</strong>
                              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                                {p.sport_name || 'Athlete'} • {p.email}
                              </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              {p.attendance_status && (
                                <span className={`${styles.badge} ${getAttBadge(p.attendance_status)}`}>
                                  {p.attendance_status}
                                </span>
                              )}
                              <button
                                className={styles.dangerBtn}
                                onClick={() => handleRemoveParticipant(p.athlete_id)}
                              >
                                Remove
                              </button>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                ) : (
                  /* Attendance Tab */
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {activeSession.participants?.length === 0 ? (
                      <p className={styles.emptyState}>Add participants before recording attendance.</p>
                    ) : (
                      activeSession.participants?.map((p) => (
                        <div
                          key={p.athlete_id}
                          style={{
                            padding: '10px 14px',
                            backgroundColor: 'var(--color-surface-2)',
                            borderRadius: 6,
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 8,
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <strong>{p.full_name}</strong>
                            <div style={{ display: 'flex', gap: 6 }}>
                              {['present', 'late', 'absent'].map((st) => (
                                <button
                                  key={st}
                                  type="button"
                                  onClick={() =>
                                    setAttStatuses({ ...attStatuses, [p.athlete_id]: st })
                                  }
                                  style={{
                                    textTransform: 'capitalize',
                                    fontSize: '0.75rem',
                                    fontWeight: 600,
                                    padding: '4px 10px',
                                    borderRadius: 4,
                                    cursor: 'pointer',
                                    border: '1px solid var(--color-border)',
                                    backgroundColor:
                                      attStatuses[p.athlete_id] === st
                                        ? st === 'present'
                                          ? '#22c55e'
                                          : st === 'late'
                                          ? '#f59e0b'
                                          : '#ef4444'
                                        : 'var(--color-surface)',
                                    color:
                                      attStatuses[p.athlete_id] === st
                                        ? '#0f1117'
                                        : 'var(--color-text)',
                                  }}
                                >
                                  {st}
                                </button>
                              ))}
                            </div>
                          </div>

                          <div style={{ display: 'flex', gap: 8 }}>
                            <input
                              type="text"
                              className={styles.formInput}
                              style={{ flex: 1, padding: '4px 8px', fontSize: '0.8rem' }}
                              placeholder="Remarks (optional, e.g. 15m late, sprained ankle)"
                              value={attRemarks[p.athlete_id] || ''}
                              onChange={(e) =>
                                setAttRemarks({ ...attRemarks, [p.athlete_id]: e.target.value })
                              }
                            />
                            <button
                              type="button"
                              className={styles.secondaryBtn}
                              style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                              disabled={attSaving}
                              onClick={() => handleRecordAttendance(p.athlete_id)}
                            >
                              Save
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              <div className={styles.modalFooter}>
                <button
                  type="button"
                  className={styles.secondaryBtn}
                  onClick={() => setActiveSession(null)}
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
