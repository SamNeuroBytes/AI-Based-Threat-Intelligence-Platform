# ThreatLens — AI-Based Threat Intelligence Platform

An end-to-end platform that **aggregates real threat intelligence from open-source feeds**,
runs an **unsupervised ML anomaly detector** over every indicator, generates
**AI-written analyst alerts**, and visualizes everything on a live security dashboard.

---

## ✨ Features

| Area | What it does |
|---|---|
| **Live data ingestion** | Pulls real indicators of compromise (IOCs) from URLhaus, ThreatFox, and AbuseIPDB on a schedule |
| **ML anomaly detection** | Extracts 8 lexical features (entropy, digit ratio, risky TLDs, suspicious keywords, etc.) and runs an `IsolationForest` to flag indicators that "look wrong" structurally — independent of the feed's own confidence score |
| **AI-generated alerts** | High-severity indicators get a 2–3 sentence plain-English summary + recommended action, generated via the Anthropic API (with a smart template fallback if no key is set) |
| **Dashboard UI** | Dark, glassmorphism-styled React dashboard with trend charts, severity breakdowns, source distribution, and a scatter plot of confidence vs. anomaly score |
| **Filterable indicator explorer** | Search/filter 100s of IOCs by type, severity, source, and ML label |
| **Alert triage workflow** | Acknowledge/resolve alerts, filter by status |
| **Scheduled jobs** | Background scheduler re-ingests data, retrains the model, and regenerates alerts hourly |

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│  Open Threat     │     │   FastAPI         │     │   React Dashboard   │
│  Feeds           │────▶│   Backend         │────▶│   (Vite + Tailwind  │
│  - URLhaus       │     │                   │     │    + Recharts)      │
│  - ThreatFox     │     │  ┌─────────────┐  │     │                     │
│  - AbuseIPDB     │     │  │ Ingestion   │  │     │  - Overview         │
└─────────────────┘     │  │ Service     │  │     │  - Indicators       │
                         │  └─────┬───────┘  │     │  - Alerts           │
                         │        ▼          │     │  - ML Insights      │
                         │  ┌─────────────┐  │     └────────────────────┘
                         │  │ SQLite DB   │  │
                         │  │ (Indicator, │  │
                         │  │  Alert)     │  │
                         │  └─────┬───────┘  │
                         │        ▼          │
                         │  ┌─────────────┐  │
                         │  │ IsolationFor│  │
                         │  │ est (sklearn│  │
                         │  └─────┬───────┘  │
                         │        ▼          │
                         │  ┌─────────────┐  │
                         │  │ LLM Summary │  │
                         │  │ (Anthropic) │  │
                         │  └─────────────┘  │
                         └───────────────────┘
```

---

## 🚀 Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt

# (Optional) for live AbuseIPDB data — free key from https://www.abuseipdb.com/
export ABUSEIPDB_KEY=your_key_here

# (Optional) for AI-generated alert summaries
export ANTHROPIC_API_KEY=your_key_here

# Seed with realistic sample data (instant demo, no internet needed)
python -m app.services.seed_data

# Run the API
python -m uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

### 3. Generate ML scores + alerts

```bash
curl -X POST http://localhost:8000/api/retrain
curl -X POST http://localhost:8000/api/ingest
```

(These also run automatically every hour via the built-in scheduler.)

---

## 🔑 API Keys (all optional — the platform works without them)

| Service | Used for | Get a free key |
|---|---|---|
| AbuseIPDB | Real malicious IP blacklist | https://www.abuseipdb.com/register |
| Anthropic | AI-generated alert summaries | https://console.anthropic.com/ |

URLhaus and ThreatFox require **no key** but do require outbound HTTPS access
to `*.abuse.ch`. If that's blocked in your environment, use the seed script
for demo data — all ML/AI/UI features still work identically.

---

## 📡 API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/stats` | Dashboard summary stats (counts, trends, breakdowns) |
| GET | `/api/indicators` | List/filter indicators (`severity`, `ioc_type`, `source`, `ml_label`, `search`) |
| GET | `/api/indicators/{id}` | Single indicator detail |
| GET | `/api/alerts` | List alerts (`acknowledged=0/1`, `severity`) |
| POST | `/api/alerts/{id}/acknowledge` | Mark an alert resolved |
| POST | `/api/ingest` | Trigger ingestion + scoring + alerting cycle |
| POST | `/api/retrain` | Retrain the IsolationForest on current data |

---

## 🧠 ML Model Details

The anomaly detector uses **lexical features only** (no external lookups needed),
making it fast and fully explainable:

- **Length** — total character count
- **Digit ratio** — proportion of digits (DGA domains often have many)
- **Special character count** — common in obfuscated phishing URLs
- **Shannon entropy** — randomness measure; high entropy ≈ algorithmically generated
- **Subdomain depth** — number of `.`-separated segments
- **Suspicious keyword flag** — `login`, `verify`, `secure`, `bank`, etc.
- **Risky TLD flag** — `.xyz`, `.top`, `.tk`, `.ml`, `.ga`, `.cf`, `.click`, `.loan`, `.work`
- **Source confidence** — the feed's own reported confidence score

These are fed into `sklearn.ensemble.IsolationForest` (150 estimators,
contamination=0.15), which assigns every indicator an anomaly score (0–100)
and a `normal` / `anomalous` label. The model retrains on the full dataset
each cycle, so it adapts as new threat patterns emerge.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite, APScheduler
- **ML**: scikit-learn, pandas
- **AI**: Anthropic Claude API (alert summarization)
- **Frontend**: React 18, Vite, Tailwind CSS, Recharts, Lucide icons

---

## 📄 Resume Bullet Points

- Built a full-stack AI threat intelligence platform aggregating live IOC
  data from 3 open-source feeds (URLhaus, ThreatFox, AbuseIPDB) via a FastAPI
  backend with scheduled ingestion jobs
- Designed and trained an unsupervised **IsolationForest anomaly detection
  model** using 8 engineered lexical features (entropy, DGA heuristics, TLD
  risk scoring) to flag suspicious indicators independent of source confidence
- Integrated the **Anthropic Claude API** to auto-generate analyst-ready
  threat summaries and recommended actions for high-severity alerts
- Developed a responsive **React + Recharts dashboard** with real-time stats,
  severity/source breakdowns, filterable IOC explorer, and an alert triage
  workflow
- Implemented a clean REST API (7 endpoints) with SQLAlchemy ORM and a
  background scheduler for hourly re-ingestion and model retraining

---

## 🔮 Future Enhancements

- Authentication & role-based access (analyst vs. admin)
- Slack/email webhook notifications for critical alerts
- Geo-IP mapping of attack origins
- Docker Compose for one-command deployment
- PostgreSQL + Elasticsearch for production-scale data
- CI/CD pipeline with GitHub Actions + automated tests
