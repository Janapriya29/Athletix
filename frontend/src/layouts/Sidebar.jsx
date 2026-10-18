import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './Sidebar.module.css'

const NAV_ITEMS = {
  admin: [
    { label: 'Dashboard',   path: '/admin/dashboard',   icon: '📊' },
    { label: 'Athletes',    path: '/admin/athletes',    icon: '🏃' },
    { label: 'Coaches',     path: '/admin/coaches',     icon: '🧑‍🏫' },
    { label: 'Sports',      path: '/admin/sports',      icon: '🏅' },
    { label: 'Users',       path: '/admin/users',       icon: '👥' },
    { label: 'Training',    path: '/admin/training',    icon: '⏱️' },
    { label: 'Analytics',   path: '/admin/analytics',   icon: '📈' },
    { label: 'Tournaments', path: '/admin/tournaments', icon: '🏆' },
    { label: 'Rankings',    path: '/admin/rankings',    icon: '🥇' },
    { label: 'Reports',     path: '/admin/reports',     icon: '📑' },
    { label: 'Notifications', path: '/notifications',   icon: '🔔' },
  ],
  coach: [
    { label: 'Dashboard',   path: '/coach/dashboard',   icon: '📊' },
    { label: 'My Athletes', path: '/coach/athletes',    icon: '🏃' },
    { label: 'Sports',      path: '/coach/sports',      icon: '🏅' },
    { label: 'Profile',     path: '/coach/profile',     icon: '👤' },
    { label: 'Training',    path: '/coach/training',    icon: '⏱️' },
    { label: 'Attendance',  path: '/coach/attendance',  icon: '📋' },
    { label: 'Assessments', path: '/coach/assessments', icon: '🎯' },
    { label: 'Analytics',   path: '/coach/analytics',   icon: '📈' },
    { label: 'Tournaments', path: '/coach/tournaments', icon: '🏆' },
    { label: 'Rankings',    path: '/coach/rankings',    icon: '🥇' },
    { label: 'Reports',     path: '/coach/reports',     icon: '📑' },
    { label: 'Notifications', path: '/coach/notifications', icon: '🔔' },
  ],
  athlete: [
    { label: 'Dashboard',    path: '/athlete/dashboard',   icon: '📊' },
    { label: 'Profile',      path: '/athlete/profile',     icon: '👤' },
    { label: 'Training',     path: '/athlete/training',    icon: '⏱️' },
    { label: 'Attendance',   path: '/athlete/attendance',  icon: '📋' },
    { label: 'Analytics',    path: '/athlete/analytics',   icon: '📈' },
    { label: 'Tournaments',  path: '/athlete/tournaments', icon: '🏆' },
    { label: 'Rankings',     path: '/athlete/rankings',    icon: '🥇' },
    { label: 'Reports',      path: '/athlete/reports',     icon: '📑' },
    { label: 'Notifications',path: '/athlete/notifications', icon: '🔔' },
  ],
}

export default function Sidebar({ isOpen = false, onClose }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  if (!user) return null

  const items = NAV_ITEMS[user.role] || []

  async function handleLogout() {
    if (onClose) onClose()
    await logout()
    navigate('/login')
  }

  const initial = (user.full_name || user.email || 'U').charAt(0).toUpperCase()

  return (
    <aside className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
      <div className={styles.brand}>
        <div className={styles.brandLeft}>
          <span className={styles.brandIcon}>⚡</span>
          <span className={styles.brandName}>ATHLETIX</span>
        </div>
        <button
          className={styles.closeBtn}
          onClick={onClose}
          aria-label="Close navigation menu"
        >
          ✕
        </button>
      </div>

      <nav className={styles.nav}>
        {items.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={() => {
              if (onClose) onClose()
            }}
            className={({ isActive }) =>
              `${styles.navItem} ${isActive ? styles.active : ''}`
            }
          >
            <span className={styles.navIcon}>{item.icon}</span>
            <span className={styles.navLabel}>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className={styles.footer}>
        <div className={styles.userBox}>
          <div className={styles.userAvatar}>{initial}</div>
          <div className={styles.userInfo}>
            <span className={styles.userName}>{user.full_name || user.email}</span>
            <span className={styles.userRole}>{user.role}</span>
          </div>
        </div>
        <button className={styles.logoutBtn} onClick={handleLogout}>
          Sign Out
        </button>
      </div>
    </aside>
  )
}
