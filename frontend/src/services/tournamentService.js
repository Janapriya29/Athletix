import api from './api'

export const getTournaments = async (params = {}) => {
  const resp = await api.get('/tournaments', { params })
  return resp.data
}

export const getTournament = async (id) => {
  const resp = await api.get(`/tournaments/${id}`)
  return resp.data
}

export const createTournament = async (data) => {
  const resp = await api.post('/tournaments', data)
  return resp.data
}

export const updateTournament = async (id, data) => {
  const resp = await api.put(`/tournaments/${id}`, data)
  return resp.data
}

export const deleteTournament = async (id) => {
  const resp = await api.delete(`/tournaments/${id}`)
  return resp.data
}

export const getParticipants = async (tournamentId) => {
  const resp = await api.get(`/tournaments/${tournamentId}/participants`)
  return resp.data
}

export const addParticipant = async (tournamentId, data) => {
  const resp = await api.post(`/tournaments/${tournamentId}/participants`, data)
  return resp.data
}

export const removeParticipant = async (tournamentId, athleteId) => {
  const resp = await api.delete(`/tournaments/${tournamentId}/participants/${athleteId}`)
  return resp.data
}

export const getTournamentResults = async (tournamentId) => {
  const resp = await api.get(`/tournaments/${tournamentId}/results`)
  return resp.data
}

export const recordResult = async (tournamentId, data) => {
  const resp = await api.post(`/tournaments/${tournamentId}/results`, data)
  return resp.data
}

export const updateResult = async (tournamentId, athleteId, data) => {
  const resp = await api.put(`/tournaments/${tournamentId}/results/${athleteId}`, data)
  return resp.data
}

export const getMyTournamentHistory = async () => {
  const resp = await api.get('/athletes/me/tournaments')
  return resp.data
}

export const getAthleteTournamentHistory = async (athleteId) => {
  const resp = await api.get(`/tournaments/history/${athleteId}`)
  return resp.data
}
