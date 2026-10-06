import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import styles from './AppLayout.module.css'

/**
 * Main shell layout: fixed sidebar + topbar + scrollable content.
 * All authenticated pages render inside this layout.
 * Pass `title` to show the current page name in the topbar.
 */
export default function AppLayout({ children, title }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  // Auto-close mobile drawer whenever route changes
  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  return (
    <div className={styles.shell}>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className={styles.backdrop}
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      <Sidebar
        isOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
      />

      <div className={styles.content}>
        <Topbar
          title={title}
          onToggleMenu={() => setMobileOpen((prev) => !prev)}
        />
        <main className={styles.main}>
          {children}
        </main>
      </div>
    </div>
  )
}
