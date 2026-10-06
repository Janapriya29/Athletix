import React, { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import styles from './LoginPage.module.css'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const from = location.state?.from?.pathname

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (!email.trim() || !password) {
      setError('Please provide both your email address and password.')
      return
    }

    setLoading(true)
    try {
      const user = await login(email.trim(), password)
      const dashboards = {
        admin: '/admin/dashboard',
        coach: '/coach/dashboard',
        athlete: '/athlete/dashboard',
      }
      navigate(from || dashboards[user.role] || '/admin/dashboard', { replace: true })
    } catch (err) {
      const status = err.response?.status
      const detail = err.response?.data?.detail

      if (status === 401) {
        if (typeof detail === 'string' && detail.toLowerCase().includes('inactive')) {
          setError(
            'Your account is currently pending approval or inactive. Please contact your academy administrator.'
          )
        } else {
          setError('Invalid email or password. Please verify your credentials and try again.')
        }
      } else if (status === 422) {
        setError('Please enter a valid email address and password format.')
      } else if (!err.response) {
        setError('Unable to reach the Athletix server. Please check your network connection.')
      } else {
        setError(typeof detail === 'string' ? detail : 'An unexpected error occurred. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      {/* ── Left Column: Branding & Value Props ── */}
      <div className={styles.brandSide}>
        <div className={styles.brandTop}>
          <Link to="/" className={styles.logoLink}>
            <span className={styles.logoIcon}>⚡</span>
            <span className={styles.logoText}>ATHLETIX</span>
          </Link>
          <span className={styles.badge}>SPORTS TECH</span>
        </div>

        <div className={styles.brandHero}>
          <h1 className={styles.tagline}>
            TRAIN SMARTER.<br />
            <span className={styles.accentText}>PERFORM BETTER.</span>
          </h1>
          <p className={styles.brandDesc}>
            Access your personalized athlete portal, coaching command center, or academy
            administration dashboard.
          </p>

          <div className={styles.featureList}>
            <div className={styles.featureItem}>
              <span className={styles.featIcon}>📊</span>
              <div>
                <strong>Performance Analytics</strong>
                <p>Objective 0–100 evaluations, multi-metric progression & trends.</p>
              </div>
            </div>
            <div className={styles.featureItem}>
              <span className={styles.featIcon}>⏱️</span>
              <div>
                <strong>Training & Attendance</strong>
                <p>Real-time session scheduling with attendance percentage tracking.</p>
              </div>
            </div>
            <div className={styles.featureItem}>
              <span className={styles.featIcon}>🏆</span>
              <div>
                <strong>Rankings & Competitions</strong>
                <p>Tournament participation, medal tallies, and academy leaderboards.</p>
              </div>
            </div>
            <div className={styles.featureItem}>
              <span className={styles.featIcon}>📑</span>
              <div>
                <strong>Academy Reporting</strong>
                <p>Multi-module development profiles and stakeholder CSV exports.</p>
              </div>
            </div>
          </div>
        </div>

        <div className={styles.brandFooter}>
          <span>Integrated Sports Academy Platform • Version 1.0.0</span>
        </div>
      </div>

      {/* ── Right Column: Sign In Form ── */}
      <div className={styles.formSide}>
        <div className={styles.formCard}>
          <div className={styles.cardHeader}>
            <h2 className={styles.welcomeTitle}>Welcome Back</h2>
            <p className={styles.welcomeSubtitle}>Sign in to your Athletix account</p>
          </div>

          {error && (
            <div className={styles.errorAlert} role="alert">
              <span className={styles.errorIcon}>⚠️</span>
              <p className={styles.errorText}>{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className={styles.form} noValidate>
            <div className={styles.formGroup}>
              <label htmlFor="login-email" className={styles.label}>
                Email Address <span className={styles.required}>*</span>
              </label>
              <input
                id="login-email"
                type="email"
                className={styles.input}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="athlete@athletix.dev"
                required
                autoComplete="email"
                autoFocus
              />
            </div>

            <div className={styles.formGroup}>
              <div className={styles.labelRow}>
                <label htmlFor="login-password" className={styles.label}>
                  Password <span className={styles.required}>*</span>
                </label>
              </div>
              <div className={styles.passwordWrapper}>
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  className={styles.passwordInput}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className={styles.toggleBtn}
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
            </div>

            <div className={styles.helpRow}>
              <span className={styles.helperNotice}>
                Forgot password? Contact your academy administrator for reset assistance.
              </span>
            </div>

            <button
              type="submit"
              className={styles.submitBtn}
              disabled={loading}
            >
              {loading ? (
                <span className={styles.btnLoading}>
                  <span className={styles.spinner}></span> Signing in…
                </span>
              ) : (
                'Sign In to Athletix →'
              )}
            </button>
          </form>

          <div className={styles.cardFooter}>
            <p>
              New to Athletix?{' '}
              <Link to="/register" className={styles.createLink}>
                Create an Account
              </Link>
            </p>
            <Link to="/" className={styles.backHomeLink}>
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
