# ⚡ DexScrapper God Mode - "Cerebro Edition"

The Ultimate Autonomous Research & Scraper Agent. It thinks, searches, and scrapes behind login walls.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)

## 🤯 God Mode Features

- **🧠 Cerebro Agent**: 
  - An Autonomous Researcher. Ask a question -> It searches the web -> Scrapes top results -> Synthesizes a Report.
- **🔐 Session Manager**: 
  - Login to any site (Facebook, LinkedIn, etc.) once, save the session, and the bot will use it forever.
- **👁️ The Watcher (Scheduler)**: Automate scraping jobs 24/7.
- **🧠 AI Extraction**: Turn unstructured HTML into JSON data using OpenAI.
- **🔌 REST API Server**: Control the bot programmatically.
- **📊 Data Explorer**: Full database management UI.

## 🛠️ Installation

### Quick Start (Windows)
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    playwright install
    ```
2.  **Run Dashboard**:
    Double-click **`run.bat`** or:
    ```powershell
    .\run.bat
    ```

### Docker Setup
```bash
docker-compose up --build
```
Access the dashboard at `http://localhost:8501`.

## 📖 Usage Guide

### 1. Cerebro Agent (Tab 5)
- Enter your **OpenAI API Key**.
- Ask a question: *"What is the latest news on SpaceX Starship?"*
- Watch the magic happen.

### 2. Session Manager (Tab 4)
- Create a session (e.g., `mytwitter`).
- Click "Launch Browser" -> Log in manually -> Close browser.
- Go to **Scraper Engine (Tab 1)** -> Select `mytwitter` in "Auth Session".

### 3. REST API
Start the backend:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

## 📂 Project Structure

- `src/cerebro.py`: AI Research Agent logic.
- `src/session_manager.py`: Playwright Auth logic.
- `src/scraper.py` & `dynamic_scraper.py`: Core engines.
- `dashboard.py`: Streamlit God Mode UI.
- `api.py`: FastAPI Server.

## 🤝 Contributing
Pull requests are welcome!
