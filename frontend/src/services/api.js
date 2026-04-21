const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export async function fetchMetadata() {
  const response = await fetch(`${API_BASE_URL}/metadata`)

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || 'Metadata fetch failed')
  }

  return response.json()
}

export async function predictSingle(payload) {
  const response = await fetch(`${API_BASE_URL}/predict-single`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || 'Prediction failed')
  }

  return response.json()
}

export async function downloadSingleReport(payload) {
  const response = await fetch(`${API_BASE_URL}/generate-report-single`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || 'Report generation failed')
  }

  return response.blob()
}