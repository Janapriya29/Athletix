import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import StatCard from '../../components/common/StatCard'
import SportsBanner from '../../components/common/SportsBanner'
import styles from '../../styles/Management.module.css'
import {
  getTournaments,
  getParticipants,
  addParticipant,
  removeParticipant,
  recordResult,
} from '../../services/tournamentService'
import { getSports } from '../../services/sportsService'
import { getAthletes } from '../../services/athletesService'

export default function CoachTournamentsPage() {
  const [tournaments, setTournaments] = useState([])
  const [sports, setSports] = useState([])
  const [myAthletes, setMyAthletes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actionSuccess, setActionSuccess] = useState(null)

  // Filters
  const [search, setSearch] = useState('')
  const [selectedSport, setSelectedSport] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('')

  // Modals
  const [activeTournament, setActiveTournament] = useState(null)
  const [showRegisterModal, setShowRegisterModal] = useState(false)
  const [showResultsModal, setShowResultsModal] = useState(false)
  const [participants, setParticipants] = useState([])
  const [partLoading, setPartLoading] = useState(false)

  // Registration Form
  const [registerAthleteId, setRegisterAthleteId] = useState('')
  const [registerEvent, setRegisterEvent] = useState('')

  // Result Form
  const [selectedResultPart, setSelectedResultPart] = useState(null)
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
      setMyAthletes(Array.isArray(aList) ? aList : [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load tournaments.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [search, selectedSport, selectedStatus])

  // Open athlete registration modal
  const handleOpenRegister = async (t) => {
    setActiveTournament(t)
    setShowRegisterModal(true)
    setPartLoading(true)
    try {
      const parts = await getParticipants(t.id)
      setParticipants(parts)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load tournament participants.')
    } finally {
      setPartLoading(false)
    }
  }

  const handleRegisterAthlete = async (e) => {
    e.preventDefault()
    if (!registerAthleteId || !activeTournament) return
    setError(null)
    try {
      await addParticipant(activeTournament.id, {
        athlete_id: registerAthleteId,
        event: registerEvent || undefined,
      })
      setActionSuccess('Athlete registered successfully for tournament.')
      setRegisterAthleteId('')
      setRegisterEvent('')
      const parts = await getParticipants(activeTournament.id)
      setParticipants(parts)
      loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to register athlete.')
    }
  }

  const handleWithdrawAthlete = async (athId) => {
    if (!window.confirm('Withdraw this athlete from the tournament?')) return
    try {
      await removeParticipant(activeTournament.id, athId)
      setActionSuccess('Athlete withdrawn successfully.')
      const parts = await getParticipants(activeTournament.id)
      setParticipants(parts)
      loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to withdraw athlete.')
    }
  }

  // Open results recording modal
  const handleOpenResults = async (t) => {
    setActiveTournament(t)
    setShowResultsModal(true)
    setPartLoading(true)
    try {
      const parts = await getParticipants(t.id)
      setParticipants(parts)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load tournament results.')
    } finally {
      setPartLoading(false)
    }
  }

  const computeDefaultPoints = (pos, medal) => {
    const p = parseInt(pos, 10)
    const m = (medal || '').trim().toLowerCase()
    if (p === 1 || m === 'gold') return 10.0
    if (p === 2 || m === 'silver') return 7.0
    if (p === 3 || m === 'bronze') return 5.0
    if (!isNaN(p) && p >= 4 && p <= 10) return Math.max(1, 11 - p)
    return null
  }

  const handleSelectResultForEdit = (p) => {
    setSelectedResultPart(p)
    const existingPts = p.points !== null && p.points !== undefined ? String(p.points) : ''
    setResultForm({
      position: p.position || '',
      score: p.score || '',
      points: existingPts,
      medal: p.medal || '',
      remarks: p.remarks || '',
      isCustomPoints: Boolean(existingPts),
    })
  }

  const handlePositionChange = (val) => {
    const p = parseInt(val, 10)
    let newMedal = resultForm.medal
    if (!resultForm.medal || resultForm.medal === 'None') {
      if (p === 1) newMedal = 'Gold'
      else if (p === 2) newMedal = 'Silver'
      else if (p === 3) newMedal = 'Bronze'
    }
    const autoPts = computeDefaultPoints(val, newMedal)
    setResultForm((prev) => ({
      ...prev,
      position: val,
      medal: newMedal,
      points: !prev.isCustomPoints ? (autoPts !== null ? String(autoPts) : '') : prev.points,
    }))
  }

  const handleMedalChange = (val) => {
    const autoPts = computeDefaultPoints(resultForm.position, val)
    setResultForm((prev) => ({
      ...prev,
      medal: val,
      points: !prev.isCustomPoints ? (autoPts !== null ? String(autoPts) : '') : prev.points,
    }))
  }

  const handleSaveResult = async (e) => {
    e.preventDefault()
    if (!activeTournament || !selectedResultPart) return
    setError(null)
    try {
      const payload = {
        athlete_id: selectedResultPart.athlete_id,
        position: resultForm.position ? parseInt(resultForm.position, 10) : undefined,
        score: resultForm.score || undefined,
        points: resultForm.points ? parseFloat(resultForm.points) : undefined,
        medal: resultForm.medal || undefined,
        remarks: resultForm.remarks || undefined,
      }
      await recordResult(activeTournament.id, payload)
      setActionSuccess('Result recorded successfully.')
      setSelectedResultPart(null)
      const parts = await getParticipants(activeTournament.id)
      setParticipants(parts)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to record result.')
    }
  }

  // Check if participant is coach's assigned athlete
  const myAthleteIds = new Set(myAthletes.map((a) => a._id || a.id))

  return (
    <AppLayout title="Coach Tournaments">
      <div className={styles.container}>
        {/* Tournament Championship Hero Banner */}
        <SportsBanner
          image="/images/tournament_championship_arena.jpg"
          alt="Tournament Championship Arena"
          badge="COACH TOURNAMENT SQUAD"
          title="Squad Tournaments & Competitions"
          subtitle="Register assigned athletes for upcoming fixtures, track live brackets, and submit results"
          metrics={[
            { label: 'Available Tournaments', value: tournaments.length },
            { label: 'My Assigned Athletes', value: myAthletes.length },
            { label: 'Active / Ongoing', value: tournaments.filter((t) => t.status === 'ongoing').length },
          ]}
        />

        {/* Stat Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <StatCard title="Available Tournaments" value={tournaments.length} icon="🏆" />
          <StatCard title="My Assigned Athletes" value={myAthletes.length} icon="🏃" />
          <StatCard
            title="Active / Ongoing"
            value={tournaments.filter((t) => t.status === 'ongoing').length}
            icon="⚡"
          />
        </div>

        {actionSuccess && (
          <div style={{ padding: '10px 16px', backgroundColor: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.3)', color: '#22c55e', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>{actionSuccess}</span>
            <button onClick={() => setActionSuccess(null)} style={{ background: 'none', border: 'none', color: '#22c55e', cursor: 'pointer' }}>✕</button>
          </div>
        )}

        {/* Filters */}
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
            </select>
          </div>
        </div>

        {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className={styles.tableWrapper}>
            {tournaments.length === 0 ? (
              <div style={{ padding: '48px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                No tournaments found matching the filters.
              </div>
            ) : (
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Tournament</th>
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
                      <td>{t.participant_count} athletes</td>
                      <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                        {t.status !== 'cancelled' && (
                          <button
                            className={styles.primaryBtn}
                            style={{ marginRight: '6px', padding: '4px 10px', fontSize: '0.75rem' }}
                            onClick={() => handleOpenRegister(t)}
                          >
                            + Register Athletes
                          </button>
                        )}
                        <button
                          className={styles.secondaryBtn}
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          onClick={() => handleOpenResults(t)}
                        >
                          🏅 Results
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Register Athletes Modal */}
        {showRegisterModal && activeTournament && (
          <div className={styles.modalBackdrop}>
            <div className={styles.modal} style={{ maxWidth: '640px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 className={styles.modalTitle} style={{ margin: 0 }}>
                  Register Assigned Athletes: {activeTournament.name}
                </h3>
                <button onClick={() => setShowRegisterModal(false)} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}>✕</button>
              </div>

              {(() => {
                const tSp = String(activeTournament.sport_id || '')
                const sportMatchingAthletes = myAthletes.filter((a) => {
                  const aSp = String(a.sport_id || '')
                  const extra = (a.additional_sport_ids || []).map(String)
                  return Boolean(tSp && (aSp === tSp || extra.includes(tSp)))
                })
                const eligibleAthletes = sportMatchingAthletes.filter((a) => {
                  const aId = String(a._id || a.id || '')
                  return !participants.some((p) => String(p.athlete_id) === aId)
                })
                const hasNoAssigned = myAthletes.length === 0
                const noMatchingSport = !hasNoAssigned && sportMatchingAthletes.length === 0
                const allAlreadyRegistered = !hasNoAssigned && !noMatchingSport && eligibleAthletes.length === 0

                return (
                  <div>
                    {hasNoAssigned && (
                      <div
                        style={{
                          padding: '10px 14px',
                          marginBottom: '12px',
                          borderRadius: 'var(--radius-sm, 6px)',
                          backgroundColor: 'rgba(234, 179, 8, 0.1)',
                          border: '1px solid rgba(234, 179, 8, 0.3)',
                          color: '#eab308',
                          fontSize: '0.85rem',
                        }}
                      >
                        ⚠️ You currently have no athletes assigned to you.
                      </div>
                    )}
                    {noMatchingSport && (
                      <div
                        style={{
                          padding: '10px 14px',
                          marginBottom: '12px',
                          borderRadius: 'var(--radius-sm, 6px)',
                          backgroundColor: 'rgba(234, 179, 8, 0.1)',
                          border: '1px solid rgba(234, 179, 8, 0.3)',
                          color: '#eab308',
                          fontSize: '0.85rem',
                        }}
                      >
                        ⚠️ None of your assigned athletes have {activeTournament.sport_name || 'this sport'} assigned as their primary or additional sport.
                      </div>
                    )}
                    {allAlreadyRegistered && (
                      <div
                        style={{
                          padding: '10px 14px',
                          marginBottom: '12px',
                          borderRadius: 'var(--radius-sm, 6px)',
                          backgroundColor: 'rgba(56, 189, 248, 0.1)',
                          border: '1px solid rgba(56, 189, 248, 0.3)',
                          color: '#38bdf8',
                          fontSize: '0.85rem',
                        }}
                      >
                        ℹ️ All of your eligible assigned athletes ({sportMatchingAthletes.length}) are already registered for this tournament.
                      </div>
                    )}
                    <form onSubmit={handleRegisterAthlete} style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
                      <select
                        required
                        className={styles.selectInput}
                        style={{ flex: 1, minWidth: '180px' }}
                        value={registerAthleteId}
                        onChange={(e) => setRegisterAthleteId(e.target.value)}
                        disabled={eligibleAthletes.length === 0}
                      >
                        <option value="">
                          {eligibleAthletes.length === 0
                            ? (hasNoAssigned
                                ? 'No assigned athletes'
                                : noMatchingSport
                                ? 'No assigned athletes for this sport'
                                : 'All eligible athletes registered')
                            : 'Select Assigned Athlete...'}
                        </option>
                        {eligibleAthletes.map((a) => (
                          <option key={a._id || a.id} value={a._id || a.id}>
                            {a.full_name} ({a.email})
                          </option>
                        ))}
                      </select>

                      <input
                        type="text"
                        placeholder="Event / Category"
                        className={styles.searchInput}
                        style={{ flex: 1, minWidth: '150px' }}
                        value={registerEvent}
                        onChange={(e) => setRegisterEvent(e.target.value)}
                        disabled={eligibleAthletes.length === 0}
                      />

                      <button
                        type="submit"
                        className={styles.primaryBtn}
                        disabled={eligibleAthletes.length === 0 || !registerAthleteId}
                      >
                        Register
                      </button>
                    </form>
                  </div>
                )
              })()}

              {partLoading ? (
                <LoadingSpinner />
              ) : (
                <div className={styles.tableWrapper} style={{ maxHeight: '300px' }}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>Athlete</th>
                        <th>Event</th>
                        <th>Status</th>
                        <th style={{ textAlign: 'right' }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {participants.map((p) => {
                        const isMine = myAthleteIds.has(p.athlete_id)
                        return (
                          <tr key={p.id}>
                            <td>
                              <strong>{p.athlete_name}</strong>
                              {isMine && <span style={{ marginLeft: '6px', fontSize: '0.75rem', color: 'var(--color-accent)' }}>★ Assigned</span>}
                            </td>
                            <td>{p.event || 'General'}</td>
                            <td>
                              <span className={styles.badge} style={{ backgroundColor: 'var(--color-surface-2)', color: 'var(--color-text)' }}>
                                {p.status}
                              </span>
                            </td>
                            <td style={{ textAlign: 'right' }}>
                              {isMine ? (
                                <button
                                  className={styles.dangerBtn}
                                  onClick={() => handleWithdrawAthlete(p.athlete_id)}
                                >
                                  Withdraw
                                </button>
                              ) : (
                                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Other Coach</span>
                              )}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Record Results Modal */}
        {showResultsModal && activeTournament && (
          <div className={styles.modalBackdrop}>
            <div className={styles.modal} style={{ maxWidth: '680px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 className={styles.modalTitle} style={{ margin: 0 }}>
                  Tournament Results: {activeTournament.name}
                </h3>
                <button onClick={() => setShowResultsModal(false)} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}>✕</button>
              </div>

              {selectedResultPart && (
                <form onSubmit={handleSaveResult} style={{ backgroundColor: 'var(--color-surface-2)', padding: '16px', borderRadius: 'var(--radius-sm)', marginBottom: '16px' }}>
                  <h4 style={{ margin: '0 0 12px', color: 'var(--color-accent)' }}>
                    Record Result for {selectedResultPart.athlete_name}
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
                        onChange={(e) => handlePositionChange(e.target.value)}
                      />
                    </div>
                    <div className={styles.formGroup}>
                      <label className={styles.label}>Score / Time</label>
                      <input
                        type="text"
                        placeholder="e.g. 21-18, 21-19"
                        className={styles.input}
                        value={resultForm.score}
                        onChange={(e) => setResultForm({ ...resultForm, score: e.target.value })}
                      />
                    </div>
                    <div className={styles.formGroup}>
                      <label className={styles.label}>
                        Points {computeDefaultPoints(resultForm.position, resultForm.medal) !== null && (
                          <span style={{ color: 'var(--color-accent)', fontSize: '0.75rem', fontWeight: 'normal' }}>
                            (Auto: {computeDefaultPoints(resultForm.position, resultForm.medal)} pts)
                          </span>
                        )}
                      </label>
                      <input
                        type="number"
                        step="0.5"
                        placeholder={computeDefaultPoints(resultForm.position, resultForm.medal) !== null ? `Auto: ${computeDefaultPoints(resultForm.position, resultForm.medal)}` : 'Auto if empty'}
                        className={styles.input}
                        value={resultForm.points}
                        onChange={(e) => setResultForm({ ...resultForm, points: e.target.value, isCustomPoints: true })}
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
                        onChange={(e) => handleMedalChange(e.target.value)}
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
                        placeholder="Performance notes..."
                        className={styles.input}
                        value={resultForm.remarks}
                        onChange={(e) => setResultForm({ ...resultForm, remarks: e.target.value })}
                      />
                    </div>
                  </div>

                  <div className={styles.formActions}>
                    <button type="button" className={styles.secondaryBtn} onClick={() => setSelectedResultPart(null)}>
                      Cancel
                    </button>
                    <button type="submit" className={styles.primaryBtn}>
                      Save Result
                    </button>
                  </div>
                </form>
              )}

              <div className={styles.tableWrapper} style={{ maxHeight: '320px' }}>
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
                    {participants.map((p) => {
                      const isMine = myAthleteIds.has(p.athlete_id)
                      return (
                        <tr key={p.id}>
                          <td>
                            <strong>{p.athlete_name}</strong>
                            {isMine && <span style={{ marginLeft: '6px', fontSize: '0.75rem', color: 'var(--color-accent)' }}>★ Assigned</span>}
                          </td>
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
                            {isMine ? (
                              <button
                                className={styles.secondaryBtn}
                                style={{ padding: '3px 8px', fontSize: '0.75rem' }}
                                onClick={() => handleSelectResultForEdit(p)}
                              >
                                {p.position ? 'Update' : 'Record'}
                              </button>
                            ) : (
                              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Restricted</span>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
