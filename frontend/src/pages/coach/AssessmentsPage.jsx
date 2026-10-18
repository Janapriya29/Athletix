import React, { useEffect, useState, useMemo } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import StatCard from '../../components/common/StatCard'
import styles from '../../styles/Management.module.css'
import { getAthletes } from '../../services/athletesService'
import { getSports, getSportCategories } from '../../services/sportsService'
import { getAssessments, createAssessment } from '../../services/assessmentService'

export default function AssessmentsPage() {
  const [assessments, setAssessments] = useState([])
  const [myAthletes, setMyAthletes] = useState([])
  const [sports, setSports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [feedback, setFeedback] = useState(null)

  // Filters
  const [search, setSearch] = useState('')
  const [selectedAthleteFilter, setSelectedAthleteFilter] = useState('all')
  const [selectedSportFilter, setSelectedSportFilter] = useState('all')

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalError, setModalError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [categoriesLoading, setCategoriesLoading] = useState(false)
  const [availableCategories, setAvailableCategories] = useState([])

  // Form State
  const [formData, setFormData] = useState({
    athlete_id: '',
    sport_id: '',
    date: new Date().toISOString().split('T')[0],
    metrics: {},
    remarks: '',
  })

  // Load Initial Data
  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [assData, athData, sportData] = await Promise.all([
        getAssessments(),
        getAthletes(),
        getSports(),
      ])
      setAssessments(assData || [])
      setMyAthletes(athData || [])
      setSports(sportData || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load assessments.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // When Athlete is selected in modal, load categories for their sport
  const handleAthleteChange = async (athleteId) => {
    const selectedAth = myAthletes.find((a) => a.id === athleteId || a._id === athleteId)
    const sportId = selectedAth?.sport_id || ''
    
    setFormData((prev) => ({
      ...prev,
      athlete_id: athleteId,
      sport_id: sportId,
      metrics: {},
    }))

    if (sportId) {
      try {
        setCategoriesLoading(true)
        const cats = await getSportCategories(sportId)
        if (cats && cats.length > 0) {
          setAvailableCategories(cats)
          const initMetrics = {}
          cats.forEach((c) => {
            initMetrics[c.name.toLowerCase()] = 75
          })
          setFormData((prev) => ({ ...prev, metrics: initMetrics }))
        } else {
          // Default athletic metrics if no categories defined
          const defaults = ['speed', 'endurance', 'technique', 'strength']
          setAvailableCategories(defaults.map((d) => ({ name: d })))
          const initMetrics = {}
          defaults.forEach((d) => {
            initMetrics[d] = 75
          })
          setFormData((prev) => ({ ...prev, metrics: initMetrics }))
        }
      } catch {
        const defaults = ['speed', 'endurance', 'technique', 'strength']
        setAvailableCategories(defaults.map((d) => ({ name: d })))
        const initMetrics = {}
        defaults.forEach((d) => {
          initMetrics[d] = 75
        })
        setFormData((prev) => ({ ...prev, metrics: initMetrics }))
      } finally {
        setCategoriesLoading(false)
      }
    } else {
      setAvailableCategories([])
    }
  }

  const handleMetricChange = (metricName, value) => {
    const valNum = Math.min(100, Math.max(0, Number(value) || 0))
    setFormData((prev) => ({
      ...prev,
      metrics: {
        ...prev.metrics,
        [metricName]: valNum,
      },
    }))
  }

  // Calculate live score
  const liveOverallScore = useMemo(() => {
    const values = Object.values(formData.metrics)
    if (values.length === 0) return null
    const total = values.reduce((sum, v) => sum + (Number(v) || 0), 0)
    return Math.round((total / values.length) * 10) / 10
  }, [formData.metrics])

  const openCreateModal = () => {
    setModalError(null)
    const initialAthId = myAthletes.length > 0 ? (myAthletes[0].id || myAthletes[0]._id) : ''
    setFormData({
      athlete_id: initialAthId,
      sport_id: '',
      date: new Date().toISOString().split('T')[0],
      metrics: {},
      remarks: '',
    })
    setIsModalOpen(true)
    if (initialAthId) {
      handleAthleteChange(initialAthId)
    }
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    setModalError(null)

    if (!formData.athlete_id) {
      setModalError('Please select an athlete.')
      return
    }

    if (Object.keys(formData.metrics).length === 0) {
      setModalError('Please define at least one performance metric.')
      return
    }

    try {
      setSubmitting(true)
      const payload = {
        athlete_id: formData.athlete_id,
        sport_id: formData.sport_id || undefined,
        date: formData.date ? new Date(formData.date).toISOString() : undefined,
        metrics: formData.metrics,
        remarks: formData.remarks?.trim() || undefined,
      }

      const res = await createAssessment(payload)
      setIsModalOpen(false)
      setFeedback(`Performance assessment recorded successfully! Overall score: ${res.overall_score}/100.`)
      // Refresh assessments list
      const updated = await getAssessments()
      setAssessments(updated || [])
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed to record assessment.')
    } finally {
      setSubmitting(false)
    }
  }

  // Filtered assessments list
  const filteredAssessments = useMemo(() => {
    return assessments.filter((a) => {
      const matchSearch =
        !search ||
        a.athlete_name?.toLowerCase().includes(search.toLowerCase()) ||
        a.remarks?.toLowerCase().includes(search.toLowerCase()) ||
        a.sport_name?.toLowerCase().includes(search.toLowerCase())

      const matchAthlete =
        selectedAthleteFilter === 'all' ||
        String(a.athlete_id) === String(selectedAthleteFilter)

      const matchSport =
        selectedSportFilter === 'all' ||
        String(a.sport_id) === String(selectedSportFilter)

      return matchSearch && matchAthlete && matchSport
    })
  }, [assessments, search, selectedAthleteFilter, selectedSportFilter])

  // Statistics calculation
  const stats = useMemo(() => {
    const total = assessments.length
    if (total === 0) {
      return { total: 0, avgScore: '—', topPerformer: '—' }
    }
    const sumScore = assessments.reduce((acc, a) => acc + (a.overall_score || 0), 0)
    const avg = Math.round((sumScore / total) * 10) / 10
    const highest = [...assessments].sort((a, b) => (b.overall_score || 0) - (a.overall_score || 0))[0]
    return {
      total,
      avgScore: `${avg} / 100`,
      topPerformer: highest ? `${highest.athlete_name} (${highest.overall_score})` : '—',
    }
  }, [assessments])

  const getScoreBadgeClass = (score) => {
    if (score >= 80) return styles.badgePresent
    if (score >= 65) return styles.badgeLate
    return styles.badgeAbsent
  }

  return (
    <AppLayout title="Performance Assessments">
      <div className={styles.container}>
        {error && <ErrorMessage message={error} />}
        {feedback && (
          <div
            style={{
              backgroundColor: 'rgba(34, 197, 94, 0.15)',
              border: '1px solid rgba(34, 197, 94, 0.3)',
              color: '#4ade80',
              padding: 'var(--space-3) var(--space-4)',
              borderRadius: 'var(--radius)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span>✅ {feedback}</span>
            <button
              onClick={() => setFeedback(null)}
              style={{ background: 'none', border: 'none', color: '#4ade80', cursor: 'pointer', fontWeight: 'bold' }}
            >
              ✕
            </button>
          </div>
        )}

        {/* Stats Row */}
        <div className={styles.statsGrid}>
          <StatCard label="Assessments Recorded" value={stats.total} />
          <StatCard label="Average Overall Score" value={stats.avgScore} />
          <StatCard label="Assigned Athletes" value={myAthletes.length} />
          <StatCard label="Top Performer" value={stats.topPerformer} />
        </div>

        {/* Header Controls & Filter Bar */}
        <div className={styles.headerBar}>
          <div className={styles.controls}>
            <input
              type="text"
              placeholder="Search by athlete or remarks..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className={styles.searchInput}
            />

            <select
              value={selectedAthleteFilter}
              onChange={(e) => setSelectedAthleteFilter(e.target.value)}
              className={styles.selectInput}
            >
              <option value="all">All Assigned Athletes</option>
              {myAthletes.map((ath) => (
                <option key={ath.id || ath._id} value={ath.id || ath._id}>
                  {ath.full_name}
                </option>
              ))}
            </select>

            <select
              value={selectedSportFilter}
              onChange={(e) => setSelectedSportFilter(e.target.value)}
              className={styles.selectInput}
            >
              <option value="all">All Sports</option>
              {sports.map((sp) => (
                <option key={sp.id || sp._id} value={sp.id || sp._id}>
                  {sp.name}
                </option>
              ))}
            </select>
          </div>

          <button className={styles.primaryBtn} onClick={openCreateModal}>
            <span>+</span> Record Assessment
          </button>
        </div>

        {/* Assessments List Table */}
        {loading ? (
          <LoadingSpinner />
        ) : filteredAssessments.length === 0 ? (
          <div
            style={{
              padding: 'var(--space-8)',
              textAlign: 'center',
              backgroundColor: 'var(--color-surface)',
              borderRadius: 'var(--radius)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-muted)',
            }}
          >
            <p style={{ fontSize: 'var(--text-lg)', marginBottom: 'var(--space-2)' }}>📋 No Assessments Found</p>
            <p style={{ fontSize: 'var(--text-sm)' }}>
              {assessments.length === 0
                ? 'No performance assessments have been recorded yet. Click "Record Assessment" to evaluate an athlete.'
                : 'No assessments match the selected search or filter criteria.'}
            </p>
          </div>
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Athlete</th>
                  <th>Sport</th>
                  <th>Metrics Breakdown</th>
                  <th>Overall Score</th>
                  <th>Remarks</th>
                </tr>
              </thead>
              <tbody>
                {filteredAssessments.map((a) => (
                  <tr key={a.id}>
                    <td>{new Date(a.date).toLocaleDateString()}</td>
                    <td>
                      <strong style={{ color: 'var(--color-text)' }}>{a.athlete_name || 'Athlete'}</strong>
                    </td>
                    <td>{a.sport_name || '—'}</td>
                    <td>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {Object.entries(a.metrics || {}).map(([key, val]) => (
                          <span
                            key={key}
                            style={{
                              backgroundColor: 'var(--color-surface-2)',
                              border: '1px solid var(--color-border)',
                              borderRadius: '4px',
                              padding: '2px 6px',
                              fontSize: 'var(--text-xs)',
                              textTransform: 'capitalize',
                            }}
                          >
                            <strong>{key}:</strong> {val}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td>
                      <span className={`${styles.badge} ${getScoreBadgeClass(a.overall_score)}`}>
                        {a.overall_score} / 100
                      </span>
                    </td>
                    <td style={{ color: 'var(--color-text-muted)', maxWidth: '240px', fontSize: 'var(--text-xs)' }}>
                      {a.remarks || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Record Assessment Modal */}
        {isModalOpen && (
          <div className={styles.modalOverlay} onClick={() => setIsModalOpen(false)}>
            <div
              className={styles.modal}
              style={{ maxWidth: '600px' }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className={styles.modalHeader}>
                <h3 className={styles.modalTitle}>Record Performance Assessment</h3>
                <button className={styles.closeBtn} onClick={() => setIsModalOpen(false)}>
                  ✕
                </button>
              </div>

              <form onSubmit={handleFormSubmit}>
                <div className={styles.modalBody}>
                  {modalError && <ErrorMessage message={modalError} />}

                  {/* Athlete Selection */}
                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Select Athlete *</label>
                    <select
                      className={styles.formSelect}
                      value={formData.athlete_id}
                      onChange={(e) => handleAthleteChange(e.target.value)}
                      required
                    >
                      <option value="" disabled>
                        Choose an assigned athlete...
                      </option>
                      {myAthletes.map((ath) => (
                        <option key={ath.id || ath._id} value={ath.id || ath._id}>
                          {ath.full_name} ({ath.sport_name || 'Assigned'})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Assessment Date */}
                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Assessment Date *</label>
                    <input
                      type="date"
                      className={styles.formInput}
                      value={formData.date}
                      onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                      required
                    />
                  </div>

                  {/* Dynamic Metrics */}
                  <div style={{ marginTop: 'var(--space-2)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <label className={styles.formLabel}>Sport Specific Metrics (0–100)</label>
                      {categoriesLoading && (
                        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                          Loading categories...
                        </span>
                      )}
                    </div>

                    {availableCategories.length === 0 ? (
                      <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                        Select an athlete above to load metrics for their sport.
                      </p>
                    ) : (
                      <div
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '12px',
                          backgroundColor: 'var(--color-surface-2)',
                          padding: '14px',
                          borderRadius: 'var(--radius)',
                          border: '1px solid var(--color-border)',
                        }}
                      >
                        {availableCategories.map((cat) => {
                          const key = cat.name.toLowerCase()
                          const score = formData.metrics[key] ?? 75
                          return (
                            <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, textTransform: 'capitalize', color: 'var(--color-text)' }}>
                                  {cat.name}
                                </span>
                                <span style={{ fontSize: 'var(--text-sm)', fontWeight: 700, color: 'var(--color-accent)' }}>
                                  {score} / 100
                                </span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <input
                                  type="range"
                                  min="0"
                                  max="100"
                                  value={score}
                                  onChange={(e) => handleMetricChange(key, e.target.value)}
                                  style={{ flex: 1, accentColor: 'var(--color-accent)', cursor: 'pointer' }}
                                />
                                <input
                                  type="number"
                                  min="0"
                                  max="100"
                                  value={score}
                                  onChange={(e) => handleMetricChange(key, e.target.value)}
                                  style={{
                                    width: '64px',
                                    padding: '4px 8px',
                                    backgroundColor: 'var(--color-surface)',
                                    border: '1px solid var(--color-border)',
                                    borderRadius: '4px',
                                    color: 'var(--color-text)',
                                    fontSize: 'var(--text-sm)',
                                    textAlign: 'center',
                                  }}
                                />
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>

                  {/* Live Overall Score Preview */}
                  {liveOverallScore !== null && (
                    <div
                      style={{
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        border: '1px solid rgba(34, 197, 94, 0.25)',
                        borderRadius: 'var(--radius)',
                        padding: '12px 16px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--color-text)' }}>
                        🎯 Live Overall Score Preview:
                      </span>
                      <strong style={{ fontSize: 'var(--text-lg)', color: '#22c55e' }}>
                        {liveOverallScore} / 100
                      </strong>
                    </div>
                  )}

                  {/* Remarks */}
                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Remarks & Coaching Notes</label>
                    <textarea
                      rows={3}
                      className={styles.formTextarea}
                      placeholder="Feedback on strengths, areas to improve, and training focus..."
                      value={formData.remarks}
                      onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
                    />
                  </div>
                </div>

                <div className={styles.modalFooter}>
                  <button
                    type="button"
                    className={styles.secondaryBtn}
                    onClick={() => setIsModalOpen(false)}
                    disabled={submitting}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className={styles.primaryBtn}
                    disabled={submitting || availableCategories.length === 0}
                  >
                    {submitting ? 'Saving Assessment...' : 'Record Assessment'}
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
