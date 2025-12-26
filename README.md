# 🕷️ DexScrapper Ultimate - "Gacor" Edition

A professional-grade, high-performance web scraper and crawler built with Python, Playwright, and Streamlit. Now compatible with "Human-like" Stealth browsing!

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)

## 🌟 Key Features

- **🚀 Dual Mode Engine**: 
  - **Static**: Async `aiohttp` for speed.
  - **Dynamic**: `Playwright` for full JavaScript support (SPA).
- **🥷 OP Stealth Mode**: Anti-detect features to bypass WAF/Bot protection.
- **📸 Media Hunter**: Auto-download Images & PDFs.
- **📝 Smart Markdown**: Auto-convert HTML to clean Markdown files.
- **📦 Batch Processing**: Scrape hundreds of URLs from a list.
- **📊 Web Dashboard**: Beautiful UI to control everything visually.
- **💾 Robust Storage**: SQLite + CSV/Excel/JSON Exports.
- ** Docker Ready**: Plug-and-play deployment.

## 🛠️ Installation

### Quick Start (Windows)
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    playwright install
    ```
2.  **Run Dashboard**:
    Double-click **`run.bat`** or types:
    ```powershell
    .\run.bat
    ```

### Docker Setup
```bash
docker-compose up --build
```
Access the dashboard at `http://localhost:8501`.

## 📖 Usage Guide

### Web Dashboard
The dashboard allows you to:
- Switch between Static/Dynamic modes.
- Adjust **Concurrency** (Speed) and **Crawl Depth**.
- Enable **Visual Mode** (See the browser working).
- Upload Batch Files (`.txt`) for mass scraping.
- Filter URLs by keywords.

### Command Line Interface (CLI)
```bash
# Basic Recursive Crawl
python main.py --url "https://example.com" --depth 2

# "OP" Dynamic Mode with Media Download
python main.py --url "https://spa-example.com" --dynamic --download-media

# Batch Scraper from File (using Helper script logic or pure python loop)
# (Currently CLI is single URL, use Dashboard for native Batch UI)
```

## 📂 Project Structure

- `src/scraper.py`: Static async scraper engine.
- `src/dynamic_scraper.py`: Dynamic Playwright scraper engine.
- `src/media_utils.py`: Media download logic.
- `src/log_utils.py`: Log streaming.
- `dashboard.py`: Streamlit UI application.
- `main.py`: CLI entry point.
- `output/`: 
    - `media/`: Downloaded images/PDFs.
    - `markdown/`: Cleaned text content.

## 🤝 Contributing
Pull requests are welcome!
