import React, { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import notificationService from '../services/notificationService'
import styles from './Topbar.module.css'

export default function Topbar({ title, onToggleMenu }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [unreadCount, setUnreadCount] = useState(0)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [recentNotifications, setRecentNotifications] = useState([])
  const [loading, setLoading] = useState(false)
  const dropdownRef = useRef(null)

  useEffect(() => {
    if (!user) return

    let isMounted = true
    async function fetchUnread() {
      try {
        const res = await notificationService.getUnreadCount()
        if (isMounted) {
          setUnreadCount(res.unread_count || 0)
        }
      } catch {
        // quiet failure for background polling
      }
    }

    fetchUnread()
    const interval = setInterval(fetchUnread, 30000)
    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [user])

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  async function toggleDropdown() {
    if (!dropdownOpen) {
      try {
        setLoading(true)
        setDropdownOpen(true)
        const notifs = await notificationService.getNotifications({ limit: 5 })
        setRecentNotifications(notifs)
      } catch {
        // ignore
      } finally {
        setLoading(false)
      }
    } else {
      setDropdownOpen(false)
    }
  }

  async function handleMarkRead(id, e) {
    e.stopPropagation()
    try {
      await notificationService.markAsRead(id)
      setRecentNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      )
      setUnreadCount((c) => Math.max(0, c - 1))
    } catch {
      // ignore
    }
  }

  async function handleMarkAllRead(e) {
    e.stopPropagation()
    try {
      await notificationService.markAllAsRead()
      setRecentNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch {
      // ignore
    }
  }

  function handleGoToNotifications() {
    setDropdownOpen(false)
    if (user?.role === 'coach') {
      navigate('/coach/notifications')
    } else if (user?.role === 'athlete') {
      navigate('/athlete/notifications')
    } else {
      navigate('/notifications')
    }
  }

  const userInitial = (user?.full_name || user?.email || 'U').charAt(0).toUpperCase()

  return (
    <header className={styles.topbar}>
      <div className={styles.left}>
        <button
          className={styles.menuBtn}
          onClick={onToggleMenu}
          aria-label="Open navigation menu"
        >
          <span className={styles.hamburgerBar}></span>
          <span className={styles.hamburgerBar}></span>
          <span className={styles.hamburgerBar}></span>
        </button>
        <h1 className={styles.title}>{title || 'Athletix'}</h1>
      </div>
      {user && (
        <div className={styles.right}>
          {/* Notification Bell */}
          <div className={styles.bellWrapper} ref={dropdownRef}>
            <button
              className={styles.bellBtn}
              onClick={toggleDropdown}
              aria-label="Notifications"
            >
              🔔
              {unreadCount > 0 && (
                <span className={styles.badge}>
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </button>

            {dropdownOpen && (
              <div className={styles.dropdown}>
                <div className={styles.dropdownHeader}>
                  <span className={styles.dropdownTitle}>Notifications</span>
                  {unreadCount > 0 && (
                    <button
                      className={styles.dropdownMarkAll}
                      onClick={handleMarkAllRead}
                    >
                      Mark all read
                    </button>
                  )}
                </div>

                <div className={styles.dropdownBody}>
                  {loading ? (
                    <div className={styles.dropdownEmpty}>Loading...</div>
                  ) : recentNotifications.length === 0 ? (
                    <div className={styles.dropdownEmpty}>No notifications yet</div>
                  ) : (
                    recentNotifications.map((n) => (
                      <div
                        key={n.id}
                        className={`${styles.dropdownItem} ${!n.is_read ? styles.unreadItem : ''}`}
                        onClick={handleGoToNotifications}
                      >
                        <div className={styles.itemHeader}>
                          <span className={styles.itemTitle}>{n.title}</span>
                          {!n.is_read && (
                            <button
                              className={styles.itemCheckBtn}
                              onClick={(e) => handleMarkRead(n.id, e)}
                              title="Mark as read"
                            >
                              ✓
                            </button>
                          )}
                        </div>
                        <p className={styles.itemMsg}>{n.message}</p>
                      </div>
                    ))
                  )}
                </div>

                <div className={styles.dropdownFooter}>
                  <button
                    className={styles.viewAllBtn}
                    onClick={handleGoToNotifications}
                  >
                    View All Notifications →
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className={styles.userChip}>
            <div className={styles.topbarAvatar}>{userInitial}</div>
            <div className={styles.userMeta}>
              <span className={styles.name}>{user.full_name || user.email}</span>
              <span className={styles.role}>{user.role}</span>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
