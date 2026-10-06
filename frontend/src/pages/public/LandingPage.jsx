import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import styles from './LandingPage.module.css'

export default function LandingPage() {
  const { user } = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const dashboardRoute =
    user?.role === 'admin'
      ? '/admin/dashboard'
      : user?.role === 'coach'
      ? '/coach/dashboard'
      : '/athlete/dashboard'

  return (
    <div className={styles.page}>
      {/* ── Navigation Header ── */}
      <header className={styles.header}>
        <div className={styles.navContainer}>
          <div className={styles.brand}>
            <span className={styles.brandLogo}>⚡</span>
            <span className={styles.brandName}>ATHLETIX</span>
            <span className={styles.brandTag}>SPORTS TECH</span>
          </div>

          <nav className={`${styles.navLinks} ${mobileMenuOpen ? styles.mobileOpen : ''}`}>
            <a href="#features" onClick={() => setMobileMenuOpen(false)}>Features</a>
            <a href="#sports" onClick={() => setMobileMenuOpen(false)}>Sports</a>
            <a href="#performance" onClick={() => setMobileMenuOpen(false)}>Performance</a>
            <a href="#roles" onClick={() => setMobileMenuOpen(false)}>Roles</a>
            <a href="#rankings" onClick={() => setMobileMenuOpen(false)}>Rankings</a>
          </nav>

          <div className={styles.headerActions}>
            {user ? (
              <Link to={dashboardRoute} className={styles.btnPrimary}>
                Dashboard →
              </Link>
            ) : (
              <>
                <Link to="/login" className={styles.btnGhost}>
                  Sign In
                </Link>
                <Link to="/register" className={styles.btnPrimary}>
                  Create Account
                </Link>
              </>
            )}

            <button
              className={styles.menuToggle}
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? '✕' : '☰'}
            </button>
          </div>
        </div>
      </header>

      {/* ── Hero Section ── */}
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <div className={styles.heroBadge}>
            <span className={styles.pulseDot}></span>
            <span>NEXT-GEN SPORTS ACADEMY PLATFORM</span>
          </div>
          <h1 className={styles.heroTitle}>
            ELEVATE YOUR GAME.<br />
            <span className={styles.titleGradient}>MEASURE YOUR PROGRESS.</span>
          </h1>
          <p className={styles.heroSubtitle}>
            A unified, data-driven sports performance and academy management platform
            engineered for athletes, coaches, and academy administrators.
          </p>
          <div className={styles.heroButtons}>
            <Link to="/register" className={styles.btnHeroPrimary}>
              Get Started Free →
            </Link>
            <a href="#features" className={styles.btnHeroSecondary}>
              Explore Platform
            </a>
          </div>

          {/* Quick Metrics Bar */}
          <div className={styles.metricStrip}>
            <div className={styles.metricItem}>
              <span className={styles.metricNum}>0–100</span>
              <span className={styles.metricLabel}>Assessment Scale</span>
            </div>
            <div className={styles.metricDivider}></div>
            <div className={styles.metricItem}>
              <span className={styles.metricNum}>&lt;75%</span>
              <span className={styles.metricLabel}>Attendance Warning</span>
            </div>
            <div className={styles.metricDivider}></div>
            <div className={styles.metricItem}>
              <span className={styles.metricNum}>🥇🥈🥉</span>
              <span className={styles.metricLabel}>Olympic Podiums</span>
            </div>
            <div className={styles.metricDivider}></div>
            <div className={styles.metricItem}>
              <span className={styles.metricNum}>Multi-Sport</span>
              <span className={styles.metricLabel}>Academy Ready</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Sports Section ── */}
      <section id="sports" className={styles.section}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionEyebrow}>MULTI-SPORT SYSTEM</span>
          <h2 className={styles.sectionTitle}>Supported Academy Sports</h2>
          <p className={styles.sectionSubtitle}>
            Configurable sport categories and athlete rosters tailored to each discipline.
          </p>
        </div>

        <div className={styles.sportsGrid}>
          <div className={styles.sportCard}>
            <div className={styles.sportIcon}>⚽</div>
            <h3>Football</h3>
            <p>Tactical sessions, speed drills, shooting, and match play metrics.</p>
          </div>
          <div className={styles.sportCard}>
            <div className={styles.sportIcon}>🏏</div>
            <h3>Cricket</h3>
            <p>Net training, bowling accuracy, batting strike rate, and fielding assessments.</p>
          </div>
          <div className={styles.sportCard}>
            <div className={styles.sportIcon}>🏸</div>
            <h3>Badminton</h3>
            <p>Court agility, reflex speed, smash power, and tournament conditioning.</p>
          </div>
          <div className={styles.sportCard}>
            <div className={styles.sportIcon}>🏀</div>
            <h3>Basketball</h3>
            <p>Shooting percentage, playmaking, transition defense, and physical stamina.</p>
          </div>
          <div className={styles.sportCard}>
            <div className={styles.sportIcon}>🏃</div>
            <h3>Athletics</h3>
            <p>Sprint split times, block mechanics, endurance intervals, and technical form.</p>
          </div>
          <div className={styles.sportCard}>
            <div className={styles.sportIcon}>🏅</div>
            <h3>Custom Sports</h3>
            <p>Add new disciplines dynamically with sport-specific metrics on the fly.</p>
          </div>
        </div>
      </section>

      {/* ── Features Section ── */}
      <section id="features" className={styles.sectionAlt}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionEyebrow}>INTEGRATED CAPABILITIES</span>
          <h2 className={styles.sectionTitle}>Built for Serious Athletic Development</h2>
          <p className={styles.sectionSubtitle}>
            All core modules work together as a synchronized performance engine.
          </p>
        </div>

        <div className={styles.featuresGrid}>
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>📊</div>
            <h3>Performance Analytics</h3>
            <p>
              Trend analysis (Improving, Stable, Declining), strongest and weakest metric
              identification, and historical benchmark charts.
            </p>
          </div>
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>📅</div>
            <h3>Training Management</h3>
            <p>
              Complete scheduling workflow: venue, start/end time validation, coach assignment,
              and participant rosters.
            </p>
          </div>
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>⏱️</div>
            <h3>Attendance Tracking</h3>
            <p>
              Per-session recording (Present, Late, Absent). Automated percentage calculations with
              strict exclusion of cancelled sessions.
            </p>
          </div>
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>🏆</div>
            <h3>Tournaments & Results</h3>
            <p>
              Full tournament lifecycle: registration deadlines, participant verification, podium
              medals (Gold, Silver, Bronze), and point tallies.
            </p>
          </div>
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>🥇</div>
            <h3>Leaderboards & Rankings</h3>
            <p>
              Deterministic multi-tier rankings across tournament points, performance scores,
              attendance rates, and improvement deltas.
            </p>
          </div>
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>📑</div>
            <h3>Reports & Data Export</h3>
            <p>
              Executive academy summaries, athlete development profiles, and clean CSV data
              downloads ready for stakeholder reporting.
            </p>
          </div>
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>🔔</div>
            <h3>In-App Notifications</h3>
            <p>
              Real-time alerts for scheduled sessions, recorded attendance, new assessments, and
              tournament podium placements.
            </p>
          </div>
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>🛡️</div>
            <h3>Role-Based Security</h3>
            <p>
              Strict separation of concerns between Academy Admins, Coaches, and Athletes, with
              ownership-level data isolation.
            </p>
          </div>
        </div>
      </section>

      {/* ── Performance Showcase Section ── */}
      <section id="performance" className={styles.section}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionEyebrow}>DATA-DRIVEN METHODOLOGY</span>
          <h2 className={styles.sectionTitle}>Precision Athlete Evaluation</h2>
          <p className={styles.sectionSubtitle}>
            Every metric is calculated from real assessments, training records, and competitive results.
          </p>
        </div>

        <div className={styles.showcaseGrid}>
          <div className={styles.showcaseCard}>
            <div className={styles.showcaseHeader}>
              <span className={styles.showcasePill}>SAMPLE ATHLETE PROFILE</span>
              <span className={styles.trendGreen}>↑ Improving Trend</span>
            </div>
            <div className={styles.scoreRow}>
              <div>
                <span className={styles.scoreValue}>88.5</span>
                <span className={styles.scoreMax}>/100</span>
                <div className={styles.scoreLabel}>Current Performance Score</div>
              </div>
              <div className={styles.scoreDelta}>
                <span className={styles.deltaValue}>+11.5%</span>
                <span className={styles.deltaLabel}>Progression vs baseline</span>
              </div>
            </div>

            <div className={styles.metricsBarList}>
              <div className={styles.metricBarItem}>
                <div className={styles.barMeta}>
                  <span>Speed & Acceleration (Strongest)</span>
                  <span className={styles.barScore}>92/100</span>
                </div>
                <div className={styles.barTrack}>
                  <div className={styles.barFill} style={{ width: '92%' }}></div>
                </div>
              </div>

              <div className={styles.metricBarItem}>
                <div className={styles.barMeta}>
                  <span>Tactical Awareness</span>
                  <span className={styles.barScore}>87/100</span>
                </div>
                <div className={styles.barTrack}>
                  <div className={styles.barFill} style={{ width: '87%' }}></div>
                </div>
              </div>

              <div className={styles.metricBarItem}>
                <div className={styles.barMeta}>
                  <span>Endurance & Stamina</span>
                  <span className={styles.barScore}>85/100</span>
                </div>
                <div className={styles.barTrack}>
                  <div className={styles.barFill} style={{ width: '85%' }}></div>
                </div>
              </div>

              <div className={styles.metricBarItem}>
                <div className={styles.barMeta}>
                  <span>Defensive Recovery</span>
                  <span className={styles.barScore}>78/100</span>
                </div>
                <div className={styles.barTrack}>
                  <div className={styles.barFill} style={{ width: '78%' }}></div>
                </div>
              </div>
            </div>

            <div className={styles.attendancePreview}>
              <div className={styles.attItem}>
                <span className={styles.attValue}>94%</span>
                <span className={styles.attLabel}>Attendance Rate</span>
              </div>
              <div className={styles.attItem}>
                <span className={styles.attValue}>0</span>
                <span className={styles.attLabel}>Warning Triggers</span>
              </div>
              <div className={styles.attItem}>
                <span className={styles.attValue}>1st</span>
                <span className={styles.attLabel}>Podium Ranking</span>
              </div>
            </div>
          </div>

          <div className={styles.showcaseSide}>
            <div className={styles.sideCard}>
              <h4>🎯 Deterministic Formula</h4>
              <p>
                Metrics are aggregated with arithmetic mean on a normalized 0–100 scale.
                Outliers and trend deltas reflect true developmental progression.
              </p>
            </div>
            <div className={styles.sideCard}>
              <h4>⏱️ Attendance Rigor</h4>
              <p>
                Athletes below 75% attendance automatically flag system warnings. Cancelled
                sessions are never counted against athlete commitment.
              </p>
            </div>
            <div className={styles.sideCard}>
              <h4>🥇 Medal & Points Parity</h4>
              <p>
                Gold medals (10 pts), Silver medals (7 pts), and Bronze medals (5 pts) award
                transparent points that feed into academy-wide rankings.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Role Section ── */}
      <section id="roles" className={styles.sectionAlt}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionEyebrow}>TAILORED EXPERIENCES</span>
          <h2 className={styles.sectionTitle}>Built for Everyone in the Academy</h2>
          <p className={styles.sectionSubtitle}>
            Dedicated portal views tailored to the exact workflows of every user role.
          </p>
        </div>

        <div className={styles.rolesGrid}>
          <div className={styles.roleCard}>
            <div className={styles.roleIcon}>👑</div>
            <span className={styles.roleBadge}>ACADEMY OPERATIONS</span>
            <h3>Admin Portal</h3>
            <p>
              Full control over academy operations, sports rosters, coach assignments,
              tournament schedules, executive reporting, and CSV exports.
            </p>
            <ul className={styles.roleList}>
              <li>✓ Manage Sports & Categories</li>
              <li>✓ Coach & Athlete Roster Assignment</li>
              <li>✓ Academy Executive Reports</li>
              <li>✓ Account Approval & User Access</li>
            </ul>
            <Link to="/login" className={styles.btnRole}>
              Sign In as Admin →
            </Link>
          </div>

          <div className={styles.roleCard}>
            <div className={styles.roleIcon}>🧢</div>
            <span className={styles.roleBadge}>TRAINING & ASSESSMENT</span>
            <h3>Coach Portal</h3>
            <p>
              Focused exclusively on assigned athletes. Schedule training, take attendance,
              record performance assessments, and enter tournaments.
            </p>
            <ul className={styles.roleList}>
              <li>✓ View Assigned Athlete Rosters</li>
              <li>✓ Schedule Training & Mark Attendance</li>
              <li>✓ Record 0–100 Performance Scores</li>
              <li>✓ Register Athletes for Competitions</li>
            </ul>
            <Link to="/register" className={styles.btnRole}>
              Apply as Coach →
            </Link>
          </div>

          <div className={styles.roleCard}>
            <div className={styles.roleIcon}>⚡</div>
            <span className={styles.roleBadge}>SELF DEVELOPMENT</span>
            <h3>Athlete Portal</h3>
            <p>
              Personalized athletic headquarters. View scheduled training, monitor attendance
              percentages, track performance curves, and check rankings.
            </p>
            <ul className={styles.roleList}>
              <li>✓ Personal Training Calendar</li>
              <li>✓ Attendance & Warning Tracker (&lt;75%)</li>
              <li>✓ Historical Performance Charts</li>
              <li>✓ Tournament Standings & Medals</li>
            </ul>
            <Link to="/register" className={styles.btnRolePrimary}>
              Join as Athlete →
            </Link>
          </div>
        </div>
      </section>

      {/* ── Rankings Preview Section ── */}
      <section id="rankings" className={styles.section}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionEyebrow}>ACADEMY LEADERBOARDS</span>
          <h2 className={styles.sectionTitle}>Competitive Excellence Recognized</h2>
          <p className={styles.sectionSubtitle}>
            Real-time leaderboards ranked across tournaments, assessments, attendance, and improvement.
          </p>
        </div>

        <div className={styles.podiumContainer}>
          <div className={styles.podiumCard}>
            <div className={styles.podiumBadge}>🥈 2nd Place</div>
            <div className={styles.podiumAvatar}>Silver</div>
            <h4>Championship Runner-Up</h4>
            <span className={styles.podiumPoints}>7.0 Points</span>
            <span className={styles.podiumMedals}>1 Silver Medal</span>
          </div>

          <div className={`${styles.podiumCard} ${styles.goldCard}`}>
            <div className={styles.goldCrown}>👑</div>
            <div className={styles.podiumBadgeGold}>🥇 1st Place</div>
            <div className={styles.podiumAvatarGold}>Gold</div>
            <h4>Tournament Champion</h4>
            <span className={styles.podiumPoints}>10.0 Points</span>
            <span className={styles.podiumMedals}>1 Gold Medal</span>
          </div>

          <div className={styles.podiumCard}>
            <div className={styles.podiumBadge}>🥉 3rd Place</div>
            <div className={styles.podiumAvatar}>Bronze</div>
            <h4>Podium Finisher</h4>
            <span className={styles.podiumPoints}>5.0 Points</span>
            <span className={styles.podiumMedals}>1 Bronze Medal</span>
          </div>
        </div>
      </section>

      {/* ── Call to Action ── */}
      <section className={styles.ctaSection}>
        <div className={styles.ctaContainer}>
          <h2>READY TO ELEVATE PERFORMANCE?</h2>
          <p>
            Join Athletix today to modernize training, measure real progression, and unlock
            athletic potential across every sport.
          </p>
          <div className={styles.ctaButtons}>
            <Link to="/register" className={styles.btnCtaPrimary}>
              Create Account Now →
            </Link>
            <Link to="/login" className={styles.btnCtaSecondary}>
              Sign In to Your Portal
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className={styles.footer}>
        <div className={styles.footerContainer}>
          <div className={styles.footerBrand}>
            <div className={styles.brand}>
              <span className={styles.brandLogo}>⚡</span>
              <span className={styles.brandName}>ATHLETIX</span>
            </div>
            <p className={styles.footerTagline}>
              Integrated Sports Performance & Academy Management Platform.
              <br />
              <strong>TRAIN SMARTER. PERFORM BETTER.</strong>
            </p>
          </div>

          <div className={styles.footerLinks}>
            <div className={styles.linkCol}>
              <h4>Navigation</h4>
              <a href="#features">Features</a>
              <a href="#sports">Sports</a>
              <a href="#performance">Performance</a>
              <a href="#rankings">Rankings</a>
            </div>
            <div className={styles.linkCol}>
              <h4>Portals</h4>
              <Link to="/login">Sign In</Link>
              <Link to="/register">Create Account</Link>
              <Link to="/notifications">Alerts</Link>
            </div>
            <div className={styles.linkCol}>
              <h4>Academy</h4>
              <span>Bangalore, India</span>
              <span>FastAPI • React • MongoDB</span>
              <span>Version 1.0.0 Production</span>
            </div>
          </div>
        </div>
        <div className={styles.footerBottom}>
          <span>© {new Date().getFullYear()} Athletix Academy. All rights reserved.</span>
        </div>
      </footer>
    </div>
  )
}
