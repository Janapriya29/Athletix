import api from './api'

export const getAthletes = async (params = {}) => {
  const resp = await api.get('/athletes', { params })
  return resp.data
}

export const getMyAthleteProfile = async () => {
  const resp = await api.get('/athletes/me')
  return resp.data
}

export const getMyCoach = async () => {
  const resp = await api.get('/athletes/me/coach')
  return resp.data
}

export const getAthlete = async (id) => {
  const resp = await api.get(`/athletes/${id}`)
  return resp.data
}

export const createAthlete = async (data) => {
  const resp = await api.post('/athletes', data)
  return resp.data
}

export const updateAthlete = async (id, data) => {
  const resp = await api.put(`/athletes/${id}`, data)
  return resp.data
}

export const setAthleteStatus = async (id, status) => {
  const resp = await api.patch(`/athletes/${id}/status`, { status })
  return resp.data
}

export const assignCoachToAthlete = async (athleteId, coachId) => {
  const resp = await api.patch(`/athletes/${athleteId}/coach`, { coach_id: coachId })
  return resp.data
}

export const assignSportToAthlete = async (athleteId, sportId, additionalSportIds = []) => {
  const resp = await api.patch(`/athletes/${athleteId}/sport`, {
    sport_id: sportId,
    additional_sport_ids: additionalSportIds,
  })
  return resp.data
}
