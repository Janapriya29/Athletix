import api from './api'

export const reportService = {
  // Athlete-specific reports
  getAthletePerformanceReport: async (athleteId) => {
    const response = await api.get(`/reports/athlete/${athleteId}/performance`)
    return response.data
  },

  getAthleteAttendanceReport: async (athleteId) => {
    const response = await api.get(`/reports/athlete/${athleteId}/attendance`)
    return response.data
  },

  getAthleteTournamentsReport: async (athleteId) => {
    const response = await api.get(`/reports/athlete/${athleteId}/tournaments`)
    return response.data
  },

  getAthleteDevelopmentSummary: async (athleteId) => {
    const response = await api.get(`/reports/athlete/${athleteId}/development`)
    return response.data
  },

  // Academy-wide reports
  getAcademySummaryReport: async () => {
    const response = await api.get('/reports/academy/summary')
    return response.data
  },

  getAcademyAttendanceReport: async (params = {}) => {
    const response = await api.get('/reports/attendance', { params })
    return response.data
  },

  downloadAttendanceReportCsv: async (params = {}) => {
    const response = await api.get('/reports/attendance', {
      params: { ...params, format: 'csv' },
      responseType: 'blob',
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'attendance_report.csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  getAcademyTournamentsReport: async (params = {}) => {
    const response = await api.get('/reports/tournaments', { params })
    return response.data
  },

  downloadTournamentsReportCsv: async (params = {}) => {
    const response = await api.get('/reports/tournaments', {
      params: { ...params, format: 'csv' },
      responseType: 'blob',
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'tournaments_report.csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}

export default reportService
