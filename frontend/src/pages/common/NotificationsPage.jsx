import React, { useState, useEffect, useCallback } from 'react'
import AppLayout from '../../layouts/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import notificationService from '../../services/notificationService'
import styles from './NotificationsPage.module.css'

const TYPE_ICONS = {
  training: '🏃',
  performance: '📊',
  tournament: '🏆',
  general: '🔔',
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)
  const [filterType, setFilterType] = useState('all') // 'all', 'unread', 'training', 'performance', 'tournament'

  const fetchNotifications = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {}
      if (filterType === 'unread') {
        params.unread = true
      } else if (filterType !== 'all') {
        params.type = filterType
      }

      const [listData, countData] = await Promise.all([
        notificationService.getNotifications(params),
        notificationService.getUnreadCount(),
      ])
      setNotifications(listData)
      setUnreadCount(countData.unread_count || 0)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load notifications')
    } finally {
      setLoading(false)
    }
  }, [filterType])

  useEffect(() => {
    fetchNotifications()
  }, [fetchNotifications])

  async function handleMarkRead(id) {
    try {
      setActionLoading(true)
      await notificationService.markAsRead(id)
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update notification')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleMarkAllRead() {
    try {
      setActionLoading(true)
      await notificationService.markAllAsRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setUnreadCount(0)
      setSuccessMsg('All notifications marked as read')
      setTimeout(() => setSuccessMsg(null), 3000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to mark all as read')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleDelete(id) {
    try {
      setActionLoading(true)
      await notificationService.deleteNotification(id)
      setNotifications((prev) => prev.filter((n) => n.id !== id))
      fetchNotifications()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete notification')
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <AppLayout title="Notifications">
      <div className={styles.container}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.title}>Your Notifications</h2>
            <p className={styles.subtitle}>
              Stay updated with your scheduled training, assessments, tournaments, and announcements.
            </p>
          </div>
          <div className={styles.headerActions}>
            {unreadCount > 0 && (
              <button
                className={styles.markAllBtn}
                onClick={handleMarkAllRead}
                disabled={actionLoading}
              >
                ✓ Mark all as read ({unreadCount})
              </button>
            )}
            <button
              className={styles.refreshBtn}
              onClick={fetchNotifications}
              disabled={loading || actionLoading}
            >
              🔄 Refresh
            </button>
          </div>
        </div>

        {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}
        {successMsg && <div className={styles.successBanner}>{successMsg}</div>}

        {/* Filters */}
        <div className={styles.filterBar}>
          <button
            className={`${styles.filterTab} ${filterType === 'all' ? styles.activeTab : ''}`}
            onClick={() => setFilterType('all')}
          >
            All
          </button>
          <button
            className={`${styles.filterTab} ${filterType === 'unread' ? styles.activeTab : ''}`}
            onClick={() => setFilterType('unread')}
          >
            Unread {unreadCount > 0 && <span className={styles.tabBadge}>{unreadCount}</span>}
          </button>
          <button
            className={`${styles.filterTab} ${filterType === 'training' ? styles.activeTab : ''}`}
            onClick={() => setFilterType('training')}
          >
            🏃 Training
          </button>
          <button
            className={`${styles.filterTab} ${filterType === 'performance' ? styles.activeTab : ''}`}
            onClick={() => setFilterType('performance')}
          >
            📊 Performance
          </button>
          <button
            className={`${styles.filterTab} ${filterType === 'tournament' ? styles.activeTab : ''}`}
            onClick={() => setFilterType('tournament')}
          >
            🏆 Tournaments
          </button>
        </div>

        {/* Notifications List */}
        {loading ? (
          <LoadingSpinner />
        ) : notifications.length === 0 ? (
          <div className={styles.emptyState}>
            <span className={styles.emptyIcon}>🔔</span>
            <h3>No notifications found</h3>
            <p>You have no notifications matching the selected filter.</p>
          </div>
        ) : (
          <div className={styles.list}>
            {notifications.map((notif) => {
              const icon = TYPE_ICONS[notif.type] || '🔔'
              const dateStr = notif.created_at
                ? new Date(notif.created_at).toLocaleString()
                : ''

              return (
                <div
                  key={notif.id}
                  className={`${styles.card} ${!notif.is_read ? styles.unreadCard : ''}`}
                >
                  <div className={styles.cardIcon}>{icon}</div>
                  <div className={styles.cardContent}>
                    <div className={styles.cardTopRow}>
                      <span className={styles.cardTitle}>{notif.title}</span>
                      <span className={styles.cardDate}>{dateStr}</span>
                    </div>
                    <p className={styles.cardMessage}>{notif.message}</p>
                    <div className={styles.cardFooter}>
                      <span className={styles.typeTag}>{notif.type}</span>
                      <div className={styles.cardActions}>
                        {!notif.is_read && (
                          <button
                            className={styles.readBtn}
                            onClick={() => handleMarkRead(notif.id)}
                            disabled={actionLoading}
                          >
                            Mark Read
                          </button>
                        )}
                        <button
                          className={styles.deleteBtn}
                          onClick={() => handleDelete(notif.id)}
                          disabled={actionLoading}
                          title="Delete notification"
                        >
                          🗑
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
