# 🕷️ DexScrapper Ultimate - "Gacor" Edition

A professional-grade, high-performance web scraper and crawler built with Python, Playwright, and Streamlit.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)

## 🌟 Key Features

- **🚀 Dual Mode**: 
  - **Static**: Extremely fast async scraping using `aiohttp` for standard websites.
  - **Dynamic**: Full JavaScript support using `Playwright` for SPAs (React, Vue, etc.).
- **📊 Web Dashboard**: Beautiful UI built with Streamlit to manage scraping and view data.
- **💾 Robust Storage**: Auto-saves to **SQLite** database and supports **CSV/Excel/JSON** exports.
- **🔄 Stealth System**: Anti-detect mechanics with randomized User-Agents and proxy support.
- **🐳 Docker Ready**: Plug-and-play deployment with Docker Compose.

## 🛠️ Installation

### Local Setup

1.  **Clone & Install Dependencies**:
    ```bash
    git clone https://github.com/dexscrapper/dexscrapper.git
    cd dexscrapper
    pip install -r requirements.txt
    ```

2.  **Install Browsers (for Dynamic Mode)**:
    ```bash
    playwright install
    ```

### Docker Setup

Simply run:
```bash
docker-compose up --build
```
Access the dashboard at `http://localhost:8501`.

## 📖 Usage Guide

### 1. Web Dashboard (Recommended)
The easiest way to use DexScrapper.
```bash
streamlit run dashboard.py
```
Open your browser at the URL provided (usually `http://localhost:8501`).

### 2. Command Line Interface (CLI)

**Basic Static Crawl (Depth 2)**
```bash
python main.py --url "https://example.com" --depth 2 --db results.db
```

**Dynamic Scraping (JS-Heavy Sites)**
```bash
python main.py --url "https://spa-example.com" --dynamic --output results.xlsx
```

**Using Proxy**
```bash
python main.py --url "https://target.com" --proxy "http://user:pass@host:port"
```

### CLI Arguments
| Flag | Description | Default |
|------|-------------|---------|
| `--url` | Target URL (Required) | - |
| `--dynamic` | Enable Playwright for JS sites | False |
| `--depth` | Crawling depth (Static mode only) | 1 |
| `--db` | SQLite database filename | None |
| `--output` | Export filename (.csv, .json, .xlsx) | `output/latest_run.csv` |
| `--proxy` | Proxy URL string | None |

## 📂 Project Structure

- `src/scraper.py`: Static async scraper engine.
- `src/dynamic_scraper.py`: Dynamic Playwright scraper engine.
- `src/db_manager.py`: Database handling (SQLAlchemy).
- `dashboard.py`: Streamlit UI application.
- `main.py`: CLI entry point.
- `output/`: Generated export files.

## 🤝 Contributing
Pull requests are welcome!
