import React, { useState, useEffect } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import reportService from '../../services/reportService'
import { getAthletes } from '../../services/athletesService'
import styles from '../../styles/Management.module.css'

export default function CoachReportsPage() {
  const [activeTab, setActiveTab] = useState('attendance') // 'attendance' | 'tournaments' | 'athlete'
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Assigned athletes list
  const [athletesList, setAthletesList] = useState([])
  const [selectedAthleteId, setSelectedAthleteId] = useState('')

  // Reports data
  const [attendanceItems, setAttendanceItems] = useState([])
  const [tournamentItems, setTournamentItems] = useState([])
  const [devSummary, setDevSummary] = useState(null)
  const [tabLoading, setTabLoading] = useState(false)

  useEffect(() => {
    async function init() {
      try {
        setLoading(true)
        const [attData, athsData] = await Promise.all([
          reportService.getAcademyAttendanceReport(),
          getAthletes().catch(() => []),
        ])
        setAttendanceItems(attData || [])
        setAthletesList(athsData || [])
        if (athsData && athsData.length > 0) {
          setSelectedAthleteId(athsData[0].id)
        }
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load reports')
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  useEffect(() => {
    if (activeTab === 'tournaments') {
      async function loadTournaments() {
        try {
          setTabLoading(true)
          const data = await reportService.getAcademyTournamentsReport()
          setTournamentItems(data || [])
        } catch (err) {
          setError(err.response?.data?.detail || 'Failed to load tournaments report')
        } finally {
          setTabLoading(false)
        }
      }
      loadTournaments()
    }
  }, [activeTab])

  useEffect(() => {
    if (activeTab === 'athlete' && selectedAthleteId) {
      async function loadAthleteDev() {
        try {
          setTabLoading(true)
          const data = await reportService.getAthleteDevelopmentSummary(selectedAthleteId)
          setDevSummary(data)
        } catch (err) {
          setError(err.response?.data?.detail || 'Failed to load athlete profile')
        } finally {
          setTabLoading(false)
        }
      }
      loadAthleteDev()
    }
  }, [activeTab, selectedAthleteId])

  async function handleExportAttendance() {
    try {
      await reportService.downloadAttendanceReportCsv()
    } catch {
      setError('Failed to download CSV export')
    }
  }

  async function handleExportTournaments() {
    try {
      await reportService.downloadTournamentsReportCsv()
    } catch {
      setError('Failed to download CSV export')
    }
  }

  return (
    <AppLayout title="Coach Reports">
      <div className={styles.container}>
        {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

        {/* Tab Controls */}
        <div className={styles.headerBar}>
          <div className={styles.controls}>
            <button
              className={activeTab === 'attendance' ? styles.primaryBtn : styles.secondaryBtn}
              onClick={() => setActiveTab('attendance')}
            >
              📋 Athletes Attendance
            </button>
            <button
              className={activeTab === 'tournaments' ? styles.primaryBtn : styles.secondaryBtn}
              onClick={() => setActiveTab('tournaments')}
            >
              🏆 Tournaments
            </button>
            <button
              className={activeTab === 'athlete' ? styles.primaryBtn : styles.secondaryBtn}
              onClick={() => setActiveTab('athlete')}
            >
              👤 Athlete Development Profile
            </button>
          </div>

          <div className={styles.controls}>
            {activeTab === 'attendance' && (
              <button className={styles.primaryBtn} onClick={handleExportAttendance}>
                📥 Export Attendance CSV
              </button>
            )}
            {activeTab === 'tournaments' && (
              <button className={styles.primaryBtn} onClick={handleExportTournaments}>
                📥 Export Tournaments CSV
              </button>
            )}
          </div>
        </div>

        {/* Attendance Tab */}
        {activeTab === 'attendance' && (
          loading ? (
            <LoadingSpinner />
          ) : (
            <div className={styles.tableCard || styles.headerBar} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                      <th style={{ padding: '12px 16px' }}>Athlete</th>
                      <th style={{ padding: '12px 16px' }}>Sport</th>
                      <th style={{ padding: '12px 16px' }}>Total Sessions</th>
                      <th style={{ padding: '12px 16px' }}>Attended</th>
                      <th style={{ padding: '12px 16px' }}>Attendance Rate</th>
                      <th style={{ padding: '12px 16px' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attendanceItems.length === 0 ? (
                      <tr>
                        <td colSpan="6" style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                          No attendance records found for your athletes.
                        </td>
                      </tr>
                    ) : (
                      attendanceItems.map((item) => (
                        <tr key={item.athlete_id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td style={{ padding: '12px 16px', fontWeight: 600 }}>{item.athlete_name}</td>
                          <td style={{ padding: '12px 16px' }}>{item.sport_name || 'N/A'}</td>
                          <td style={{ padding: '12px 16px' }}>{item.total_sessions}</td>
                          <td style={{ padding: '12px 16px' }}>{item.attended_sessions}</td>
                          <td style={{ padding: '12px 16px', fontWeight: 600 }}>
                            {item.attendance_percentage !== null ? `${item.attendance_percentage}%` : 'N/A'}
                          </td>
                          <td style={{ padding: '12px 16px' }}>
                            {item.warning ? (
                              <span style={{ color: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.15)', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 600 }}>
                                ⚠️ Below 75%
                              </span>
                            ) : item.attendance_percentage !== null ? (
                              <span style={{ color: '#22c55e', backgroundColor: 'rgba(34, 197, 94, 0.15)', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 600 }}>
                                ✓ Good
                              </span>
                            ) : (
                              <span style={{ color: 'var(--color-text-muted)', fontSize: '12px' }}>No Data</span>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )
        )}

        {/* Tournaments Tab */}
        {activeTab === 'tournaments' && (
          tabLoading ? (
            <LoadingSpinner />
          ) : (
            <div className={styles.tableCard || styles.headerBar} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                      <th style={{ padding: '12px 16px' }}>Tournament</th>
                      <th style={{ padding: '12px 16px' }}>Sport</th>
                      <th style={{ padding: '12px 16px' }}>Status</th>
                      <th style={{ padding: '12px 16px' }}>Start Date</th>
                      <th style={{ padding: '12px 16px' }}>Participants</th>
                      <th style={{ padding: '12px 16px' }}>🥇 Gold</th>
                      <th style={{ padding: '12px 16px' }}>🥈 Silver</th>
                      <th style={{ padding: '12px 16px' }}>🥉 Bronze</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tournamentItems.length === 0 ? (
                      <tr>
                        <td colSpan="8" style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                          No tournament records found.
                        </td>
                      </tr>
                    ) : (
                      tournamentItems.map((item) => (
                        <tr key={item.tournament_id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td style={{ padding: '12px 16px', fontWeight: 600 }}>{item.tournament_name}</td>
                          <td style={{ padding: '12px 16px' }}>{item.sport_name || 'N/A'}</td>
                          <td style={{ padding: '12px 16px', textTransform: 'capitalize' }}>{item.status}</td>
                          <td style={{ padding: '12px 16px' }}>
                            {item.start_date ? new Date(item.start_date).toLocaleDateString() : 'N/A'}
                          </td>
                          <td style={{ padding: '12px 16px' }}>{item.total_participants}</td>
                          <td style={{ padding: '12px 16px', color: '#eab308' }}>{item.gold_medalist || '—'}</td>
                          <td style={{ padding: '12px 16px', color: '#94a3b8' }}>{item.silver_medalist || '—'}</td>
                          <td style={{ padding: '12px 16px', color: '#d97706' }}>{item.bronze_medalist || '—'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )
        )}

        {/* Athlete Tab */}
        {activeTab === 'athlete' && (
          <div>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ fontSize: '14px', color: 'var(--color-text-muted)', marginRight: '10px' }}>
                Select Assigned Athlete:
              </label>
              <select
                className={styles.selectInput}
                value={selectedAthleteId}
                onChange={(e) => setSelectedAthleteId(e.target.value)}
              >
                {athletesList.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.full_name} ({a.email})
                  </option>
                ))}
              </select>
            </div>

            {tabLoading ? (
              <LoadingSpinner />
            ) : devSummary ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '12px', padding: '20px' }}>
                  <h3 style={{ margin: '0 0 8px 0', fontSize: '20px' }}>{devSummary.athlete_name}</h3>
                  <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', color: 'var(--color-text-muted)', fontSize: '14px' }}>
                    <span>📧 {devSummary.email}</span>
                    <span>⚽ Sport: <strong>{devSummary.sport_name || 'N/A'}</strong></span>
                    <span>Status: <strong style={{ textTransform: 'capitalize' }}>{devSummary.status}</strong></span>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
                  <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '12px', padding: '20px' }}>
                    <h4 style={{ margin: '0 0 16px 0', color: 'var(--color-accent)' }}>📋 Training & Attendance</h4>
                    <p style={{ margin: '6px 0', fontSize: '14px' }}>
                      Total Sessions: <strong>{devSummary.attendance_summary.total_sessions}</strong>
                    </p>
                    <p style={{ margin: '6px 0', fontSize: '14px' }}>
                      Attended Sessions: <strong>{devSummary.attendance_summary.attended_sessions}</strong>
                    </p>
                    <p style={{ margin: '6px 0', fontSize: '14px' }}>
                      Attendance Rate:{' '}
                      <strong>
                        {devSummary.attendance_summary.attendance_percentage !== null
                          ? `${devSummary.attendance_summary.attendance_percentage}%`
                          : 'N/A'}
                      </strong>
                    </p>
                    {devSummary.attendance_summary.warning && (
                      <div style={{ marginTop: '12px', color: '#ef4444', backgroundColor: 'rgba(239,68,68,0.1)', padding: '8px 12px', borderRadius: '6px', fontSize: '13px' }}>
                        ⚠️ Warning: Attendance below 75% academy threshold.
                      </div>
                    )}
                  </div>

                  <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '12px', padding: '20px' }}>
                    <h4 style={{ margin: '0 0 16px 0', color: 'var(--color-accent)' }}>📈 Performance Assessment</h4>
                    <p style={{ margin: '6px 0', fontSize: '14px' }}>
                      Current Score:{' '}
                      <strong>
                        {devSummary.performance_summary.current_score !== null
                          ? `${devSummary.performance_summary.current_score}/100`
                          : 'No assessments'}
                      </strong>
                    </p>
                    <p style={{ margin: '6px 0', fontSize: '14px' }}>
                      Performance Trend: <strong>{devSummary.performance_summary.trend}</strong>
                    </p>
                    <p style={{ margin: '6px 0', fontSize: '14px' }}>
                      Strongest Metric: <strong>{devSummary.performance_summary.strongest_metric || 'N/A'}</strong>
                    </p>
                    <p style={{ margin: '6px 0', fontSize: '14px' }}>
                      Weakest Metric: <strong>{devSummary.performance_summary.weakest_metric || 'N/A'}</strong>
                    </p>
                  </div>

                  <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '12px', padding: '20px' }}>
                    <h4 style={{ margin: '0 0 16px 0', color: 'var(--color-accent)' }}>🏆 Tournaments & Medals</h4>
                    <p style={{ margin: '6px 0', fontSize: '14px' }}>
                      Tournaments Entered: <strong>{devSummary.tournaments_summary.total_tournaments}</strong>
                    </p>
                    <p style={{ margin: '6px 0', fontSize: '14px' }}>
                      Career Points: <strong>{devSummary.tournaments_summary.total_points}</strong>
                    </p>
                    <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
                      <span style={{ fontSize: '13px', color: '#eab308' }}>
                        🥇 Gold: {devSummary.tournaments_summary.medals_summary?.gold || 0}
                      </span>
                      <span style={{ fontSize: '13px', color: '#94a3b8' }}>
                        🥈 Silver: {devSummary.tournaments_summary.medals_summary?.silver || 0}
                      </span>
                      <span style={{ fontSize: '13px', color: '#d97706' }}>
                        🥉 Bronze: {devSummary.tournaments_summary.medals_summary?.bronze || 0}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
