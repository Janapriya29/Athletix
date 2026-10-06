import api from './api'

export const getTrainingSessions = async (params = {}) => {
  const resp = await api.get('/training/sessions', { params })
  return resp.data
}

export const getTrainingSession = async (id) => {
  const resp = await api.get(`/training/sessions/${id}`)
  return resp.data
}

export const createTrainingSession = async (data) => {
  const resp = await api.post('/training/sessions', data)
  return resp.data
}

export const updateTrainingSession = async (id, data) => {
  const resp = await api.put(`/training/sessions/${id}`, data)
  return resp.data
}

export const setTrainingSessionStatus = async (id, status) => {
  const resp = await api.patch(`/training/sessions/${id}/status`, { status })
  return resp.data
}

export const addSessionParticipant = async (sessionId, athleteId) => {
  const resp = await api.post(`/training/sessions/${sessionId}/participants`, { athlete_id: athleteId })
  return resp.data
}

export const removeSessionParticipant = async (sessionId, athleteId) => {
  const resp = await api.delete(`/training/sessions/${sessionId}/participants/${athleteId}`)
  return resp.data
}

export const getSessionAttendance = async (sessionId) => {
  const resp = await api.get(`/training/sessions/${sessionId}/attendance`)
  return resp.data
}

export const recordAttendance = async (sessionId, athleteId, status, remarks = null) => {
  const resp = await api.post(`/training/sessions/${sessionId}/attendance`, {
    athlete_id: athleteId,
    status,
    remarks,
  })
  return resp.data
}

export const recordBulkAttendance = async (sessionId, records) => {
  const resp = await api.post(`/training/sessions/${sessionId}/attendance/bulk`, { records })
  return resp.data
}

export const getMyTrainingSessions = async () => {
  const resp = await api.get('/training/me')
  return resp.data
}

export const getMyAttendanceSummary = async () => {
  const resp = await api.get('/training/me/attendance')
  return resp.data
}

export const getAthleteAttendanceSummary = async (athleteId) => {
  const resp = await api.get(`/training/athlete/${athleteId}/attendance`)
  return resp.data
}

export const getCoachTrainingSummary = async () => {
  const resp = await api.get('/training/coach/summary')
  return resp.data
}

export const getAdminTrainingSummary = async () => {
  const resp = await api.get('/training/admin/summary')
  return resp.data
}
