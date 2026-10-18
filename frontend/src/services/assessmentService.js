import api from './api'

export const getAssessments = async (params = {}) => {
  const resp = await api.get('/assessments', { params })
  return resp.data
}

export const getAssessment = async (id) => {
  const resp = await api.get(`/assessments/${id}`)
  return resp.data
}

export const getAthleteAssessments = async (athleteId) => {
  const resp = await api.get(`/assessments/athlete/${athleteId}`)
  return resp.data
}

export const createAssessment = async (data) => {
  const resp = await api.post('/assessments', data)
  return resp.data
}
