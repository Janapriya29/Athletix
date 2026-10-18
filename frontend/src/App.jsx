import React from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ProtectedRoute from './routes/ProtectedRoute'

// Public
import LandingPage from './pages/public/LandingPage'

// Auth
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'

// Admin
import AdminDashboard from './pages/admin/AdminDashboard'
import AthletesPage from './pages/admin/AthletesPage'
import CoachesPage from './pages/admin/CoachesPage'
import SportsPage from './pages/admin/SportsPage'
import UsersPage from './pages/admin/UsersPage'
import AdminTrainingPage from './pages/admin/AdminTrainingPage'
import AdminAnalyticsPage from './pages/admin/AdminAnalyticsPage'
import AdminTournamentsPage from './pages/admin/TournamentsPage'
import ReportsPage from './pages/admin/ReportsPage'

// Coach
import CoachDashboard from './pages/coach/CoachDashboard'
import CoachAthletesPage from './pages/coach/CoachAthletesPage'
import CoachProfilePage from './pages/coach/CoachProfilePage'
import CoachSportsPage from './pages/coach/CoachSportsPage'
import TrainingPage from './pages/coach/TrainingPage'
import AttendancePage from './pages/coach/AttendancePage'
import AssessmentsPage from './pages/coach/AssessmentsPage'
import AnalyticsPage from './pages/coach/AnalyticsPage'
import CoachTournamentsPage from './pages/coach/CoachTournamentsPage'
import CoachReportsPage from './pages/coach/CoachReportsPage'
import CoachNotificationsPage from './pages/coach/CoachNotificationsPage'

// Athlete
import AthleteDashboard from './pages/athlete/AthleteDashboard'
import AthleteProfilePage from './pages/athlete/AthleteProfilePage'
import AthleteTrainingPage from './pages/athlete/AthleteTrainingPage'
import AthleteAttendancePage from './pages/athlete/AthleteAttendancePage'
import AthletePerformancePage from './pages/athlete/AthletePerformancePage'
import AthleteAnalyticsPage from './pages/athlete/AthleteAnalyticsPage'
import AthleteTournamentsPage from './pages/athlete/AthleteTournamentsPage'
import AthleteNotificationsPage from './pages/athlete/AthleteNotificationsPage'
import AthleteReportsPage from './pages/athlete/AthleteReportsPage'

// Common
import NotificationsPage from './pages/common/NotificationsPage'
import RankingsPage from './pages/common/RankingsPage'

// 404
import NotFoundPage from './pages/NotFoundPage'

function RootRedirect() {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  const dashboards = { admin: '/admin/dashboard', coach: '/coach/dashboard', athlete: '/athlete/dashboard' }
  return <Navigate to={dashboards[user.role] || '/login'} replace />
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public Landing */}
      <Route path="/" element={<LandingPage />} />

      {/* Public Auth */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Admin routes */}
      <Route path="/admin/dashboard" element={<ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>} />
      <Route path="/admin/athletes"  element={<ProtectedRoute role="admin"><AthletesPage /></ProtectedRoute>} />
      <Route path="/admin/coaches"   element={<ProtectedRoute role="admin"><CoachesPage /></ProtectedRoute>} />
      <Route path="/admin/sports"    element={<ProtectedRoute role="admin"><SportsPage /></ProtectedRoute>} />
      <Route path="/admin/users"     element={<ProtectedRoute role="admin"><UsersPage /></ProtectedRoute>} />
      <Route path="/admin/training"  element={<ProtectedRoute role="admin"><AdminTrainingPage /></ProtectedRoute>} />
      <Route path="/admin/analytics" element={<ProtectedRoute role="admin"><AdminAnalyticsPage /></ProtectedRoute>} />
      <Route path="/admin/tournaments" element={<ProtectedRoute role="admin"><AdminTournamentsPage /></ProtectedRoute>} />
      <Route path="/admin/rankings"  element={<ProtectedRoute role="admin"><RankingsPage role="admin" /></ProtectedRoute>} />
      <Route path="/admin/reports"   element={<ProtectedRoute role="admin"><ReportsPage /></ProtectedRoute>} />
      <Route path="/admin/notifications" element={<ProtectedRoute role="admin"><NotificationsPage /></ProtectedRoute>} />

      {/* Coach routes */}
      <Route path="/coach/dashboard"   element={<ProtectedRoute role="coach"><CoachDashboard /></ProtectedRoute>} />
      <Route path="/coach/athletes"    element={<ProtectedRoute role="coach"><CoachAthletesPage /></ProtectedRoute>} />
      <Route path="/coach/profile"     element={<ProtectedRoute role="coach"><CoachProfilePage /></ProtectedRoute>} />
      <Route path="/coach/sports"      element={<ProtectedRoute role="coach"><CoachSportsPage /></ProtectedRoute>} />
      <Route path="/coach/training"    element={<ProtectedRoute role="coach"><TrainingPage /></ProtectedRoute>} />
      <Route path="/coach/attendance"  element={<ProtectedRoute role="coach"><AttendancePage /></ProtectedRoute>} />
      <Route path="/coach/assessments" element={<ProtectedRoute role="coach"><AssessmentsPage /></ProtectedRoute>} />
      <Route path="/coach/analytics"   element={<ProtectedRoute role="coach"><AnalyticsPage /></ProtectedRoute>} />
      <Route path="/coach/tournaments" element={<ProtectedRoute role="coach"><CoachTournamentsPage /></ProtectedRoute>} />
      <Route path="/coach/rankings"    element={<ProtectedRoute role="coach"><RankingsPage role="coach" /></ProtectedRoute>} />
      <Route path="/coach/reports"     element={<ProtectedRoute role="coach"><CoachReportsPage /></ProtectedRoute>} />
      <Route path="/coach/notifications" element={<ProtectedRoute role="coach"><CoachNotificationsPage /></ProtectedRoute>} />

      {/* Athlete routes */}
      <Route path="/athlete/dashboard"      element={<ProtectedRoute role="athlete"><AthleteDashboard /></ProtectedRoute>} />
      <Route path="/athlete/profile"        element={<ProtectedRoute role="athlete"><AthleteProfilePage /></ProtectedRoute>} />
      <Route path="/athlete/training"       element={<ProtectedRoute role="athlete"><AthleteTrainingPage /></ProtectedRoute>} />
      <Route path="/athlete/attendance"     element={<ProtectedRoute role="athlete"><AthleteAttendancePage /></ProtectedRoute>} />
      <Route path="/athlete/analytics"      element={<ProtectedRoute role="athlete"><AthleteAnalyticsPage /></ProtectedRoute>} />
      <Route path="/athlete/performance"    element={<ProtectedRoute role="athlete"><AthletePerformancePage /></ProtectedRoute>} />
      <Route path="/athlete/tournaments"    element={<ProtectedRoute role="athlete"><AthleteTournamentsPage /></ProtectedRoute>} />
      <Route path="/athlete/rankings"       element={<ProtectedRoute role="athlete"><RankingsPage role="athlete" /></ProtectedRoute>} />
      <Route path="/athlete/reports"        element={<ProtectedRoute role="athlete"><AthleteReportsPage /></ProtectedRoute>} />
      <Route path="/athlete/notifications"  element={<ProtectedRoute role="athlete"><AthleteNotificationsPage /></ProtectedRoute>} />

      {/* Common authenticated routes */}
      <Route path="/notifications" element={<ProtectedRoute><NotificationsPage /></ProtectedRoute>} />

      {/* 404 */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
