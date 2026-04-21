# Credit Risk Analysis App

Progetto completo backend + frontend per eseguire una valutazione di **credit risk** a partire dal tuo modello neurosimbolico.

## Cosa include

### Backend FastAPI
- `GET /health`
- `GET /metadata`
- `POST /predict-single`
- `POST /predict-excel`
- `POST /generate-report-single`
- `POST /generate-report/{row_index}`

### Frontend React + Vite
- form manuale per singola azienda
- analisi batch via Excel
- visualizzazione esito, probabilità e driver principali
- download PDF del report

## Struttura

```text
credit-risk-app/
  backend/
    app/
    artifacts/
    requirements.txt
    run.py
  frontend/
    src/
    package.json
  README.md
```

## Avvio backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # su Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Backend disponibile su:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

## Avvio frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend disponibile su:

```text
http://localhost:5173
```

## Variabili ambiente

### Backend
Copia `.env.example` in `.env` se vuoi personalizzare nome app e CORS.

### Frontend
Copia `.env.example` in `.env` e imposta:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Input minimi richiesti per la singola analisi
- Current Ratio
- Debt/Equity Ratio
- EBITDA Margin
- ROA - Return On Assets
- ROE - Return On Equity
- Year
- Month

## Nota importante
Gli artifact del modello sono già inclusi in `backend/artifacts/` e il backend è configurato per leggerli da lì.
