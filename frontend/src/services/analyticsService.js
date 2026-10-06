import api from './api'

export const getMyAnalytics = async () => {
  const resp = await api.get('/analytics/athlete/me')
  return resp.data
}

export const getAthleteAnalytics = async (athleteId) => {
  const resp = await api.get(`/analytics/athlete/${athleteId}`)
  return resp.data
}

export const getCoachAnalyticsSummary = async () => {
  const resp = await api.get('/analytics/coach/summary')
  return resp.data
}

export const getCoachAthletesAnalytics = async (params = {}) => {
  const resp = await api.get('/analytics/coach/athletes', { params })
  return resp.data
}

export const getAdminAnalyticsSummary = async () => {
  const resp = await api.get('/analytics/admin/summary')
  return resp.data
}

export const getAdminSportsAnalytics = async () => {
  const resp = await api.get('/analytics/admin/sports')
  return resp.data
}
