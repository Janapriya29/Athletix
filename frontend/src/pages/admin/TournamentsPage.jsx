import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import StatCard from '../../components/common/StatCard'
import styles from '../../styles/Management.module.css'
import {
  createTournament,
  deleteTournament,
  getTournaments,
  updateTournament,
  getParticipants,
  addParticipant,
  removeParticipant,
  recordResult,
} from '../../services/tournamentService'
import { getSports } from '../../services/sportsService'
import { getAthletes } from '../../services/athletesService'

export default function AdminTournamentsPage() {
  const [tournaments, setTournaments] = useState([])
  const [sports, setSports] = useState([])
  const [athletes, setAthletes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actionSuccess, setActionSuccess] = useState(null)

  // Filters
  const [search, setSearch] = useState('')
  const [selectedSport, setSelectedSport] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('')

  // Create / Edit Tournament Modal
  const [showTournamentModal, setShowTournamentModal] = useState(false)
  const [editingTournament, setEditingTournament] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    sport_id: '',
    description: '',
    location: '',
    start_date: '',
    end_date: '',
    registration_deadline: '',
    status: 'upcoming',
  })

  // Manage Participants Modal
  const [showParticipantModal, setShowParticipantModal] = useState(false)
  const [activeTournament, setActiveTournament] = useState(null)
  const [participants, setParticipants] = useState([])
  const [partLoading, setPartLoading] = useState(false)
  const [newPartAthleteId, setNewPartAthleteId] = useState('')
  const [newPartEvent, setNewPartEvent] = useState('')

  // Record Results Modal
  const [showResultsModal, setShowResultsModal] = useState(false)
  const [selectedResultParticipant, setSelectedResultParticipant] = useState(null)
  const [resultForm, setResultForm] = useState({
    position: '',
    score: '',
    points: '',
    medal: '',
    remarks: '',
  })

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [tList, sList, aList] = await Promise.all([
        getTournaments({
          search: search || undefined,
          sport_id: selectedSport || undefined,
          status: selectedStatus || undefined,
        }),
        getSports(),
        getAthletes().catch(() => []),
      ])
      setTournaments(tList)
      setSports(Array.isArray(sList) ? sList : sList.sports || [])
      setAthletes(Array.isArray(aList) ? aList : [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load tournaments.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [search, selectedSport, selectedStatus])

  // Stats calculation
  const totalTournaments = tournaments.length
  const upcomingCount = tournaments.filter((t) => t.status === 'upcoming').length
  const ongoingCount = tournaments.filter((t) => t.status === 'ongoing').length
  const completedCount = tournaments.filter((t) => t.status === 'completed').length

  // Tournament CRUD
  const handleOpenCreateModal = () => {
    setEditingTournament(null)
    setFormData({
      name: '',
      sport_id: sports[0]?._id || sports[0]?.id || '',
      description: '',
      location: '',
      start_date: '',
      end_date: '',
      registration_deadline: '',
      status: 'upcoming',
    })
    setShowTournamentModal(true)
  }

  const handleOpenEditModal = (t) => {
    setEditingTournament(t)
    setFormData({
      name: t.name,
      sport_id: t.sport_id,
      description: t.description || '',
      location: t.location || t.venue || '',
      start_date: t.start_date ? t.start_date.substring(0, 16) : '',
      end_date: t.end_date ? t.end_date.substring(0, 16) : '',
      registration_deadline: t.registration_deadline ? t.registration_deadline.substring(0, 16) : '',
      status: t.status,
    })
    setShowTournamentModal(true)
  }

  const handleSaveTournament = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      const payload = {
        name: formData.name,
        sport_id: formData.sport_id,
        description: formData.description || undefined,
        location: formData.location,
        start_date: new Date(formData.start_date).toISOString(),
        end_date: new Date(formData.end_date).toISOString(),
        registration_deadline: formData.registration_deadline
          ? new Date(formData.registration_deadline).toISOString()
          : undefined,
        status: formData.status,
      }

      if (editingTournament) {
        await updateTournament(editingTournament.id, payload)
        setActionSuccess(`Tournament '${formData.name}' updated successfully.`)
      } else {
        await createTournament(payload)
        setActionSuccess(`Tournament '${formData.name}' created successfully.`)
      }

      setShowTournamentModal(false)
      loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save tournament.')
    }
  }

  const handleDeleteTournament = async (t) => {
    if (!window.confirm(`Are you sure you want to delete tournament '${t.name}'?`)) return
    try {
      await deleteTournament(t.id)
      setActionSuccess('Tournament deleted successfully.')
      loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete tournament.')
    }
  }

  // Participants modal
  const handleOpenParticipants = async (t) => {
    setActiveTournament(t)
    setShowParticipantModal(true)
    setPartLoading(true)
    try {
      const parts = await getParticipants(t.id)
      setParticipants(parts)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load participants.')
    } finally {
      setPartLoading(false)
    }
  }

  const handleAddParticipant = async (e) => {
    e.preventDefault()
    if (!newPartAthleteId || !activeTournament) return
    setError(null)
    try {
      await addParticipant(activeTournament.id, {
        athlete_id: newPartAthleteId,
        event: newPartEvent || undefined,
      })
      setNewPartAthleteId('')
      setNewPartEvent('')
      const parts = await getParticipants(activeTournament.id)
      setParticipants(parts)
      loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to register athlete.')
    }
  }

  const handleRemoveParticipant = async (athleteId) => {
    if (!window.confirm('Withdraw this athlete from the tournament?')) return
    try {
      await removeParticipant(activeTournament.id, athleteId)
      const parts = await getParticipants(activeTournament.id)
      setParticipants(parts)
      loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove participant.')
    }
  }

  // Results modal
  const handleOpenResults = async (t) => {
    setActiveTournament(t)
    setPartLoading(true)
    setShowResultsModal(true)
    try {
      const parts = await getParticipants(t.id)
      setParticipants(parts)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load tournament participants.')
    } finally {
      setPartLoading(false)
    }
  }

  const handleSelectResultForEdit = (p) => {
    setSelectedResultParticipant(p)
    setResultForm({
      position: p.position || '',
      score: p.score || '',
      points: p.points || '',
      medal: p.medal || '',
      remarks: p.remarks || '',
    })
  }

  const handleSaveResult = async (e) => {
    e.preventDefault()
    if (!activeTournament || !selectedResultParticipant) return
    setError(null)
    try {
      const payload = {
        athlete_id: selectedResultParticipant.athlete_id,
        position: resultForm.position ? parseInt(resultForm.position, 10) : undefined,
        score: resultForm.score || undefined,
        points: resultForm.points ? parseFloat(resultForm.points) : undefined,
        medal: resultForm.medal || undefined,
        remarks: resultForm.remarks || undefined,
      }
      await recordResult(activeTournament.id, payload)
      setActionSuccess('Result recorded successfully.')
      setSelectedResultParticipant(null)
      const parts = await getParticipants(activeTournament.id)
      setParticipants(parts)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to record result.')
    }
  }

  return (
    <AppLayout title="Tournaments & Competitions">
      <div className={styles.container}>
        {/* Stat Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <StatCard title="Total Tournaments" value={totalTournaments} icon="🏆" />
          <StatCard title="Upcoming" value={upcomingCount} icon="📅" />
          <StatCard title="Ongoing" value={ongoingCount} icon="⚡" />
          <StatCard title="Completed" value={completedCount} icon="✅" />
        </div>

        {/* Action / Success Banner */}
        {actionSuccess && (
          <div style={{ padding: '10px 16px', backgroundColor: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.3)', color: '#22c55e', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>{actionSuccess}</span>
            <button onClick={() => setActionSuccess(null)} style={{ background: 'none', border: 'none', color: '#22c55e', cursor: 'pointer' }}>✕</button>
          </div>
        )}

        {/* Filter bar */}
        <div className={styles.headerBar}>
          <div className={styles.controls}>
            <input
              type="text"
              placeholder="Search tournament name, venue..."
              className={styles.searchInput}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />

            <select
              className={styles.selectInput}
              value={selectedSport}
              onChange={(e) => setSelectedSport(e.target.value)}
            >
              <option value="">All Sports</option>
              {sports.map((sp) => (
                <option key={sp._id || sp.id} value={sp._id || sp.id}>
                  {sp.name}
                </option>
              ))}
            </select>

            <select
              className={styles.selectInput}
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="upcoming">Upcoming</option>
              <option value="ongoing">Ongoing</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          <button className={styles.primaryBtn} onClick={handleOpenCreateModal}>
            + Create Tournament
          </button>
        </div>

        {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className={styles.tableWrapper}>
            {tournaments.length === 0 ? (
              <div style={{ padding: '48px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                No tournaments found. Create one to get started!
              </div>
            ) : (
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Tournament Name</th>
                    <th>Sport</th>
                    <th>Dates</th>
                    <th>Venue</th>
                    <th>Status</th>
                    <th>Participants</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {tournaments.map((t) => (
                    <tr key={t.id}>
                      <td>
                        <strong>{t.name}</strong>
                        {t.description && (
                          <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                            {t.description}
                          </div>
                        )}
                      </td>
                      <td>
                        <span className={styles.badge} style={{ backgroundColor: 'var(--color-surface-2)', color: 'var(--color-text)' }}>
                          {t.sport_name || 'Sport'}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.85rem' }}>
                        <div>{new Date(t.start_date).toLocaleDateString()}</div>
                        <div style={{ color: 'var(--color-text-muted)' }}>to {new Date(t.end_date).toLocaleDateString()}</div>
                      </td>
                      <td>{t.location || t.venue || 'TBD'}</td>
                      <td>
                        <span
                          className={`${styles.badge} ${
                            t.status === 'upcoming'
                              ? styles.badgeScheduled
                              : t.status === 'ongoing'
                              ? styles.badgeActive
                              : t.status === 'completed'
                              ? styles.badgeCompleted
                              : styles.badgeCancelled
                          }`}
                        >
                          {t.status}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontWeight: 600 }}>{t.participant_count}</span> athletes
                      </td>
                      <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                        <button
                          className={styles.secondaryBtn}
                          style={{ marginRight: '6px', padding: '4px 8px', fontSize: '0.75rem' }}
                          onClick={() => handleOpenParticipants(t)}
                        >
                          👥 Athletes ({t.participant_count})
                        </button>
                        <button
                          className={styles.secondaryBtn}
                          style={{ marginRight: '6px', padding: '4px 8px', fontSize: '0.75rem' }}
                          onClick={() => handleOpenResults(t)}
                        >
                          🏅 Results
                        </button>
                        <button
                          className={styles.secondaryBtn}
                          style={{ marginRight: '6px', padding: '4px 8px', fontSize: '0.75rem' }}
                          onClick={() => handleOpenEditModal(t)}
                        >
                          ✏️ Edit
                        </button>
                        <button
                          className={styles.dangerBtn}
                          onClick={() => handleDeleteTournament(t)}
                        >
                          🗑️
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Create / Edit Tournament Modal */}
        {showTournamentModal && (
          <div className={styles.modalBackdrop}>
            <div className={styles.modal} style={{ maxWidth: '540px' }}>
              <h3 className={styles.modalTitle}>
                {editingTournament ? 'Edit Tournament' : 'Create New Tournament'}
              </h3>
              <form onSubmit={handleSaveTournament}>
                <div className={styles.formGroup}>
                  <label className={styles.label}>Tournament Name *</label>
                  <input
                    type="text"
                    required
                    className={styles.input}
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.label}>Sport *</label>
                  <select
                    className={styles.selectInput}
                    style={{ width: '100%' }}
                    required
                    value={formData.sport_id}
                    onChange={(e) => setFormData({ ...formData, sport_id: e.target.value })}
                  >
                    {sports.map((sp) => (
                      <option key={sp._id || sp.id} value={sp._id || sp.id}>
                        {sp.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.label}>Description</label>
                  <textarea
                    className={styles.input}
                    rows="2"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.label}>Location / Venue *</label>
                  <input
                    type="text"
                    required
                    className={styles.input}
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div className={styles.formGroup}>
                    <label className={styles.label}>Start Date & Time *</label>
                    <input
                      type="datetime-local"
                      required
                      className={styles.input}
                      value={formData.start_date}
                      onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    />
                  </div>
                  <div className={styles.formGroup}>
                    <label className={styles.label}>End Date & Time *</label>
                    <input
                      type="datetime-local"
                      required
                      className={styles.input}
                      value={formData.end_date}
                      onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div className={styles.formGroup}>
                    <label className={styles.label}>Registration Deadline</label>
                    <input
                      type="datetime-local"
                      className={styles.input}
                      value={formData.registration_deadline}
                      onChange={(e) => setFormData({ ...formData, registration_deadline: e.target.value })}
                    />
                  </div>
                  <div className={styles.formGroup}>
                    <label className={styles.label}>Status</label>
                    <select
                      className={styles.selectInput}
                      style={{ width: '100%' }}
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    >
                      <option value="upcoming">Upcoming</option>
                      <option value="ongoing">Ongoing</option>
                      <option value="completed">Completed</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                  </div>
                </div>

                <div className={styles.formActions}>
                  <button type="button" className={styles.secondaryBtn} onClick={() => setShowTournamentModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className={styles.primaryBtn}>
                    {editingTournament ? 'Update Tournament' : 'Create Tournament'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Participants Modal */}
        {showParticipantModal && activeTournament && (
          <div className={styles.modalBackdrop}>
            <div className={styles.modal} style={{ maxWidth: '640px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 className={styles.modalTitle} style={{ margin: 0 }}>
                  Participants: {activeTournament.name}
                </h3>
                <button onClick={() => setShowParticipantModal(false)} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}>✕</button>
              </div>

              {/* Add athlete form */}
              <form onSubmit={handleAddParticipant} style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
                <select
                  required
                  className={styles.selectInput}
                  style={{ flex: 1, minWidth: '180px' }}
                  value={newPartAthleteId}
                  onChange={(e) => setNewPartAthleteId(e.target.value)}
                >
                  <option value="">Select Athlete to Register...</option>
                  {athletes
                    .filter((a) => {
                      const tSp = String(activeTournament.sport_id)
                      const aSp = String(a.sport_id)
                      const extra = (a.additional_sport_ids || []).map(String)
                      const isSportMatch = aSp === tSp || extra.includes(tSp)
                      const alreadyIn = participants.some((p) => p.athlete_id === (a._id || a.id))
                      return isSportMatch && !alreadyIn
                    })
                    .map((a) => (
                      <option key={a._id || a.id} value={a._id || a.id}>
                        {a.full_name} ({a.email})
                      </option>
                    ))}
                </select>

                <input
                  type="text"
                  placeholder="Event / Category (optional)"
                  className={styles.searchInput}
                  style={{ flex: 1, minWidth: '160px' }}
                  value={newPartEvent}
                  onChange={(e) => setNewPartEvent(e.target.value)}
                />

                <button type="submit" className={styles.primaryBtn}>
                  + Register
                </button>
              </form>

              {partLoading ? (
                <LoadingSpinner />
              ) : (
                <div className={styles.tableWrapper} style={{ maxHeight: '350px' }}>
                  {participants.length === 0 ? (
                    <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                      No participants registered yet.
                    </div>
                  ) : (
                    <table className={styles.table}>
                      <thead>
                        <tr>
                          <th>Athlete</th>
                          <th>Event</th>
                          <th>Status</th>
                          <th>Registered</th>
                          <th style={{ textAlign: 'right' }}>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {participants.map((p) => (
                          <tr key={p.id}>
                            <td><strong>{p.athlete_name}</strong></td>
                            <td>{p.event || 'General'}</td>
                            <td>
                              <span className={styles.badge} style={{ backgroundColor: 'var(--color-surface-2)', color: 'var(--color-text)' }}>
                                {p.status}
                              </span>
                            </td>
                            <td style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                              {new Date(p.registered_at).toLocaleDateString()}
                            </td>
                            <td style={{ textAlign: 'right' }}>
                              <button
                                className={styles.dangerBtn}
                                onClick={() => handleRemoveParticipant(p.athlete_id)}
                              >
                                Withdraw
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Results Modal */}
        {showResultsModal && activeTournament && (
          <div className={styles.modalBackdrop}>
            <div className={styles.modal} style={{ maxWidth: '700px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 className={styles.modalTitle} style={{ margin: 0 }}>
                  Tournament Results: {activeTournament.name}
                </h3>
                <button onClick={() => setShowResultsModal(false)} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}>✕</button>
              </div>

              {selectedResultParticipant ? (
                <form onSubmit={handleSaveResult} style={{ backgroundColor: 'var(--color-surface-2)', padding: '16px', borderRadius: 'var(--radius-sm)', marginBottom: '16px' }}>
                  <h4 style={{ margin: '0 0 12px', color: 'var(--color-accent)' }}>
                    Record Result for {selectedResultParticipant.athlete_name}
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                    <div className={styles.formGroup}>
                      <label className={styles.label}>Position / Rank</label>
                      <input
                        type="number"
                        min="1"
                        placeholder="1, 2, 3..."
                        className={styles.input}
                        value={resultForm.position}
                        onChange={(e) => setResultForm({ ...resultForm, position: e.target.value })}
                      />
                    </div>
                    <div className={styles.formGroup}>
                      <label className={styles.label}>Score / Time</label>
                      <input
                        type="text"
                        placeholder="e.g. 3-1, 10.45s"
                        className={styles.input}
                        value={resultForm.score}
                        onChange={(e) => setResultForm({ ...resultForm, score: e.target.value })}
                      />
                    </div>
                    <div className={styles.formGroup}>
                      <label className={styles.label}>Points (Auto if empty)</label>
                      <input
                        type="number"
                        step="0.5"
                        placeholder="e.g. 10.0"
                        className={styles.input}
                        value={resultForm.points}
                        onChange={(e) => setResultForm({ ...resultForm, points: e.target.value })}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '12px' }}>
                    <div className={styles.formGroup}>
                      <label className={styles.label}>Medal (Auto if 1-3)</label>
                      <select
                        className={styles.selectInput}
                        style={{ width: '100%' }}
                        value={resultForm.medal}
                        onChange={(e) => setResultForm({ ...resultForm, medal: e.target.value })}
                      >
                        <option value="">Auto by position</option>
                        <option value="Gold">🥇 Gold</option>
                        <option value="Silver">🥈 Silver</option>
                        <option value="Bronze">🥉 Bronze</option>
                        <option value="None">None</option>
                      </select>
                    </div>
                    <div className={styles.formGroup}>
                      <label className={styles.label}>Remarks</label>
                      <input
                        type="text"
                        placeholder="Performance remarks..."
                        className={styles.input}
                        value={resultForm.remarks}
                        onChange={(e) => setResultForm({ ...resultForm, remarks: e.target.value })}
                      />
                    </div>
                  </div>

                  <div className={styles.formActions}>
                    <button type="button" className={styles.secondaryBtn} onClick={() => setSelectedResultParticipant(null)}>
                      Cancel
                    </button>
                    <button type="submit" className={styles.primaryBtn}>
                      Save Result
                    </button>
                  </div>
                </form>
              ) : null}

              {partLoading ? (
                <LoadingSpinner />
              ) : (
                <div className={styles.tableWrapper} style={{ maxHeight: '350px' }}>
                  {participants.length === 0 ? (
                    <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                      No registered athletes for this tournament.
                    </div>
                  ) : (
                    <table className={styles.table}>
                      <thead>
                        <tr>
                          <th>Athlete</th>
                          <th>Position</th>
                          <th>Medal</th>
                          <th>Score</th>
                          <th>Points</th>
                          <th style={{ textAlign: 'right' }}>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {participants.map((p) => (
                          <tr key={p.id}>
                            <td><strong>{p.athlete_name}</strong></td>
                            <td>{p.position ? `#${p.position}` : '-'}</td>
                            <td>
                              {p.medal === 'Gold' && '🥇 Gold'}
                              {p.medal === 'Silver' && '🥈 Silver'}
                              {p.medal === 'Bronze' && '🥉 Bronze'}
                              {!p.medal && '-'}
                            </td>
                            <td>{p.score || '-'}</td>
                            <td style={{ fontWeight: 600, color: 'var(--color-accent)' }}>
                              {p.points !== null && p.points !== undefined ? `${p.points} pts` : '-'}
                            </td>
                            <td style={{ textAlign: 'right' }}>
                              <button
                                className={styles.secondaryBtn}
                                style={{ padding: '3px 8px', fontSize: '0.75rem' }}
                                onClick={() => handleSelectResultForEdit(p)}
                              >
                                {p.position ? 'Update' : 'Record'}
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
