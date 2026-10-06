import api from './api'

export const authService = {
  async login(email, password) {
    // FastAPI OAuth2 form expects application/x-www-form-urlencoded
    const params = new URLSearchParams()
    params.append('username', email)
    params.append('password', password)
    const response = await api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return response.data
  },

  async register({ full_name, email, password, role }) {
    const response = await api.post('/auth/register', {
      full_name,
      email,
      password,
      role,
    })
    return response.data
  },

  async logout() {
    try {
      await api.post('/auth/logout')
    } catch {
      // Always clear local state regardless of server response
    }
    localStorage.removeItem('athletix_token')
    localStorage.removeItem('athletix_user')
  },

  async getMe() {
    const response = await api.get('/auth/me')
    return response.data
  },

  async changePassword(currentPassword, newPassword) {
    const response = await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
    return response.data
  },
}
