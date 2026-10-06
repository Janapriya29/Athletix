import api from './api'

export const getSports = async (params = {}) => {
  const resp = await api.get('/sports', { params })
  return resp.data
}

export const getSport = async (id) => {
  const resp = await api.get(`/sports/${id}`)
  return resp.data
}

export const createSport = async (data) => {
  const resp = await api.post('/sports', data)
  return resp.data
}

export const updateSport = async (id, data) => {
  const resp = await api.put(`/sports/${id}`, data)
  return resp.data
}

export const setSportStatus = async (id, isActive) => {
  const resp = await api.patch(`/sports/${id}/status`, { is_active: isActive })
  return resp.data
}

export const deleteSport = async (id) => {
  const resp = await api.delete(`/sports/${id}`)
  return resp.data
}

export const addSportCategory = async (sportId, data) => {
  const resp = await api.post(`/sports/${sportId}/categories`, data)
  return resp.data
}
