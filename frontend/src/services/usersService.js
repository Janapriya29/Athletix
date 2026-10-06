import api from './api'

export const getUsers = async (params = {}) => {
  const resp = await api.get('/users', { params })
  return resp.data
}

export const getUser = async (id) => {
  const resp = await api.get(`/users/${id}`)
  return resp.data
}

export const createUser = async (data) => {
  const resp = await api.post('/users', data)
  return resp.data
}

export const updateUser = async (id, data) => {
  const resp = await api.put(`/users/${id}`, data)
  return resp.data
}

export const setUserStatus = async (id, isActive) => {
  const resp = await api.patch(`/users/${id}/status`, { is_active: isActive })
  return resp.data
}
