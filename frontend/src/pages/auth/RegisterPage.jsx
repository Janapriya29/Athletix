import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import styles from './RegisterPage.module.css'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [role, setRole] = useState('athlete')
  const [showPassword, setShowPassword] = useState(false)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [successData, setSuccessData] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (!fullName.trim()) {
      setError('Please provide your full name.')
      return
    }
    if (!email.trim()) {
      setError('Please enter a valid email address.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters in length.')
      return
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match. Please verify both password entries.')
      return
    }

    setLoading(true)
    try {
      const res = await register({
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        password,
        role,
      })
      setSuccessData(res)
    } catch (err) {
      const status = err.response?.status
      const detail = err.response?.data?.detail

      if (status === 409) {
        setError('An account with this email address already exists. Please sign in instead.')
      } else if (status === 403) {
        setError(typeof detail === 'string' ? detail : 'Unauthorized role creation request.')
      } else if (status === 422) {
        setError('Please check your input values. Password must be at least 8 characters.')
      } else if (!err.response) {
        setError('Unable to connect to the Athletix server. Please check your internet connection.')
      } else {
        setError(typeof detail === 'string' ? detail : 'Registration failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  // ── Success State View ──
  if (successData) {
    return (
      <div className={styles.container}>
        <div className={styles.centerBox}>
          <div className={styles.successCard}>
            <div className={styles.successIcon}>
              {successData.role === 'athlete' ? '🎉' : '⏳'}
            </div>
            <h2 className={styles.successTitle}>
              {successData.role === 'athlete'
                ? 'Welcome to Athletix!'
                : 'Access Request Submitted'}
            </h2>
            <p className={styles.successMessage}>
              {successData.message || 'Your account request has been processed.'}
            </p>

            <div className={styles.accountInfoBadge}>
              <span className={styles.accountRoleBadge}>
                {successData.role.toUpperCase()}
              </span>
              <span className={styles.accountEmail}>{successData.email}</span>
            </div>

            {successData.role !== 'athlete' && (
              <div className={styles.approvalNoticeBox}>
                <span>ℹ️</span>
                <p>
                  To maintain strict academy security, Coach and Admin accounts require manual
                  verification by an active administrator before you can sign in.
                </p>
              </div>
            )}

            <button
              type="button"
              className={styles.successBtn}
              onClick={() => navigate('/login')}
            >
              Back to Sign In →
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ── Registration Form View ──
  return (
    <div className={styles.container}>
      <div className={styles.formBox}>
        {/* Brand Top Header */}
        <div className={styles.header}>
          <Link to="/" className={styles.logoLink}>
            <span className={styles.logoIcon}>⚡</span>
            <span className={styles.logoText}>ATHLETIX</span>
          </Link>
          <span className={styles.headerTag}>ACCOUNT ACCESS</span>
        </div>

        <div className={styles.card}>
          <div className={styles.cardHeading}>
            <h2>Create Your Account</h2>
            <p>Select your role and enter your details to register</p>
          </div>

          {error && (
            <div className={styles.errorAlert} role="alert">
              <span>⚠️</span>
              <p>{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className={styles.form} noValidate>
            {/* ── Role Selection ── */}
            <div className={styles.roleGroup}>
              <label className={styles.roleLabel}>Select Your Role</label>
              <div className={styles.roleTiles}>
                <div
                  className={`${styles.roleTile} ${role === 'athlete' ? styles.roleActive : ''}`}
                  onClick={() => setRole('athlete')}
                >
                  <div className={styles.roleTileTop}>
                    <span className={styles.roleIcon}>⚡</span>
                    <span className={styles.roleName}>Athlete</span>
                    <span className={styles.instantBadge}>Immediate Access</span>
                  </div>
                  <p className={styles.roleDesc}>
                    Track your personal training, assessments, attendance, and rankings.
                  </p>
                </div>

                <div
                  className={`${styles.roleTile} ${role === 'coach' ? styles.roleActive : ''}`}
                  onClick={() => setRole('coach')}
                >
                  <div className={styles.roleTileTop}>
                    <span className={styles.roleIcon}>🧢</span>
                    <span className={styles.roleName}>Coach</span>
                    <span className={styles.pendingBadge}>Requires Approval</span>
                  </div>
                  <p className={styles.roleDesc}>
                    Manage assigned athletes, schedule training, and record assessments.
                  </p>
                </div>

                <div
                  className={`${styles.roleTile} ${role === 'admin' ? styles.roleActive : ''}`}
                  onClick={() => setRole('admin')}
                >
                  <div className={styles.roleTileTop}>
                    <span className={styles.roleIcon}>👑</span>
                    <span className={styles.roleName}>Admin</span>
                    <span className={styles.adminBadge}>Admin Request</span>
                  </div>
                  <p className={styles.roleDesc}>
                    Academy operations, user rosters, sports, and system reporting.
                  </p>
                </div>
              </div>
            </div>

            {/* ── Form Inputs ── */}
            <div className={styles.formGroup}>
              <label htmlFor="reg-name" className={styles.label}>
                Full Name <span className={styles.required}>*</span>
              </label>
              <input
                id="reg-name"
                type="text"
                className={styles.input}
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Marcus Sprint"
                required
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="reg-email" className={styles.label}>
                Email Address <span className={styles.required}>*</span>
              </label>
              <input
                id="reg-email"
                type="email"
                className={styles.input}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="athlete@athletix.dev"
                required
              />
            </div>

            <div className={styles.row}>
              <div className={styles.formGroup}>
                <label htmlFor="reg-pass" className={styles.label}>
                  Password <span className={styles.required}>*</span>
                </label>
                <div className={styles.passWrap}>
                  <input
                    id="reg-pass"
                    type={showPassword ? 'text' : 'password'}
                    className={styles.input}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min 8 characters"
                    required
                  />
                  <button
                    type="button"
                    className={styles.toggleBtn}
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label="Toggle password visibility"
                  >
                    {showPassword ? '👁️' : '👁️‍🗨️'}
                  </button>
                </div>
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="reg-confirm" className={styles.label}>
                  Confirm Password <span className={styles.required}>*</span>
                </label>
                <input
                  id="reg-confirm"
                  type={showPassword ? 'text' : 'password'}
                  className={styles.input}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat password"
                  required
                />
              </div>
            </div>

            {/* Role Notice */}
            {role !== 'athlete' && (
              <div className={styles.noticeBox}>
                <span>🔒</span>
                <p>
                  Security notice: {role === 'coach' ? 'Coach' : 'Admin'} account requests will be
                  reviewed by academy administration before authorization is granted.
                </p>
              </div>
            )}

            <button
              type="submit"
              className={styles.submitBtn}
              disabled={loading}
            >
              {loading ? 'Creating Account…' : 'Create Athletix Account →'}
            </button>
          </form>

          <div className={styles.footerLinks}>
            <span>
              Already have an account?{' '}
              <Link to="/login" className={styles.signInLink}>
                Sign In
              </Link>
            </span>
            <Link to="/" className={styles.homeLink}>
              ← Return to Landing Page
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
