# 🏭 OpsPilot — AI Operations Assistant for Manufacturers

> Built for FlowZint AI Hackathon 2026 | Open Innovation Category

---

## 🌐 Live Demo

- **Frontend (app):** https://opspilot-sudarshan.netlify.app
- **Backend (API):** https://opspilot-pa3y.onrender.com

**Login credentials:**

| Role | ID | Password |
|---|---|---|
| Factory Owner | `OWNER` | `SG2026` |
| Factory Manager | `MANAGER` | `SG2026` |
| QC Inspector | `QC` | `SG2026` |

> Note: the backend is hosted on Render's free tier, which spins down after ~15 minutes of inactivity. The first request after idle time may take 30–50 seconds to respond while it wakes up — this is expected, not a bug.

---

## 📹 Demo Video

[Link to demo video — coming soon]

---

## 🎯 The Problem

When Rudra worked at Sudarshan Gears — a gear
manufacturing company in Mira Road, Thane — he
witnessed firsthand how small manufacturers
struggle daily:

- **Every morning** managers spent 45 minutes
  just figuring out what happened the day before
- **Machines sat idle** because nobody knew
  raw material hadn't arrived yet
- **Quality defects repeated** because nothing
  was ever properly logged
- **Vendors delayed** and nobody knew until
  the machine was already waiting
- **Everything lived** in Excel sheets, physical
  registers, WhatsApp messages and Tally —
  completely disconnected

**The result:** Wrong decisions based on wrong
information. Every single day.

---

## 💡 The Solution

OpsPilot is a role-based operations dashboard with
a built-in AI assistant that gives any manufacturer
a real-time view of their entire operation — for
Owners, Managers, and QC Inspectors alike.

Ask the AI anything:
- *"What should I focus on today?"*
- *"Is Machine 3 free for the next job?"*
- *"Why is Job J002 delayed?"*
- *"Do we have enough material for the
   Tata AutoComp order?"*
- *"Any repeat quality issues this week?"*

OpsPilot connects information across all
operational data sources, reasons about
cause and effect, and gives prioritized,
actionable responses — in seconds.

---

## 🏗️ Architecture

```
Google Sheets (Live Data)
        ↓
FastAPI backend reads all 7 data sources
        ↓
Pattern Analyzer detects issues (Event_Log)
        ↓
Structured RAG — data packaged as AI context
        ↓
OpenAI GPT-4o mini reasons across all data
        ↓
Single-file HTML/Tailwind/JS frontend renders
   role-based dashboard + chat
        ↓
Worker updates data via chat or dashboard action
        ↓
Google Sheets updated instantly
```

---

## ✨ Features

### 🔐 Role-Based Dashboards
Three distinct views — Owner (revenue, customer
health, vendor reliability), Manager (production
timelines, machine allocation, gearbox assembly),
and QC (defect history, repeat alerts, stage
analysis).

### 💬 Conversational AI Assistant
Ask anything in plain English, scoped to your
role. OpsPilot reads live data and gives
intelligent, contextual responses — including
quick actions like "Ripple Effect" and "Draft
Vendor Message."

### 📊 Live Dashboard
Real-time view of:
- Material stock levels with reorder alerts
- Machine status and idle time tracking
- Active production jobs and stages
- Vendor delivery status and overdue detection
- Quality defect log
- Gearbox assembly progress and completion %

### 🔍 Cross-Sheet Reasoning
OpsPilot connects information across all
7 data sources to explain causation:
*"Machine M003 is idle because Vendor V002
is 7 days late on EN19 steel rods needed
for Job J002"*

### 📝 Two-Way Updates
Workers log events directly from the UI:
- Machine breakdowns
- Quality defects
- Vendor delays
- Stage completions

OpsPilot writes everything to Google Sheets
automatically — no spreadsheet skills needed.

### 🔮 Pattern Detection
Reads the Event_Log once per session (to respect
Sheets API quotas) and detects:
- Which machines break down most often
- Which vendors are consistently late
- Which parts have repeat quality defects
- When to reorder materials proactively

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | FastAPI (Python 3.12) | REST API, business logic |
| Frontend | Single HTML file (Tailwind CSS + Vanilla JS) | Chat + Dashboard UI |
| AI Brain | OpenAI GPT-4o mini | Natural language reasoning |
| Data | Google Sheets (gspread) | Live operational database |
| RAG | Structured RAG (not vector DB) | Context built directly from Sheets data |
| Pattern Detection | Python, rule-based | Event log analysis |
| Backend Hosting | Render | Live API |
| Frontend Hosting | Netlify | Live static site |

---

## 📁 Project Structure

```
OpsPilot/
├── backend/
│   └── main.py                # FastAPI — all endpoints
├── frontend/
│   └── index.html             # Single-file frontend
├── modules/
│   ├── __init__.py
│   ├── system_prompt.py       # AI personality + role behavior
│   ├── sheets_connector.py    # Google Sheets connection + update_by_id()
│   ├── ai_engine.py           # RAG + AI responses
│   ├── event_logger.py        # Event logging
│   └── pattern_analyzer.py    # Pattern detection
├── tests/
│   ├── test_ai.py             # Manual smoke test — AI + Sheets connection
│   └── test_connection.py     # Manual smoke test — Sheets connection only
├── credentials.json           # NOT committed (gitignored)
├── .env                       # NOT committed (gitignored)
├── .env.example                # Template for required env vars
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # + local-only dependencies (Ollama fallback)
└── README.md
```

---

## 📊 Data Sources (Google Sheets)

Spreadsheet: **"OpsPilot - Sudarshan Gears"**

| Sheet | Tracks |
|---|---|
| Material_Ledger | Steel rod batches, quantities, entry/exit dates |
| Production_Jobs | Active jobs, stages, assignments, unit price |
| Machines | Status, runtime, idle time, operators |
| Vendors | Deliveries, reliability scores |
| Quality_Log | Defects, actions, decisions |
| Event_Log | All logged events for pattern analysis |
| Gearbox_Assembly | Multi-part gearbox orders and completion status |

---

## ⚙️ How to Run Locally

### Prerequisites
- Python 3.12+
- A Google Cloud project with Sheets + Drive APIs enabled
- An OpenAI API key
- (Optional) Ollama installed, for local AI fallback

### Setup

**1. Clone the repo**
```bash
git clone https://github.com/RKM7-art/OpsPilot.git
cd OpsPilot
```

**2. Create virtual environment**
```bash
python -m venv venv --copies
source venv/Scripts/activate   # Windows Git Bash
source venv/bin/activate        # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements-dev.txt
```

**4. Set up Google Sheets API**
- Create a Google Cloud project
- Enable the Sheets and Drive APIs
- Create a Service Account, download its JSON key
- Save it as `credentials.json` in the project root

**5. Set up environment variables**
```bash
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

**6. Run the backend**
```bash
uvicorn backend.main:app --reload --port 8000
```

**7. Open the frontend**
```bash
start frontend/index.html   # Windows
open frontend/index.html    # Mac
```
> For local development, `frontend/index.html` should point its `API` constant at `http://localhost:8000`. The deployed version points at the live Render URL instead.

---

## ☁️ Deployment Notes

- **Backend (Render):** deployed from `main`, build command
  `pip install -r requirements.txt`, start command
  `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
  Since `credentials.json` is gitignored, production reads
  credentials from a `GOOGLE_CREDENTIALS` environment variable
  instead (raw JSON contents) — see `connect_to_sheets()` in
  `modules/sheets_connector.py`.
- **Frontend (Netlify):** deployed from `main`, publish
  directory set to `frontend`, no build step needed since it's
  a single static HTML file.

---

## 🏭 Demo Company

OpsPilot is demonstrated using **Sudarshan Gears**
— a gear manufacturing company in Mira Road,
Thane, Maharashtra — as the reference implementation.

The scenarios, data and pain points are based on
real operational challenges observed in small gear
manufacturing units in the Mumbai-Thane industrial
belt, aligned with Indian MSME manufacturing
industry standards.

OpsPilot works for ANY small manufacturer —
gears, auto parts, 3D printed components,
electronics assembly. Sudarshan Gears is our
proof of concept.

---

## 🗺️ Roadmap

### Phase 1 (Current — Hackathon)
- ✅ Role-based login and dashboards
- ✅ Conversational AI assistant per role
- ✅ Live Google Sheets integration
- ✅ Cross-sheet reasoning
- ✅ Pattern detection
- ✅ Two-way data updates (event logging + sheet updates from AI)
- ✅ Deployed backend (Render) and frontend (Netlify)

### Phase 2 (Post-Hackathon)
- Vector similarity search for Event_Log
- WhatsApp integration for shop floor workers
- Mobile-optimized interface
- Basic ML models as Event_Log grows

### Phase 3 (Scale)
- Multi-company support
- IoT sensor integration
- Full predictive ML models
- ERP integration (Tally, SAP)

---

## 👤 Built By

**Rudra K. Mehta** — FlowZint AI Hackathon 2026

*"I built OpsPilot because I lived the problem.
Every morning at Sudarshan Gears was chaos —
machines idle, vendors late, defects repeating.
OpsPilot is what we needed but didn't have."*

---

## 📄 License

MIT License — see LICENSE file for details.