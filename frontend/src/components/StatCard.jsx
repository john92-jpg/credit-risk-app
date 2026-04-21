export default function StatCard({ label, value, accent = false }) {
  return (
    <div className={`card stat-card ${accent ? 'accent' : ''}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value ?? '—'}</div>
    </div>
  )
}
