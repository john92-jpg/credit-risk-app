import { useEffect, useMemo, useState } from 'react'
import ResultPanel from './components/ResultPanel'
import { downloadSingleReport, fetchMetadata, predictSingle } from './services/api'

const fieldGroups = [
  {
    title: 'Required inputs',
    fields: [
      { label: 'Current Ratio', type: 'number', required: true },
      { label: 'Debt/Equity Ratio', type: 'number', required: true },
      { label: 'EBITDA Margin', type: 'number', required: true },
      { label: 'ROA - Return On Assets', type: 'number', required: true },
      { label: 'ROE - Return On Equity', type: 'number', required: true },
      { label: 'Year', type: 'number', required: true },
      { label: 'Month', type: 'number', required: true },
    ],
  },
  {
    title: 'Optional business context',
    fields: [
      { label: 'Corporation', type: 'text' },
      { label: 'Sector', type: 'text' },
      { label: 'Ticker', type: 'text' },
      { label: 'Long-term Debt / Capital', type: 'number' },
      { label: 'Gross Margin', type: 'number' },
      { label: 'Operating Margin', type: 'number' },
      { label: 'EBIT Margin', type: 'number' },
      { label: 'Pre-Tax Profit Margin', type: 'number' },
      { label: 'Net Profit Margin', type: 'number' },
      { label: 'Asset Turnover', type: 'number' },
      { label: 'Return On Tangible Equity', type: 'number' },
      { label: 'ROI - Return On Investment', type: 'number' },
      { label: 'Operating Cash Flow Per Share', type: 'number' },
      { label: 'Free Cash Flow Per Share', type: 'number' },
    ],
  },
]

function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function initialFormState() {
  return fieldGroups.flatMap((group) => group.fields).reduce((acc, field) => {
    acc[field.label] = ''
    return acc
  }, {})
}

export default function App() {
  const [form, setForm] = useState(initialFormState())
  const [metadata, setMetadata] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    fetchMetadata().then(setMetadata).catch((err) => setError(err.message))
  }, [])

  const requiredLabels = useMemo(() => metadata?.required_columns || [], [metadata])

  function handleChange(label, value, type) {
    setForm((prev) => ({
      ...prev,
      [label]: type === 'number' ? value : value,
    }))
  }

  function buildPayload() {
    const payload = {}
    Object.entries(form).forEach(([key, value]) => {
      if (value === '') return
      const maybeNumber = Number(value)
      payload[key] = Number.isNaN(maybeNumber) || typeof value !== 'string' || value.trim() === '' || !/^-?\d*\.?\d+$/.test(value) ? value : maybeNumber
    })
    return payload
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const payload = buildPayload()
      const data = await predictSingle(payload)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleDownloadReport() {
    setDownloading(true)
    setError('')
    try {
      const payload = buildPayload()
      const blob = await downloadSingleReport(payload)
      saveBlob(blob, 'credit-risk-report.pdf')
    } catch (err) {
      setError(err.message)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="page-shell">
      <header className="hero">
        <div>
          <div className="eyebrow">Neurosymbolic Credit Risk</div>
          <h1>Credit Risk Analysis App</h1>
          <p>
            Inserisci gli indicatori finanziari, ottieni la classe di rischio stimata, i driver principali
            e genera un report PDF pronto da presentare.
          </p>
        </div>
      </header>

      {error && <div className="error-box global-error">{error}</div>}

      <main className="main-grid">
        <section className="card form-panel">
          <h2>Single company analysis</h2>
          <p className="section-description">
            I campi obbligatori derivano dal tuo metadata di training. Obbligatori: {requiredLabels.join(', ')}
          </p>

          <form onSubmit={handleSubmit}>
            {fieldGroups.map((group) => (
              <div key={group.title} className="form-group-block">
                <h3>{group.title}</h3>
                <div className="form-grid">
                  {group.fields.map((field) => (
                    <label key={field.label} className="field">
                      <span>
                        {field.label}
                        {field.required ? ' *' : ''}
                      </span>
                      <input
                        type={field.type}
                        step={field.type === 'number' ? 'any' : undefined}
                        value={form[field.label]}
                        onChange={(event) => handleChange(field.label, event.target.value, field.type)}
                        required={field.required}
                        placeholder={field.type === 'number' ? 'Enter a numeric value' : 'Optional'}
                      />
                    </label>
                  ))}
                </div>
              </div>
            ))}

            <div className="action-row">
              <button className="primary-button" type="submit" disabled={loading}>
                {loading ? 'Running analysis...' : 'Run analysis'}
              </button>
              <button className="ghost-button" type="button" onClick={() => { setForm(initialFormState()); setResult(null); setError('') }}>
                Reset
              </button>
            </div>
          </form>
        </section>

        <section>
          <ResultPanel result={result} onDownloadReport={handleDownloadReport} downloading={downloading} />
        </section>
      </main>

    </div>
  )
}
