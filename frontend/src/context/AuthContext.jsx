import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { authService } from '../services/authService'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('athletix_user')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })
  const [loading, setLoading] = useState(true)

  // On mount, verify the stored token is still valid
  useEffect(() => {
    const token = localStorage.getItem('athletix_token')
    if (!token) {
      setLoading(false)
      return
    }
    authService
      .getMe()
      .then((userData) => {
        setUser(userData)
        localStorage.setItem('athletix_user', JSON.stringify(userData))
      })
      .catch(() => {
        localStorage.removeItem('athletix_token')
        localStorage.removeItem('athletix_user')
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email, password) => {
    const data = await authService.login(email, password)
    localStorage.setItem('athletix_token', data.access_token)
    // Fetch full user profile after login
    const userData = await authService.getMe()
    localStorage.setItem('athletix_user', JSON.stringify(userData))
    setUser(userData)
    return userData
  }, [])

  const logout = useCallback(async () => {
    await authService.logout()
    setUser(null)
  }, [])

  const register = useCallback(async (formData) => {
    return await authService.register(formData)
  }, [])

  const value = { user, loading, login, logout, register, isAuthenticated: !!user }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
