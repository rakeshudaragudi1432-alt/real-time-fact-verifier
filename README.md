# Real-Time AI Fact Verification System

A production-ready web application that verifies natural-language factual statements against live external data sources and authoritative online APIs across **Weather**, **Sports**, **Movies**, and **Science** domains in real time.

---

## 📌 Project Overview
Unlike static text classifiers or offline models, this system performs **live evidence-based verification**. It accepts arbitrary natural-language claims from users, extracts intent and key entities using a domain claim analyzer, queries relevant external REST APIs, and compares the claimed facts against retrieved live data.

---

## ✨ Key Features
- 🧠 **Intelligent Domain Detection**: Automatically classifies inputs into Weather, Sports, Movies, Science, or Unknown.
- 📡 **Live Real-World API Integration**: Integrates directly with Open-Meteo, TheSportsDB, OMDb / IMDb, Wikimedia REST API, NASA Open Science API, and PubChem NIH API.
- 📊 **3-State Verification Classification**:
  - `VERIFIED ✅`: Live evidence directly supports the claim.
  - `NOT VERIFIED ❌` (or `FALSE`): Live evidence refutes or contradicts the claim.
  - `UNCERTAIN ⚠️`: Available evidence is insufficient or ambiguous.
- 🛡️ **Zero Fake Data Policy**: Never invents or hardcodes data. Returns `UNCERTAIN` when external APIs are unavailable.
- 🔒 **Security & API Key Protection**: Server-side API key management via `.env`. Zero secrets exposed to frontend templates or client scripts.
- 🚀 **Performance & Resiliency**: Built-in 8-second HTTP request timeouts, in-memory TTL query caching, and SQLite indexing.
- 📜 **Historical Verification Log**: SQLite database layer saving verification history and live aggregate statistics.
- 📱 **Modern Responsive UI**: Clean Inter & Plus Jakarta Sans design supporting desktop and mobile viewports.

---

## 🏛️ System Architecture

```
                    ┌─────────────────────────┐
                    │       USER CLAIM        │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     CLAIM ANALYZER      │
                    │  (Category & NLP Entity)│
                    └────────────┬────────────┘
                                 │
                                 ▼
                     Domain Routing (Single API)
        ┌────────────────┬───────┴────────┬────────────────┐
        │                │                │                │
        ▼                ▼                ▼                ▼
 ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
 │ Weather API │  │ Sports API  │  │ Movies API  │  │ Science API │
 │(Open-Meteo) │  │(TheSportsDB)│  │ (OMDb/IMDb) │  │ (Wikimedia/ │
 └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │ NASA/PubChem│
        │                │                │         └──────┬──────┘
        └────────────────┼────────────────┴────────────────┘
                         │
                         ▼
            ┌─────────────────────────┐
            │   FACT VERIFIER ENGINE  │
            │ (Claim vs Live Evidence)│
            └────────────┬────────────┘
                         │
                         ▼
       RESULT (VERIFIED / NOT VERIFIED / UNCERTAIN)
                         │
                         ▼
             SQLite DB & Responsive Frontend
```

---

## 🛠️ Technology Stack
- **Backend Framework**: Python 3, Flask
- **Environment Management**: `python-dotenv`
- **HTTP Client**: `requests` (with 8s timeout & exception handlers)
- **Database**: SQLite3 (with parameterized queries and performance indexes)
- **Frontend**: HTML5, CSS3 (Modern Flexbox/Grid), JavaScript (ES6)
- **Unit Testing**: Python `unittest` suite

---

## 🔐 Environment Variables & API Setup

Create a `.env` file in the project root directory:

```env
# Server Configuration
PORT=5000
SECRET_KEY=production_secret_key_change_me_12345

# Optional API Keys (Free public fallbacks are active by default)
WEATHER_API_KEY=
SPORTS_API_KEY=
MOVIE_API_KEY=
NASA_API_KEY=
```

> [!NOTE]
> All domain services include automatic free public API fallbacks (e.g. Open-Meteo for Weather, Wikimedia & PubChem for Science, public OMDb mirrors for Movies).

---

## 📦 Installation & Local Setup

### 1. Clone & Navigate to Repository
```bash
cd real_time_fact_verifier
```

### 2. Set Up Python Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the Application
```bash
python app.py
```
Open your browser at `http://127.0.0.1:5000`.

---

## 🧪 Testing Suite

### Run Automated Unit Tests
```bash
python -m unittest discover -s tests
```

### Verification Scenarios Tested
- **Weather Claims**: Temperature accuracy (e.g., Vijayawada 28°C), weather condition matching, missing location handling.
- **Sports Claims**: Match winner validation, loss assertions ("lost their last game"), box score comparisons, unknown team handling.
- **Movie Claims**: Release year verification (Interstellar 2014 vs 2018), director validation, cast extractions.
- **Science Claims**: Satellite relations, planetary positions, physical constants (water freezing point), fake science assertions.
- **Input Edge Cases**: Empty string, random text ("xyz abc 123"), long text truncation, network timeout simulation.

---

## 🔍 How Verification Works

1. **Claim Submission**: The user submits a natural-language claim via the web UI or JSON API (`POST /api/verify`).
2. **Domain Classification**: `ClaimAnalyzer` inspects keywords and phrase patterns to determine if the claim belongs to `weather`, `sports`, `movies`, `science`, or `unknown`.
3. **Targeted Retrieval**: The system invokes only the required domain service, fetching fresh evidence from external REST endpoints.
4. **Evidence Comparison**: `FactVerifier` compares the user's assertion against retrieved structured fields.
5. **Result Generation**:
   - `VERIFIED ✅`: Retrieved evidence supports the claim within expected thresholds.
   - `NOT VERIFIED ❌`: Retrieved evidence explicitly refutes the claim.
   - `UNCERTAIN ⚠️`: Information is missing, ambiguous, or the domain could not be confidently identified.

---

## ⚠️ Limitations & Security Safeguards
- **Live Data Dependency**: Fact verification depends on external REST API uptime. If an API times out or is unreachable, the system returns `UNCERTAIN ⚠️` rather than inventing data.
- **API Key Confidentiality**: All API keys remain server-side. No credentials or internal tracebacks are exposed in frontend templates or log files.
- **Database Safety**: SQLite database queries use prepared parameterized statements to prevent SQL injection.

---

## 📜 License
Academic & Research Project for Fact Verification.
