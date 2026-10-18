import React, { useEffect, useState } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import styles from '../../styles/Management.module.css'
import { getRankings } from '../../services/rankingService'
import { getSports } from '../../services/sportsService'

const TAB_CONFIG = [
  { key: 'tournament', label: '🏆 Tournament Points & Medals', desc: 'Points accumulated across all tournament competitions.' },
  { key: 'performance', label: '⚡ Performance Scores', desc: 'Rankings derived from verified performance assessments.' },
  { key: 'attendance', label: '📅 Attendance Rate', desc: 'Training participation percentage (cancelled sessions excluded).' },
  { key: 'improvement', label: '📈 Improvement', desc: 'Percentage growth between consecutive performance assessments.' },
]

export default function RankingsPage({ role = 'admin' }) {
  const [activeTab, setActiveTab] = useState('tournament')
  const [selectedSport, setSelectedSport] = useState('')
  const [includeZero, setIncludeZero] = useState(true)
  const [sports, setSports] = useState([])
  const [rankingsData, setRankingsData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function loadSports() {
      try {
        const res = await getSports()
        setSports(Array.isArray(res) ? res : res.sports || [])
      } catch (err) {
        console.error('Failed to load sports filter', err)
      }
    }
    loadSports()
  }, [])

  const fetchRankings = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getRankings(activeTab, selectedSport || null, includeZero)
      setRankingsData(data?.items || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load rankings leaderboard.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRankings()
  }, [activeTab, selectedSport, includeZero])

  const renderRankBadge = (rank) => {
    if (rank === 1) return <span style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>🥇 #1</span>
    if (rank === 2) return <span style={{ fontSize: '1.15rem', fontWeight: 'bold' }}>🥈 #2</span>
    if (rank === 3) return <span style={{ fontSize: '1.05rem', fontWeight: 'bold' }}>🥉 #3</span>
    return <span style={{ fontWeight: 600, color: 'var(--color-text-muted)' }}>#{rank}</span>
  }

  return (
    <AppLayout title="Academy Rankings & Leaderboards">
      <div className={styles.container}>
        {/* Header bar with filters */}
        <div className={styles.headerBar}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.25rem', color: 'var(--color-text)' }}>
              Athletix Leaderboard
            </h2>
            <p style={{ margin: '4px 0 0', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
              {TAB_CONFIG.find((t) => t.key === activeTab)?.desc}
            </p>
          </div>

          <div className={styles.controls} style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.875rem', color: 'var(--color-text-muted)', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={includeZero}
                onChange={(e) => setIncludeZero(e.target.checked)}
              />
              Include zero-activity athletes
            </label>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <label style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Sport:</label>
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
            </div>
          </div>
        </div>

        {/* Tab Selection */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
          {TAB_CONFIG.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                padding: '8px 16px',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.875rem',
                backgroundColor: activeTab === tab.key ? 'var(--color-accent)' : 'var(--color-surface-2)',
                color: activeTab === tab.key ? '#0f1117' : 'var(--color-text)',
                transition: 'all 0.2s ease',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tie-breaking footnote info */}
        <div style={{ padding: '8px 14px', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
          ℹ️ <strong>Tie-handling rule:</strong>{' '}
          {activeTab === 'tournament' && 'Ranked by Points (desc), Gold (desc), Silver (desc), Bronze (desc), Tournaments Played (desc), then Athlete name.'}
          {activeTab === 'performance' && 'Ranked by Assessment Score (desc), then Athlete name. Athletes without assessments are displayed with "Unassessed" status.'}
          {activeTab === 'attendance' && 'Ranked by Attendance Rate (desc), Total Sessions (desc), then Athlete name. Zero-session athletes show "—".'}
          {activeTab === 'improvement' && 'Ranked by Improvement % (desc), then Athlete name (requires ≥ 2 assessments to calculate).'}
        </div>

        {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className={styles.tableWrapper}>
            {rankingsData.length === 0 ? (
              <div style={{ padding: '48px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                No rankings data available for this category yet.
              </div>
            ) : (
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th style={{ width: '80px' }}>Rank</th>
                    <th>Athlete</th>
                    <th>Sport</th>
                    {activeTab === 'tournament' && (
                      <>
                        <th style={{ textAlign: 'right' }}>Points</th>
                        <th style={{ textAlign: 'center' }}>🥇 Gold</th>
                        <th style={{ textAlign: 'center' }}>🥈 Silver</th>
                        <th style={{ textAlign: 'center' }}>🥉 Bronze</th>
                        <th style={{ textAlign: 'center' }}>Total Medals</th>
                        <th style={{ textAlign: 'right' }}>Tournaments</th>
                      </>
                    )}
                    {activeTab === 'performance' && (
                      <>
                        <th style={{ textAlign: 'right' }}>Overall Score</th>
                        <th>Assessment Date</th>
                      </>
                    )}
                    {activeTab === 'attendance' && (
                      <>
                        <th style={{ textAlign: 'right' }}>Attendance Rate</th>
                        <th style={{ textAlign: 'center' }}>Attended Sessions</th>
                        <th style={{ textAlign: 'center' }}>Total Applicable</th>
                      </>
                    )}
                    {activeTab === 'improvement' && (
                      <>
                        <th style={{ textAlign: 'right' }}>Improvement %</th>
                        <th style={{ textAlign: 'right' }}>Current Score</th>
                        <th style={{ textAlign: 'right' }}>Previous Score</th>
                      </>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {rankingsData.map((item) => (
                    <tr
                      key={item.athlete_id}
                      style={{
                        backgroundColor:
                          item.rank === 1
                            ? 'rgba(234, 179, 8, 0.05)'
                            : item.rank === 2
                            ? 'rgba(148, 163, 184, 0.05)'
                            : item.rank === 3
                            ? 'rgba(217, 119, 6, 0.05)'
                            : 'transparent',
                      }}
                    >
                      <td>{renderRankBadge(item.rank)}</td>
                      <td>
                        <strong>{item.athlete_name}</strong>
                      </td>
                      <td>
                        <span className={styles.badge} style={{ backgroundColor: 'var(--color-surface-2)', color: 'var(--color-text)' }}>
                          {item.sport_name || 'All'}
                        </span>
                      </td>

                      {activeTab === 'tournament' && (
                        <>
                          <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--color-accent)' }}>
                            {item.points} pts
                          </td>
                          <td style={{ textAlign: 'center' }}>{item.gold_count}</td>
                          <td style={{ textAlign: 'center' }}>{item.silver_count}</td>
                          <td style={{ textAlign: 'center' }}>{item.bronze_count}</td>
                          <td style={{ textAlign: 'center', fontWeight: 600 }}>{item.total_medals}</td>
                          <td style={{ textAlign: 'right' }}>{item.tournaments_played}</td>
                        </>
                      )}

                      {activeTab === 'performance' && (
                        <>
                          <td style={{ textAlign: 'right', fontWeight: 700, color: item.performance_score != null ? 'var(--color-accent)' : 'var(--color-text-muted)' }}>
                            {item.performance_score != null ? `${item.performance_score} / 100` : <span style={{ fontStyle: 'italic', fontWeight: 400 }}>Unassessed</span>}
                          </td>
                          <td style={{ color: item.assessment_date ? 'inherit' : 'var(--color-text-muted)' }}>
                            {item.assessment_date ? new Date(item.assessment_date).toLocaleDateString() : '—'}
                          </td>
                        </>
                      )}

                      {activeTab === 'attendance' && (
                        <>
                          <td style={{ textAlign: 'right', fontWeight: 700, color: item.total_sessions === 0 ? 'var(--color-text-muted)' : item.attendance_percentage >= 75 ? '#22c55e' : '#ef4444' }}>
                            {item.total_sessions === 0 ? '—' : `${item.attendance_percentage}%`}
                          </td>
                          <td style={{ textAlign: 'center' }}>{item.attended_sessions}</td>
                          <td style={{ textAlign: 'center' }}>{item.total_sessions}</td>
                        </>
                      )}

                      {activeTab === 'improvement' && (
                        <>
                          <td style={{ textAlign: 'right', fontWeight: 700, color: item.improvement_percentage >= 0 ? '#22c55e' : '#ef4444' }}>
                            {item.improvement_percentage >= 0 ? `+${item.improvement_percentage}%` : `${item.improvement_percentage}%`}
                          </td>
                          <td style={{ textAlign: 'right' }}>{item.current_score}</td>
                          <td style={{ textAlign: 'right' }}>{item.previous_score}</td>
                        </>
                      )}
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
