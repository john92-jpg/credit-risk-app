import { useState } from 'react'
import { downloadExcelRowReport, predictExcel } from '../services/api'

function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function BatchUpload() {
  const [file, setFile] = useState(null)
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [downloadingRow, setDownloadingRow] = useState(null)

  async function handleAnalyze() {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const data = await predictExcel(file)
      setRows(data.rows || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleDownloadRow(index) {
    if (!file) return
    setDownloadingRow(index)
    setError('')
    try {
      const blob = await downloadExcelRowReport(file, index)
      saveBlob(blob, `credit-risk-report-row-${index}.pdf`)
    } catch (err) {
      setError(err.message)
    } finally {
      setDownloadingRow(null)
    }
  }

  return (
    <div className="card batch-panel">
      <h2>Batch analysis via Excel</h2>
      <p className="section-description">Usa questa modalità per analizzare più aziende in una sola esecuzione.</p>

      <div className="upload-row">
        <input
          type="file"
          accept=".xlsx,.xls"
          onChange={(event) => {
            setFile(event.target.files?.[0] || null)
            setRows([])
          }}
        />
        <button className="secondary-button" onClick={handleAnalyze} disabled={!file || loading}>
          {loading ? 'Analyzing...' : 'Analyze Excel'}
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}

      {rows.length > 0 && (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Corporation</th>
                <th>Ticker</th>
                <th>Prediction</th>
                <th>Probability</th>
                <th>Report</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={index}>
                  <td>{index}</td>
                  <td>{row['Corporation'] || 'N/D'}</td>
                  <td>{row['Ticker'] || 'N/D'}</td>
                  <td>{row['ns_esito']}</td>
                  <td>{row['ns_prob_classe_1'] != null ? `${(row['ns_prob_classe_1'] * 100).toFixed(2)}%` : '—'}</td>
                  <td>
                    <button
                      className="table-button"
                      onClick={() => handleDownloadRow(index)}
                      disabled={downloadingRow === index}
                    >
                      {downloadingRow === index ? 'Generating...' : 'PDF'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
