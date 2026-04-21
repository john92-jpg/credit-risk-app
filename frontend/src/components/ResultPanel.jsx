import StatCard from './StatCard'

export default function ResultPanel({ result, onDownloadReport, downloading }) {
  if (!result) {
    return (
      <div className="card result-panel muted-box">
        <h3>Analysis output</h3>
        <p>Compila il form e lancia l’analisi per vedere il risultato.</p>
      </div>
    )
  }

  const row = result.row
  const probability = row['ns_prob_classe_1'] != null ? `${(row['ns_prob_classe_1'] * 100).toFixed(2)}%` : '—'
  const riskLevel = (() => {
    const p = row['ns_prob_classe_1']
    if (p >= 0.75) return 'Basso'
    if (p >= 0.55) return 'Medio-Basso'
    if (p >= 0.4) return 'Medio'
    return 'Alto'
  })()

  return (
    <div className="result-panel">
      <div className="result-grid">
        <StatCard label="Corporation" value={row['Corporation'] || 'N/D'} />
        <StatCard label="Ticker" value={row['Ticker'] || 'N/D'} />
        <StatCard label="Classe prevista" value={row['ns_esito']} accent />
        <StatCard label="Probabilità classe 1" value={probability} />
        <StatCard label="Livello di rischio" value={riskLevel} />
        <StatCard label="Confidenza regola" value={row['confidenza_regola'] ?? 'N/D'} />
      </div>

{/*
      <div className="card detail-card">
        <h3>Driver principali</h3>
        <p>{row['driver_principali'] || 'N/D'}</p>
      </div>
*/}
{/*
      <div className="card detail-card">
        <h3>Traduzione della regola</h3>
        <p>{row['traduzione_regola'] || 'N/D'}</p>
      </div>
*/}

      <div className="card detail-card">
        <h3>Interpretazione del rischio</h3>
        <p>{row['interpretazione_rischio_regola'] || 'N/D'}</p>
      </div>

      <div className="action-row">
        <button className="primary-button" onClick={onDownloadReport} disabled={downloading}>
          {downloading ? 'Generating PDF...' : 'Download PDF report'}
        </button>
      </div>
    </div>
  )
}
