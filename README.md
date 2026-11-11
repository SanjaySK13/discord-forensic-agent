# Discord Forensic Agent 🕵️‍♂️🔬

> **AI-Powered Stylometric Authorship Attribution, Behavioral Profiling, and Forensic Intelligence System for Discord Servers.**

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Flask](https://img.shields.io/badge/framework-Flask-lightgrey.svg)
![Gemini AI](https://img.shields.io/badge/model-Gemini%20Flash-orange.svg)
![Stylometrics](https://img.shields.io/badge/stylometrics-Burrows'%20Delta%20%7C%20Zipf-green.svg)

---

## 🌟 Overview

The **Discord Forensic Agent** is an end-to-end digital forensic analysis platform built to uncover the anonymous authors of Discord confessions, messages, or leaks. Combining **rigorous mathematical stylometrics** with **deep qualitative LLM psychological profiling (Google Gemini Flash)**, the platform evaluates syntax, lexical choice, punctuation cadence, and contraction habits across tens of thousands of server messages.

---

## 🚀 Key Features

### 1. 5-Layer Mathematical Stylometrics Engine
Analyzes thousands of server messages against an unknown confession across five distinct forensic layers:
* **Burrows' Delta ($Z$-score Proximity):** Calculates standard deviations against the most frequent function words in the corpus to identify subconscious writing habits.
* **Character 3–5 Gram TF-IDF Cosine Similarity:** Measures sub-word morphological patterns, typographical quirks, and casing preferences.
* **Zipfian Surprisal Density:** Evaluates word frequency distribution and information-theoretic lexical entropy to catch atypical vocabulary usage.
* **Semantic Embedding Space:** Measures conceptual and topical alignment in dense vector space.
* **Descriptive Biometrics:** Compares apostrophe drop ratio ($R_{\text{drop}}$), punctuation density, and mean clause length.
* **Bayesian Posterior Probability:** Normalizes composite distance scores through a softmax ensemble layer to assign rigorous percentage confidence values to suspect candidates.

### 2. Qualitative Forensic Intelligence Dossier (Gemini Flash)
Generates an investigative dossier detailing:
* **Motive Analysis & Psychological Profiling:** Unpacks status grievances, social policing, romantic jealousy, or server hierarchy frustrations.
* **Adversarial Frame-Job & Mimicry Risk:** Distinguishes between habitual reflexes (casing, trailing tildes, sentence length) and copy-pasted catchphrases to assess if a suspect is being framed.
* **Social Graph Dynamics:** Identifies server targets, monitoring habits, and cross-channel observation patterns.
* **Actionable Interrogation Traps:** Provides bait questions to ask in server channels or DMs to elicit a conclusive linguistic reaction.

### 3. Interactive Interrogation Room
* A real-time conversational partner powered by Gemini Flash with live indexed access to the entire server message database.
* Grounded in factual message statistics, member message counts, and verified quotes.

### 4. Member Behavioral Profiler & 3-Line Roast
* Analyzes any member's past message history (from 20 to 5,000+ messages).
* Produces personality archetypes, communication vibes, topic fixations, and a customized 3-line roast based on their real messages.

### 5. High-Throughput Discord Scraper
* **Forward Sync:** Fetches all new messages posted since the newest cached message.
* **Targeted Backward Sync:** Paginates backwards into past channel history to hunt older messages for specific authors.
* **Live Progress Tracking:** Real-time animated progress bar showing messages scanned, targets found, rate limits, and pause/cancel controls.
* **Unified Database:** Both attribution and behavioral profiling share a single cached message corpus.

---

## 🛠️ System Architecture

```
discord-forensic-agent/
│
├── server.py                  # Flask web backend and REST API
├── gemini_analyst.py          # Gemini Flash LLM integration & prompt engineering
├── math_stylometrics.py       # 5-layer mathematical stylometrics engine
├── stylometrics.py            # Attribution orchestrator & statistical scoring
├── scrape_discord.py          # Discord REST API pagination & deduplication
│
├── templates/
│   └── index.html             # Discord-themed UI (Tailwind CSS, Lucide icons)
│
├── requirements.txt           # Python dependencies
├── config.example.json        # Template configuration file
├── run_web.bat                # Windows Batch launcher
└── run_web.ps1                # PowerShell launcher
```

---

## 📦 Installation & Quickstart

### Prerequisites
* **Python 3.10+**
* A **Discord Bot Token** with `Read Message History` and `View Channel` permissions.
* A **Google Gemini API Key**.

### 1. Clone Repository
```bash
git clone https://github.com/SanjaySK13/discord-forensic-agent.git
cd discord-forensic-agent
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Credentials
Copy `config.example.json` to `config.json` and add your tokens:
```json
{
  "token": "YOUR_DISCORD_BOT_TOKEN_HERE",
  "gemini_api_key": "YOUR_GEMINI_API_KEY_HERE"
}
```
*(Alternatively, credentials can be entered directly in the web dashboard UI).*

### 5. Launch the Application
```bash
python server.py
```
Open **`http://localhost:5000`** in your browser.

---

## 🔌 API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/predict` | `POST` | Runs the 5-layer mathematical attribution on a confession. |
| `/api/ai_analysis` | `POST` | Generates the Gemini Forensic Dossier & Frame-Job analysis. |
| `/api/chat` | `POST` | Interactive conversational interrogation with database grounding. |
| `/api/members` | `GET` | Returns list of top active members and message counts. |
| `/api/behavioral_analysis`| `POST` | Generates psychological profile and 3-line roast for a member. |
| `/api/start_fetch_user_messages` | `POST` | Starts asynchronous background history scrape for a member. |
| `/api/user_scrape_progress` | `GET` | Polls live progress of the targeted user scraper. |
| `/api/cancel_user_scrape` | `POST` | Cancels an ongoing background scrape and saves progress. |
| `/api/sync_latest` | `POST` | Incremental forward sync of latest Discord messages. |

---

## 🔒 Security & Privacy Notice
* Message databases and API keys are strictly excluded via `.gitignore`.
* Never commit `config.json` or cached JSON archives to public repositories.

---

## 📄 License
MIT License. Created for digital linguistics and forensic NLP research.

