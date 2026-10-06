import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './NotFoundPage.module.css'

export default function NotFoundPage() {
  const { user } = useAuth()
  const dashboards = { admin: '/admin/dashboard', coach: '/coach/dashboard', athlete: '/athlete/dashboard' }
  const home = user ? dashboards[user.role] : '/login'

  return (
    <div className={styles.page}>
      <h1 className={styles.code}>404</h1>
      <p className={styles.message}>Page not found.</p>
      <Link to={home} className={styles.link}>Go back home</Link>
    </div>
  )
}
