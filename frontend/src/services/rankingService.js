import api from './api'

export const getRankings = async (type = 'tournament', sportId = null, includeZero = true) => {
  const params = { type, include_zero: includeZero }
  if (sportId) params.sport_id = sportId
  const resp = await api.get('/rankings', { params })
  return resp.data
}

export const getTournamentRankings = async (sportId = null, includeZero = false) => {
  const params = { include_zero: includeZero }
  if (sportId) params.sport_id = sportId
  const resp = await api.get('/rankings/tournament', { params })
  return resp.data
}

export const getPerformanceRankings = async (sportId = null, includeZero = false) => {
  const params = { include_zero: includeZero }
  if (sportId) params.sport_id = sportId
  const resp = await api.get('/rankings/performance', { params })
  return resp.data
}

export const getAttendanceRankings = async (sportId = null, includeZero = false) => {
  const params = { include_zero: includeZero }
  if (sportId) params.sport_id = sportId
  const resp = await api.get('/rankings/attendance', { params })
  return resp.data
}

export const getImprovementRankings = async (sportId = null) => {
  const params = {}
  if (sportId) params.sport_id = sportId
  const resp = await api.get('/rankings/improvement', { params })
  return resp.data
}
