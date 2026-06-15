# 🏭 OpsPilot — AI Operations Assistant for Manufacturers

> Built for FlowZint AI Hackathon 2026 | Open Innovation Category

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

OpsPilot is a conversational AI operations 
assistant that gives any manufacturer a 
real-time view of their entire operation 
through a single chat interface.

Ask it anything:
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
Google Sheets (Live Data)

↓

Python reads all 6 data sources

↓

Pattern Analyzer detects issues

↓

RAG — data packaged as AI context

↓

LLM reasons across all data

↓

Streamlit displays response + dashboard

↓

Worker can update data via chat

↓

Google Sheets updated instantly

---

## ✨ Features

### 🌅 Proactive Morning Briefing
Automatically shows critical alerts when 
app loads — no questions needed.

### 💬 Conversational AI Assistant
Ask anything in plain English. OpsPilot 
reads live data and gives intelligent, 
contextual responses.

### 📊 Live Dashboard
Real-time view of:
- Material stock levels with reorder alerts
- Machine status and idle time tracking  
- Active production jobs and stages
- Vendor delivery status
- Quality defect log

### 🔍 Cross-Sheet Reasoning
OpsPilot connects information across all 
6 data sources to explain causation:
*"Machine M003 is idle because Vendor V002 
is 7 days late on EN19 steel rods needed 
for Job J002"*

### 📝 Two-Way Updates
Workers report events via chat:
- Machine breakdowns
- Quality defects
- Vendor delays
- Stage completions

OpsPilot logs everything to Google Sheets 
automatically — no Excel skills needed.

### 🔮 Pattern Detection
Identifies recurring issues:
- Which machines break down most often
- Which vendors are consistently late
- Which parts have repeat quality defects
- When to reorder materials proactively

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Streamlit | Chat + Dashboard UI |
| AI Brain | OpenAI GPT-4 / LLaMA 3.2 | Natural language reasoning |
| Data | Google Sheets | Live operational database |
| RAG | gspread + build_context() | Structured retrieval augmentation |
| Pattern Detection | Python rule-based | Event log analysis |
| Backend | Python 3.12 | Core application logic |
| Deployment | Streamlit Cloud | Live public access |

---

## 📁 Project Structure
OpsPilot/

├── app.py                    # Main application

├── requirements.txt          # Production dependencies

├── requirements-dev.txt      # Development dependencies

├── .env.example              # Environment variables template

│

├── modules/

│   ├── init.py           # Package initializer

│   ├── system_prompt.py      # AI personality + rules

│   ├── sheets_connector.py   # Google Sheets connection

│   ├── ai_engine.py          # RAG + AI responses

│   ├── event_logger.py       # Event logging system

│   └── pattern_analyzer.py   # Pattern detection

│

├── data/

│   └── sample_data.csv       # Sample data reference

│

├── docs/

│   └── architecture.png      # System diagram

│

└── tests/

└── test_basic.py         # Basic tests

---

## 📊 Data Sources (Google Sheets)

| Sheet | Tracks |
|---|---|
| Material_Ledger | Steel rod batches, quantities, locations |
| Production_Jobs | Active jobs, stages, assignments |
| Machines | Status, runtime, idle time, operators |
| Vendors | Deliveries, reliability scores |
| Quality_Log | Defects, actions, decisions |
| Event_Log | All events for pattern analysis |

---

## ⚙️ How to Run Locally

### Prerequisites
- Python 3.12+
- Google Cloud account
- Ollama installed (for local AI)

### Setup

**1. Clone the repo**
```bash
git clone https://github.com/RKM7-art/OpsPilot.git
cd OpsPilot
```

**2. Create virtual environment**
```bash
python -m venv venv --copies
source venv/Scripts/activate  # Windows
source venv/bin/activate       # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements-dev.txt
```

**4. Set up Google Sheets API**
- Create Google Cloud Project
- Enable Sheets + Drive APIs
- Create Service Account
- Download credentials.json
- Place in project root

**5. Set up environment variables**
```bash
cp .env.example .env
# Add your API keys to .env
```

**6. Run the app**
```bash
streamlit run app.py
```

---

## 🌐 Live Demo

[Link to deployed app — coming soon]

---

## 📹 Demo Video

[Link to demo video — coming soon]

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
- ✅ Conversational AI assistant
- ✅ Live Google Sheets integration
- ✅ Cross-sheet reasoning
- ✅ Pattern detection
- ✅ Two-way data updates

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

**Rudra** — FlowZint AI Hackathon 2026

*"I built OpsPilot because I lived the problem. 
Every morning at Sudarshan Gears was chaos — 
machines idle, vendors late, defects repeating. 
OpsPilot is what we needed but didn't have."*

---

## 📄 License

MIT License — see LICENSE file for details.