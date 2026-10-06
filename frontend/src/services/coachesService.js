import api from './api'

export const getCoaches = async (params = {}) => {
  const resp = await api.get('/coaches', { params })
  return resp.data
}

export const getMyCoachProfile = async () => {
  const resp = await api.get('/coaches/me')
  return resp.data
}

export const getCoach = async (id) => {
  const resp = await api.get(`/coaches/${id}`)
  return resp.data
}

export const createCoach = async (data) => {
  const resp = await api.post('/coaches', data)
  return resp.data
}

export const updateCoach = async (id, data) => {
  const resp = await api.put(`/coaches/${id}`, data)
  return resp.data
}

export const setCoachStatus = async (id, status) => {
  const resp = await api.patch(`/coaches/${id}/status`, { status })
  return resp.data
}

export const assignAthletesToCoach = async (coachId, athleteIds) => {
  const resp = await api.post(`/coaches/${coachId}/athletes`, { athlete_ids: athleteIds })
  return resp.data
}

export const removeAthleteFromCoach = async (coachId, athleteId) => {
  const resp = await api.delete(`/coaches/${coachId}/athletes/${athleteId}`)
  return resp.data
}
