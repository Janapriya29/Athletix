import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/**
 * Wraps a route so it requires authentication and optionally a specific role.
 * Unauthenticated users are sent to /login with the intended path preserved.
 * Users with the wrong role are sent to their own dashboard.
 */
export default function ProtectedRoute({ children, role }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <span style={{ color: 'var(--color-text-muted)' }}>Loading…</span>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (role && user.role !== role) {
    // Redirect to the correct dashboard for the user's actual role
    const dashboards = { admin: '/admin/dashboard', coach: '/coach/dashboard', athlete: '/athlete/dashboard' }
    return <Navigate to={dashboards[user.role] || '/login'} replace />
  }

  return children
}
