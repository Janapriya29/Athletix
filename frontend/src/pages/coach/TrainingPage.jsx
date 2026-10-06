import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import {
  addSessionParticipant,
  createTrainingSession,
  getCoachTrainingSummary,
  getTrainingSessions,
  recordAttendance,
  removeSessionParticipant,
  setTrainingSessionStatus,
  updateTrainingSession,
} from '../../services/trainingService'
import { getMyCoachProfile } from '../../services/coachesService'
import { getSports } from '../../services/sportsService'
import { getAthletes } from '../../services/athletesService'

export default function TrainingPage() {
  const [sessions, setSessions] = useState([])
  const [summary, setSummary] = useState(null)
  const [coachProfile, setCoachProfile] = useState(null)
  const [sports, setSports] = useState([])
  const [myAthletes, setMyAthletes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [feedback, setFeedback] = useState(null)

  // Filters
  const [search, setSearch] = useState('')
  const [sportFilter, setSportFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  // Create / Edit Session Modal
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingSession, setEditingSession] = useState(null)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    sport_id: '',
    session_date: '',
    start_time: '09:00',
    end_time: '11:00',
    location: 'Academy Main Ground',
    status: 'scheduled',
    athlete_ids: [],
  })
  const [modalError, setModalError] = useState(null)
  const [saving, setSaving] = useState(false)

  // Manage Participants Modal
  const [participantModalSession, setParticipantModalSession] = useState(null)
  const [newParticipantId, setNewParticipantId] = useState('')

  // Quick Attendance Modal
  const [attModalSession, setAttModalSession] = useState(null)
  const [attStatuses, setAttStatuses] = useState({})
  const [attRemarks, setAttRemarks] = useState({})
  const [attSaving, setAttSaving] = useState(false)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {}
      if (search.trim()) params.search = search.trim()
      if (sportFilter !== 'all') params.sport_id = sportFilter
      if (statusFilter !== 'all') params.status = statusFilter

      const [sessData, summData, profileData, sportsData, athletesData] = await Promise.all([
        getTrainingSessions(params),
        getCoachTrainingSummary().catch(() => null),
        getMyCoachProfile().catch(() => null),
        getSports().catch(() => []),
        getAthletes().catch(() => []),
      ])

      setSessions(sessData || [])
      setSummary(summData)
      setCoachProfile(profileData)
      setSports(sportsData || [])
      setMyAthletes(athletesData || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load training sessions.')
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
    setEditingSession(null)
    const defaultSport =
      coachProfile?.sport_ids?.[0] || (sports.length > 0 ? sports[0].id : '')
    setFormData({
      title: '',
      description: '',
      sport_id: defaultSport,
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
      setModalError('Session title is required.')
      return
    }
    if (!formData.sport_id) {
      setModalError('Please select a sport.')
      return
    }

    try {
      setSaving(true)
      setModalError(null)
      const payload = {
        ...formData,
        coach_id: coachProfile?.id,
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
      setFeedback(`Session marked as ${newStatus}.`)
      fetchData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update session status.')
    }
  }

  const openParticipantsModal = (sess) => {
    setParticipantModalSession(sess)
    setNewParticipantId('')
  }

  const handleAddParticipant = async () => {
    if (!participantModalSession || !newParticipantId) return
    try {
      const updated = await addSessionParticipant(participantModalSession.id, newParticipantId)
      setParticipantModalSession(updated)
      setNewParticipantId('')
      setFeedback('Athlete added to training session.')
      fetchData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add athlete.')
    }
  }

  const handleRemoveParticipant = async (athleteId) => {
    if (!participantModalSession) return
    try {
      const updated = await removeSessionParticipant(participantModalSession.id, athleteId)
      setParticipantModalSession(updated)
      setFeedback('Athlete removed from training session.')
      fetchData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove athlete.')
    }
  }

  const openAttendanceModal = (sess) => {
    setAttModalSession(sess)
    const initialStatuses = {}
    const initialRemarks = {}
    sess.participants?.forEach((p) => {
      initialStatuses[p.athlete_id] = p.attendance_status || 'present'
      initialRemarks[p.athlete_id] = p.remarks || ''
    })
    setAttStatuses(initialStatuses)
    setAttRemarks(initialRemarks)
  }

  const handleSaveAttendanceRow = async (athleteId) => {
    if (!attModalSession) return
    try {
      setAttSaving(true)
      const st = attStatuses[athleteId] || 'present'
      const rem = attRemarks[athleteId] || null
      await recordAttendance(attModalSession.id, athleteId, st, rem)
      setFeedback('Attendance recorded successfully.')
      // Refresh current modal data
      const refreshedList = await getTrainingSessions({ search: attModalSession.title })
      const found = refreshedList.find((s) => s.id === attModalSession.id)
      if (found) setAttModalSession(found)
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

  // Filter sports available to coach
  const coachSports =
    coachProfile?.sport_ids?.length > 0
      ? sports.filter((s) => coachProfile.sport_ids.includes(s.id))
      : sports

  return (
    <AppLayout title="Coach Training Sessions">
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

        {/* Summary Metric Cards */}
        {summary && (
          <div className={styles.statsGrid}>
            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: 'var(--color-accent)' }}>
                {summary.today_count}
              </span>
              <span className={styles.statLabel}>Today's Sessions</span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: '#60a5fa' }}>
                {summary.upcoming_count}
              </span>
              <span className={styles.statLabel}>Upcoming Sessions</span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: '#22c55e' }}>
                {summary.completed_count}
              </span>
              <span className={styles.statLabel}>Completed Sessions</span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statValue} style={{ color: '#fbbf24' }}>
                {summary.average_attendance_percentage}%
              </span>
              <span className={styles.statLabel}>Avg Attendance Rate</span>
            </div>
          </div>
        )}

        {/* Header Controls */}
        <div className={styles.headerBar}>
          <form className={styles.controls} onSubmit={handleSearchSubmit}>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="Search by session title, venue..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              className={styles.selectInput}
              value={sportFilter}
              onChange={(e) => setSportFilter(e.target.value)}
            >
              <option value="all">All Sports</option>
              {coachSports.map((s) => (
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
                    <td colSpan="7" className={styles.emptyState}>
                      No training sessions scheduled. Click "+ Schedule Session" to begin.
                    </td>
                  </tr>
                ) : (
                  sessions.map((sess) => (
                    <tr key={sess.id}>
                      <td>
                        <strong>{sess.title}</strong>
                        {sess.description && (
                          <div
                            style={{
                              fontSize: '0.75rem',
                              color: 'var(--color-text-muted)',
                              maxWidth: 240,
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                            }}
                          >
                            {sess.description}
                          </div>
                        )}
                      </td>
                      <td>{sess.sport_name || '—'}</td>
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
                            onClick={() => openParticipantsModal(sess)}
                          >
                            Athletes
                          </button>
                          <button
                            className={styles.actionBtn}
                            onClick={() => openAttendanceModal(sess)}
                          >
                            Attendance
                          </button>
                          <button
                            className={styles.actionBtn}
                            onClick={() => openEditModal(sess)}
                          >
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
            <div className={styles.modal} style={{ maxWidth: 580 }}>
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
                      placeholder="e.g. Afternoon Endurance & Agility Drills"
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
                        {coachSports.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className={styles.formGroup}>
                      <label className={styles.formLabel}>Location / Venue</label>
                      <input
                        type="text"
                        className={styles.formInput}
                        value={formData.location}
                        onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                        placeholder="Court 1, Ground A, etc."
                      />
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

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Session Objectives & Training Focus</label>
                    <textarea
                      rows="3"
                      className={styles.formTextarea}
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Drills, conditioning goals, equipment, tactical notes..."
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

        {/* Modal: Manage Athletes / Participants */}
        {participantModalSession && (
          <div className={styles.modalOverlay}>
            <div className={styles.modal} style={{ maxWidth: 580 }}>
              <div className={styles.modalHeader}>
                <div>
                  <h3 className={styles.modalTitle}>Manage Athletes</h3>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {participantModalSession.title} ({participantModalSession.sport_name})
                  </div>
                </div>
                <button className={styles.closeBtn} onClick={() => setParticipantModalSession(null)}>
                  ×
                </button>
              </div>

              <div className={styles.modalBody}>
                {/* Add athlete dropdown */}
                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                  <select
                    className={styles.formSelect}
                    style={{ flex: 1 }}
                    value={newParticipantId}
                    onChange={(e) => setNewParticipantId(e.target.value)}
                  >
                    <option value="">Select athlete to add...</option>
                    {myAthletes
                      .filter((a) => !participantModalSession.athlete_ids?.includes(a.id))
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

                {/* Enrolled participants list */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 300, overflowY: 'auto' }}>
                  {participantModalSession.participants?.length === 0 ? (
                    <p className={styles.emptyState}>No athletes registered in this session yet.</p>
                  ) : (
                    participantModalSession.participants?.map((p) => (
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

              <div className={styles.modalFooter}>
                <button
                  type="button"
                  className={styles.secondaryBtn}
                  onClick={() => setParticipantModalSession(null)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Record Attendance */}
        {attModalSession && (
          <div className={styles.modalOverlay}>
            <div className={styles.modal} style={{ maxWidth: 640 }}>
              <div className={styles.modalHeader}>
                <div>
                  <h3 className={styles.modalTitle}>Record Attendance</h3>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {attModalSession.title} • {new Date(attModalSession.session_date).toLocaleDateString()}
                  </div>
                </div>
                <button className={styles.closeBtn} onClick={() => setAttModalSession(null)}>
                  ×
                </button>
              </div>

              <div className={styles.modalBody}>
                {attModalSession.participants?.length === 0 ? (
                  <p className={styles.emptyState}>
                    Please add athletes to this session before recording attendance.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxHeight: 360, overflowY: 'auto' }}>
                    {attModalSession.participants?.map((p) => (
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
                          <div>
                            <strong>{p.full_name}</strong>
                            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                              {p.email}
                            </div>
                          </div>
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
                            placeholder="Optional notes / remarks (e.g. excused absence, injury)..."
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
                            onClick={() => handleSaveAttendanceRow(p.athlete_id)}
                          >
                            Save
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className={styles.modalFooter}>
                <button
                  type="button"
                  className={styles.secondaryBtn}
                  onClick={() => setAttModalSession(null)}
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
