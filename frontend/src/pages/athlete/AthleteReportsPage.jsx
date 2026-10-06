import React, { useState, useEffect } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import reportService from '../../services/reportService'
import { getMyAthleteProfile } from '../../services/athletesService'
import styles from '../../styles/Management.module.css'

export default function AthleteReportsPage() {
  const [activeTab, setActiveTab] = useState('summary') // 'summary' | 'attendance' | 'tournaments'
  const [athleteProfile, setAthleteProfile] = useState(null)
  const [devSummary, setDevSummary] = useState(null)
  const [attReport, setAttReport] = useState(null)
  const [tournReport, setTournReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function init() {
      try {
        setLoading(true)
        const profile = await getMyAthleteProfile()
        setAthleteProfile(profile)

        if (profile?.id) {
          const [devData, attData, tournData] = await Promise.all([
            reportService.getAthleteDevelopmentSummary(profile.id).catch(() => null),
            reportService.getAthleteAttendanceReport(profile.id).catch(() => null),
            reportService.getAthleteTournamentsReport(profile.id).catch(() => null),
          ])
          setDevSummary(devData)
          setAttReport(attData)
          setTournReport(tournData)
        }
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load athlete reports')
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  return (
    <AppLayout title="My Reports & Development">
      <div className={styles.container}>
        {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

        {/* Tab Selection */}
        <div className={styles.headerBar}>
          <div className={styles.controls}>
            <button
              className={activeTab === 'summary' ? styles.primaryBtn : styles.secondaryBtn}
              onClick={() => setActiveTab('summary')}
            >
              👤 Development Summary
            </button>
            <button
              className={activeTab === 'attendance' ? styles.primaryBtn : styles.secondaryBtn}
              onClick={() => setActiveTab('attendance')}
            >
              📋 Attendance Breakdown
            </button>
            <button
              className={activeTab === 'tournaments' ? styles.primaryBtn : styles.secondaryBtn}
              onClick={() => setActiveTab('tournaments')}
            >
              🏆 Tournaments & Medals
            </button>
          </div>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : (
          <div>
            {/* Tab 1: Development Summary */}
            {activeTab === 'summary' && devSummary && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '12px', padding: '20px' }}>
                  <h3 style={{ margin: '0 0 8px 0', fontSize: '20px' }}>{devSummary.athlete_name}</h3>
                  <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', color: 'var(--color-text-muted)', fontSize: '14px' }}>
                    <span>⚽ Sport: <strong>{devSummary.sport_name || 'N/A'}</strong></span>
                    <span>🧑‍🏫 Coach: <strong>{devSummary.coach_name || 'N/A'}</strong></span>
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
            )}

            {/* Tab 2: Attendance Breakdown */}
            {activeTab === 'attendance' && attReport && (
              <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '12px', padding: '24px' }}>
                <h3 style={{ margin: '0 0 16px 0' }}>Attendance Statistics</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                  <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Total Sessions</div>
                    <div style={{ fontSize: '24px', fontWeight: 700 }}>{attReport.total_sessions}</div>
                  </div>
                  <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Present</div>
                    <div style={{ fontSize: '24px', fontWeight: 700, color: '#22c55e' }}>{attReport.present_count}</div>
                  </div>
                  <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Late</div>
                    <div style={{ fontSize: '24px', fontWeight: 700, color: '#eab308' }}>{attReport.late_count}</div>
                  </div>
                  <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Absent</div>
                    <div style={{ fontSize: '24px', fontWeight: 700, color: '#ef4444' }}>{attReport.absent_count}</div>
                  </div>
                  <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Attendance Rate</div>
                    <div style={{ fontSize: '24px', fontWeight: 700 }}>
                      {attReport.attendance_percentage !== null ? `${attReport.attendance_percentage}%` : 'N/A'}
                    </div>
                  </div>
                </div>

                {attReport.warning && (
                  <div style={{ color: '#ef4444', backgroundColor: 'rgba(239,68,68,0.1)', padding: '12px 16px', borderRadius: '8px', fontSize: '14px' }}>
                    ⚠️ Your attendance is currently below the academy standard of 75%. Please attend upcoming sessions.
                  </div>
                )}
              </div>
            )}

            {/* Tab 3: Tournaments & Medals */}
            {activeTab === 'tournaments' && tournReport && (
              <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '12px', padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                  <h3 style={{ margin: 0 }}>Tournament Participations</h3>
                  <div style={{ display: 'flex', gap: '16px' }}>
                    <span style={{ color: '#eab308', fontWeight: 600 }}>🥇 {tournReport.medals_summary?.gold || 0} Gold</span>
                    <span style={{ color: '#94a3b8', fontWeight: 600 }}>🥈 {tournReport.medals_summary?.silver || 0} Silver</span>
                    <span style={{ color: '#d97706', fontWeight: 600 }}>🥉 {tournReport.medals_summary?.bronze || 0} Bronze</span>
                    <span style={{ fontWeight: 600 }}>Points: {tournReport.total_points}</span>
                  </div>
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                        <th style={{ padding: '12px 16px' }}>Tournament</th>
                        <th style={{ padding: '12px 16px' }}>Sport</th>
                        <th style={{ padding: '12px 16px' }}>Event</th>
                        <th style={{ padding: '12px 16px' }}>Date</th>
                        <th style={{ padding: '12px 16px' }}>Position</th>
                        <th style={{ padding: '12px 16px' }}>Medal</th>
                        <th style={{ padding: '12px 16px' }}>Points</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tournReport.history.length === 0 ? (
                        <tr>
                          <td colSpan="7" style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                            No tournament history recorded yet.
                          </td>
                        </tr>
                      ) : (
                        tournReport.history.map((h) => (
                          <tr key={h.tournament_id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                            <td style={{ padding: '12px 16px', fontWeight: 600 }}>{h.tournament_name}</td>
                            <td style={{ padding: '12px 16px' }}>{h.sport_name || 'N/A'}</td>
                            <td style={{ padding: '12px 16px' }}>{h.event || '—'}</td>
                            <td style={{ padding: '12px 16px' }}>
                              {h.start_date ? new Date(h.start_date).toLocaleDateString() : 'N/A'}
                            </td>
                            <td style={{ padding: '12px 16px' }}>{h.position ? `#${h.position}` : '—'}</td>
                            <td style={{ padding: '12px 16px' }}>
                              {h.medal ? (
                                <span style={{ textTransform: 'capitalize', fontWeight: 600 }}>{h.medal}</span>
                              ) : (
                                '—'
                              )}
                            </td>
                            <td style={{ padding: '12px 16px', fontWeight: 600 }}>{h.points ?? '—'}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
