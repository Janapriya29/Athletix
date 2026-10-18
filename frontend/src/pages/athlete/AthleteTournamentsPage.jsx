import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import StatCard from '../../components/common/StatCard'
import SportsBanner from '../../components/common/SportsBanner'
import styles from '../../styles/Management.module.css'
import {
  getTournaments,
  getMyTournamentHistory,
  addParticipant,
  removeParticipant,
} from '../../services/tournamentService'
import { useAuth } from '../../context/AuthContext'
import { getMyAthleteProfile } from '../../services/athletesService'

export default function AthleteTournamentsPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('upcoming') // 'upcoming' | 'history'
  const [tournaments, setTournaments] = useState([])
  const [history, setHistory] = useState([])
  const [myAthlete, setMyAthlete] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actionSuccess, setActionSuccess] = useState(null)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [tList, hList, meProfile] = await Promise.all([
        getTournaments(),
        getMyTournamentHistory().catch(() => []),
        getMyAthleteProfile().catch(() => null),
      ])
      setTournaments(tList)
      setHistory(hList)
      setMyAthlete(meProfile)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load tournament data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Self registration for upcoming tournament
  const handleRegisterSelf = async (tourney) => {
    if (!myAthlete) {
      setError('Athlete profile not found.')
      return
    }
    setError(null)
    try {
      await addParticipant(tourney.id, {
        athlete_id: myAthlete._id || myAthlete.id,
      })
      setActionSuccess(`Successfully registered for ${tourney.name}!`)
      loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to register for tournament.')
    }
  }

  const handleWithdrawSelf = async (tourney) => {
    if (!myAthlete) return
    if (!window.confirm(`Withdraw registration from ${tourney.name}?`)) return
    setError(null)
    try {
      await removeParticipant(tourney.id, myAthlete._id || myAthlete.id)
      setActionSuccess(`Withdrew registration from ${tourney.name}.`)
      loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to withdraw registration.')
    }
  }

  // Personal statistics
  const totalPlayed = history.filter((h) => h.participation_status === 'participated' || h.position).length
  const totalPoints = history.reduce((acc, h) => acc + (h.points || 0), 0)
  const goldCount = history.filter((h) => h.medal === 'Gold' || h.position === 1).length
  const silverCount = history.filter((h) => h.medal === 'Silver' || h.position === 2).length
  const bronzeCount = history.filter((h) => h.medal === 'Bronze' || h.position === 3).length

  // Set of tournament IDs where athlete is registered
  const registeredTournamentIds = new Set(history.map((h) => h.tournament_id))

  return (
    <AppLayout title="Tournaments & Competitions">
      <div className={styles.container}>
        {/* Tournament Championship Hero Banner */}
        <SportsBanner
          image="/images/tournament_championship_arena.jpg"
          alt="Tournament Championship Arena"
          badge="ATHLETE COMPETITIONS"
          title="Tournaments & Fixtures"
          subtitle="Explore upcoming tournaments, register for academy fixtures, and view your career medal haul"
          metrics={[
            { label: 'Competitions', value: totalPlayed },
            { label: 'Total Points', value: `${totalPoints} pts` },
            { label: 'Medal Count', value: goldCount + silverCount + bronzeCount },
          ]}
        />

        {/* Personal Tournament Performance Summary */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
          <StatCard title="Competitions" value={totalPlayed} icon="🏃" />
          <StatCard title="Total Points" value={`${totalPoints} pts`} icon="⚡" />
          <StatCard title="Gold Medals" value={goldCount} icon="🥇" />
          <StatCard title="Silver Medals" value={silverCount} icon="🥈" />
          <StatCard title="Bronze Medals" value={bronzeCount} icon="🥉" />
        </div>

        {actionSuccess && (
          <div style={{ padding: '10px 16px', backgroundColor: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.3)', color: '#22c55e', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>{actionSuccess}</span>
            <button onClick={() => setActionSuccess(null)} style={{ background: 'none', border: 'none', color: '#22c55e', cursor: 'pointer' }}>✕</button>
          </div>
        )}

        {/* Tab switch */}
        <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
          <button
            onClick={() => setActiveTab('upcoming')}
            style={{
              padding: '8px 16px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.875rem',
              backgroundColor: activeTab === 'upcoming' ? 'var(--color-accent)' : 'var(--color-surface-2)',
              color: activeTab === 'upcoming' ? '#0f1117' : 'var(--color-text)',
            }}
          >
            📅 Upcoming & Open Tournaments
          </button>
          <button
            onClick={() => setActiveTab('history')}
            style={{
              padding: '8px 16px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.875rem',
              backgroundColor: activeTab === 'history' ? 'var(--color-accent)' : 'var(--color-surface-2)',
              color: activeTab === 'history' ? '#0f1117' : 'var(--color-text)',
            }}
          >
            🏅 My History & Results
          </button>
        </div>

        {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

        {loading ? (
          <LoadingSpinner />
        ) : activeTab === 'upcoming' ? (
          <div className={styles.tableWrapper}>
            {tournaments.length === 0 ? (
              <div style={{ padding: '48px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                No tournaments scheduled at the moment. Check back soon!
              </div>
            ) : (
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Tournament</th>
                    <th>Sport</th>
                    <th>Dates</th>
                    <th>Venue</th>
                    <th>Registration Deadline</th>
                    <th>Status</th>
                    <th style={{ textAlign: 'right' }}>Registration</th>
                  </tr>
                </thead>
                <tbody>
                  {tournaments.map((t) => {
                    const isRegistered = registeredTournamentIds.has(t.id)
                    const deadlinePassed = t.registration_deadline && new Date(t.registration_deadline) < new Date()
                    const isSportEligible = myAthlete && (
                      String(myAthlete.sport_id) === String(t.sport_id) ||
                      (myAthlete.additional_sport_ids || []).map(String).includes(String(t.sport_id))
                    )

                    return (
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
                        <td style={{ fontSize: '0.85rem' }}>
                          {t.registration_deadline ? new Date(t.registration_deadline).toLocaleDateString() : 'Until Start'}
                        </td>
                        <td>
                          <span
                            className={`${styles.badge} ${
                              t.status === 'upcoming'
                                ? styles.badgeScheduled
                                : t.status === 'ongoing'
                                ? styles.badgeActive
                                : styles.badgeCompleted
                            }`}
                          >
                            {t.status}
                          </span>
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          {isRegistered ? (
                            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ color: '#22c55e', fontWeight: 600, fontSize: '0.8rem' }}>✓ Registered</span>
                              {t.status === 'upcoming' && (
                                <button
                                  className={styles.dangerBtn}
                                  onClick={() => handleWithdrawSelf(t)}
                                >
                                  Withdraw
                                </button>
                              )}
                            </div>
                          ) : t.status === 'upcoming' && !deadlinePassed ? (
                            isSportEligible ? (
                              <button
                                className={styles.primaryBtn}
                                style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                                onClick={() => handleRegisterSelf(t)}
                              >
                                Register Now
                              </button>
                            ) : (
                              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Different Sport</span>
                            )
                          ) : (
                            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Closed</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        ) : (
          <div className={styles.tableWrapper}>
            {history.length === 0 ? (
              <div style={{ padding: '48px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                You have not participated in any tournaments yet.
              </div>
            ) : (
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Tournament</th>
                    <th>Sport</th>
                    <th>Date</th>
                    <th>Event</th>
                    <th>Status</th>
                    <th>Position / Medal</th>
                    <th>Score</th>
                    <th style={{ textAlign: 'right' }}>Points</th>
                    <th>Remarks</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h, idx) => (
                    <tr key={idx}>
                      <td>
                        <strong>{h.tournament_name}</strong>
                        {h.location && (
                          <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                            📍 {h.location}
                          </div>
                        )}
                      </td>
                      <td>
                        <span className={styles.badge} style={{ backgroundColor: 'var(--color-surface-2)', color: 'var(--color-text)' }}>
                          {h.sport_name || 'Sport'}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.85rem' }}>
                        {new Date(h.start_date).toLocaleDateString()}
                      </td>
                      <td>{h.event || 'General'}</td>
                      <td>
                        <span className={styles.badge} style={{ backgroundColor: 'var(--color-surface-2)', color: 'var(--color-text)' }}>
                          {h.participation_status}
                        </span>
                      </td>
                      <td>
                        {h.position && (
                          <span style={{ fontWeight: 600, marginRight: '6px' }}>#{h.position}</span>
                        )}
                        {h.medal === 'Gold' && '🥇 Gold'}
                        {h.medal === 'Silver' && '🥈 Silver'}
                        {h.medal === 'Bronze' && '🥉 Bronze'}
                        {!h.medal && !h.position && '-'}
                      </td>
                      <td>{h.score || '-'}</td>
                      <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--color-accent)' }}>
                        {h.points !== null && h.points !== undefined ? `${h.points} pts` : '-'}
                      </td>
                      <td style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                        {h.remarks || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
