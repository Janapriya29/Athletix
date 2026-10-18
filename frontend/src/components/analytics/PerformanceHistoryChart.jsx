import React from 'react'

export default function PerformanceHistoryChart({ history = [] }) {
  if (!history || history.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--color-text-muted)' }}>
        <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>📊</div>
        <p style={{ margin: 0 }}>No assessment history recorded yet.</p>
        <p style={{ fontSize: '0.8rem', marginTop: 4 }}>
          Assessments conducted by coaches will appear here with progression curves.
        </p>
      </div>
    )
  }

  // Sort chronological (oldest to newest for left-to-right progression)
  const sorted = [...history].sort((a, b) => new Date(a.date) - new Date(b.date))

  if (sorted.length === 1) {
    const single = sorted[0]
    return (
      <div style={{ padding: '24px 16px', textAlign: 'center' }}>
        <div style={{ display: 'inline-block', backgroundColor: 'var(--color-surface-2)', padding: '12px 24px', borderRadius: 8, border: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
            Assessment Date: {new Date(single.date).toLocaleDateString()}
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--color-accent)', margin: '6px 0' }}>
            {single.overall_score}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
            Single data point recorded. At least 2 assessments are required to plot a historical trend line.
          </div>
        </div>
      </div>
    )
  }

  // Multi-point SVG chart
  const width = 600
  const height = 200
  const paddingX = 45
  const paddingY = 30

  const plotWidth = width - paddingX * 2
  const plotHeight = height - paddingY * 2

  // Scores range
  const scores = sorted.map((item) => Number(item.overall_score) || 0)
  const minScore = Math.max(0, Math.floor(Math.min(...scores) / 10) * 10 - 10)
  const maxScore = Math.min(100, Math.ceil(Math.max(...scores) / 10) * 10 + 10)
  const scoreRange = maxScore - minScore || 1

  const points = sorted.map((item, idx) => {
    const x = paddingX + (idx / (sorted.length - 1)) * plotWidth
    const normalizedY = (Number(item.overall_score) - minScore) / scoreRange
    const y = height - paddingY - normalizedY * plotHeight
    return {
      x,
      y,
      score: item.overall_score,
      date: new Date(item.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
      trend: item.trend,
    }
  })

  const pathD = points.reduce((acc, pt, i) => (i === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`), '')
  const areaD = `${pathD} L ${points[points.length - 1].x} ${height - paddingY} L ${points[0].x} ${height - paddingY} Z`

  // Grid lines
  const gridLines = [minScore, Math.round((minScore + maxScore) / 2), maxScore]

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', maxHeight: 220, display: 'block' }}
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="var(--color-accent, #FF5A1F)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="var(--color-accent, #FF5A1F)" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Horizontal grid lines */}
        {gridLines.map((gl) => {
          const y = height - paddingY - ((gl - minScore) / scoreRange) * plotHeight
          return (
            <g key={gl}>
              <line
                x1={paddingX}
                y1={y}
                x2={width - paddingX}
                y2={y}
                stroke="var(--color-border, #E5E5E5)"
                strokeDasharray="4 4"
                strokeWidth="1"
              />
              <text
                x={paddingX - 8}
                y={y + 4}
                textAnchor="end"
                fontSize="10"
                fill="var(--color-text-muted, #6B7280)"
              >
                {gl}
              </text>
            </g>
          )
        })}

        {/* Shaded Area under curve */}
        <path d={areaD} fill="url(#scoreGradient)" />

        {/* Trend Polyline */}
        <path
          d={pathD}
          fill="none"
          stroke="var(--color-accent, #FF5A1F)"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Data points & tooltips */}
        {points.map((pt, i) => (
          <g key={i}>
            <circle
              cx={pt.x}
              cy={pt.y}
              r="5"
              fill="var(--color-surface, #FFFFFF)"
              stroke="var(--color-accent, #FF5A1F)"
              strokeWidth="3"
            />
            {/* Score label above point */}
            <text
              x={pt.x}
              y={pt.y - 10}
              textAnchor="middle"
              fontSize="11"
              fontWeight="bold"
              fill="var(--color-text, #edf2f7)"
            >
              {pt.score}
            </text>
            {/* Date label under x-axis */}
            <text
              x={pt.x}
              y={height - paddingY + 16}
              textAnchor="middle"
              fontSize="10"
              fill="var(--color-text-muted, #718096)"
            >
              {pt.date}
            </text>
          </g>
        ))}
      </svg>
    </div>
  )
}
