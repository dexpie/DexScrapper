# 🕷️ DexScrapper Enterprise - "The Intelligent One"

A professional-grade, high-performance web scraping suite with **AI Capabilities** and **API Access**.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)

## 🌟 Key Features

- **🚀 Dual Mode Engine**: Static (speed) & Dynamic (JS support).
- **🧠 AI Extraction**: 
  - Turn messy HTML into clean JSON using **OpenAI (GPT-4o)** for structured data.
- **🔌 REST API Server**: 
  - Control the scraper programmatically via HTTP endpoints (`/scrape`).
- **📊 Data Explorer**: 
  - View, Filter, Delete, and Export (`CSV/Excel/JSON`) data directly in the Dashboard.
- **👁️ The Watcher (Scheduler)**: Automate scraping jobs.
- **🔔 Notifications**: Discord/Telegram alerts.
- **🥷 OP Stealth Mode**: Anti-detect capabilities.
- **📸 Media Hunter**: Auto-download Images & PDFs.
- ** Batch Processing**: Process lists of URLs.

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

### 1. Web Dashboard (Enterprise UI)
- **Scraper Engine**: Configure and run jobs. Enable **"AI Parsing"** in sidebar to extract structured data.
- **Data Explorer**: View SQLite database, delete rows, or export data.
- **The Watcher**: Schedule background jobs.

### 2. REST API Server
Start the backend for integration:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```
- **Swagger Docs**: Visit `http://localhost:8000/docs`.
- **Start Job**: `POST /scrape`
- **Check Status**: `GET /status/{job_id}`

### 3. Command Line Interface (CLI)
```bash
# Basic Recursive Crawl
python main.py --url "https://example.com" --depth 2
```

## 📂 Project Structure

- `src/`: Core logic (scraper, ai_utils, notifications).
- `dashboard.py`: Streamlit Enterprise UI.
- `api.py`: FastAPI Server.
- `scheduler.py`: Background job runner.
- `output/`: Results (media, markdown).

## 🤝 Contributing
Pull requests are welcome!
