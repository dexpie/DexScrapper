import sys
import asyncio

# Windows asyncio fix for Playwright/Subprocesses
# MUST BE FIRST
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import pandas as pd
import os
import queue
import logging
from src.scraper import StaticScraper
from src.dynamic_scraper import DynamicScraper
from src.db_manager import DBManager
from src.utils import save_to_csv, save_to_excel, save_to_json, ensure_dir
from src.log_utils import QueueHandler

# Setup Page
st.set_page_config(page_title="DexScrapper Ultimate V2", page_icon="🕷️", layout="wide")

# Setup Logging
if 'log_queue' not in st.session_state:
    st.session_state['log_queue'] = queue.Queue()
    
    # Configure root logger to send to queue
    q_handler = QueueHandler(st.session_state['log_queue'])
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    q_handler.setFormatter(formatter)
    
    # Add handler to scrapers loggers
    logging.getLogger().addHandler(q_handler)
    logging.getLogger().setLevel(logging.INFO)

st.title("🕷️ DexScrapper Ultimate V2")
st.markdown("### 🚀 High-Performance Visual Web Scraper")

# Sidebar - Configuration
st.sidebar.header("🔧 Configuration")

# Input Method (Single vs Batch)
input_method = st.sidebar.radio("Input Method", ["Single URL", "Batch File (.txt)"])
urls_to_scrape = []

if input_method == "Single URL":
    url_input = st.sidebar.text_input("Target URL", "https://example.com")
    if url_input:
        urls_to_scrape.append(url_input)
else:
    uploaded_file = st.sidebar.file_uploader("Upload URL List (.txt)", type=['txt'])
    if uploaded_file:
        stringio = uploaded_file.getvalue().decode("utf-8")
        urls = [line.strip() for line in stringio.splitlines() if line.strip() and line.strip().startswith('http')]
        st.sidebar.success(f"Loaded {len(urls)} URLs")
        urls_to_scrape = urls

mode = st.sidebar.radio("Scraping Mode", ["Static (Fast)", "Dynamic (JS Support)"])

# Advanced Options
st.sidebar.subheader("⚙️ Advanced Settings")
depth = st.sidebar.slider("Crawl Depth", 1, 5, 2)
concurrency = st.sidebar.slider("Concurrency (Tabs)", 1, 10, 3, help="Higher = Faster but heavier")

enable_proxy = st.sidebar.checkbox("Enable Proxy")
proxy_url = ""
if enable_proxy:
    proxy_url = st.sidebar.text_input("Proxy URL", "http://user:pass@host:port")

# V3 Features: Media & Filter
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Smart Features")
download_media = st.sidebar.checkbox("📸 Download Media (Images/PDF)", help="Save images and PDFs to output/media")
url_filter = st.sidebar.text_input("🔍 URL Key Filter", help="Only scrape URLs containing this keyword")

# Visual Mode (Dynamic Only)
visual_mode = False
if "Dynamic" in mode:
    visual_mode = st.sidebar.checkbox("📺 Show Browser (Visual Mode)", value=False, help="Watch the scraper in action!")

# Action
if st.sidebar.button("🚀 Start Scraping"):
    if not urls_to_scrape:
        st.error("Please provide a URL or upload a file.")
        st.stop()

    # Clear logs
    while not st.session_state['log_queue'].empty():
        st.session_state['log_queue'].get()

    status_area = st.empty()
    log_area = st.expander("📜 Live Logs", expanded=True)
    log_container = log_area.empty()
    logs = []
    
    all_results = []
    
    # Progress Bar for Batch
    progress_bar = st.progress(0)
    
    with st.spinner(f"Scraping {len(urls_to_scrape)} URLs using {mode}..."):
        try:
            for i, target_url in enumerate(urls_to_scrape):
                status_area.info(f"Processing ({i+1}/{len(urls_to_scrape)}): {target_url}")
                
                # Run Scraper
                current_results = []
                if "Static" in mode:
                    scraper = StaticScraper(target_url, max_depth=depth, concurrency=concurrency, 
                                            proxy=proxy_url if enable_proxy else None,
                                            download_media=download_media,
                                            url_filter=url_filter)
                    current_results = asyncio.run(scraper.run())
                else:
                    # Dynamic
                    scraper = DynamicScraper(target_url, max_depth=depth, concurrency=concurrency, 
                                           headless=not visual_mode, 
                                           proxy=proxy_url if enable_proxy else None,
                                           download_media=download_media,
                                           url_filter=url_filter)
                    current_results = asyncio.run(scraper.run())
                
                if current_results:
                    all_results.extend(current_results)
                
                progress_bar.progress((i + 1) / len(urls_to_scrape))
            
            if all_results:
                status_area.success(f"✅ Batch Complete! Scraped {len(all_results)} total pages.")
                
                # Save to DB
                db_path = "sqlite:///scraped_data.db"
                db = DBManager(db_path)
                for item in all_results:
                    db.save_result(
                        url=item['url'],
                        title=item['title'],
                        content_snippet=item.get('content_snippet')
                    )
                
                st.session_state['results'] = all_results
            else:
                status_area.error("❌ No data found or scraping failed.")
        
        except Exception as e:
            status_area.error(f"An error occurred: {e}")

    # Show collected logs
    while not st.session_state['log_queue'].empty():
        record = st.session_state['log_queue'].get()
        logs.append(record.message if hasattr(record, 'message') else str(record))
    
    if logs:
        log_container.code("\n".join(logs), language='log')

# Display Results
if 'results' in st.session_state and st.session_state['results']:
    data = st.session_state['results']
    df = pd.DataFrame(data)
    
    # Clean up for display
    # Check if links exists to avoid key error if empty result structure
    if 'links' in df.columns:
        display_df = df.copy()
        display_df['links_count'] = display_df['links'].apply(lambda x: len(x) if isinstance(x, list) else 0)
        display_df = display_df.drop(columns=['links'])
    else:
        display_df = df

    st.subheader("📊 Scraped Data")
    st.dataframe(display_df, use_container_width=True)

    # Export Section
    st.subheader("💾 Export Data")
    col1, col2, col3 = st.columns(3)
    
    ensure_dir('output')
    
    # Generate files for download
    csv_file = 'output/dashboard_export.csv'
    save_to_csv(data, csv_file)
    with open(csv_file, 'rb') as f:
        col1.download_button("Download CSV", f, file_name="scraped_data.csv", mime="text/csv")
    
    # Excel requires openpyxl
    xlsx_file = 'output/dashboard_export.xlsx'
    try:
        save_to_excel(data, xlsx_file)
        with open(xlsx_file, 'rb') as f:
            col2.download_button("Download Excel", f, file_name="scraped_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        col2.error("Excel export failed")

    json_file = 'output/dashboard_export.json'
    save_to_json(data, json_file)
    with open(json_file, 'rb') as f:
        col3.download_button("Download JSON", f, file_name="scraped_data.json", mime="application/json")

# Database Viewer
st.markdown("---")
st.subheader("🗄️ Database Viewer (History)")
if st.checkbox("Show Database History"):
    try:
        db_path = "sqlite:///scraped_data.db"
        conn = DBManager(db_path).engine.connect()
        history_df = pd.read_sql("SELECT * FROM scraped_data ORDER BY created_at DESC LIMIT 50", conn)
        st.dataframe(history_df)
        conn.close()
    except Exception as e:
        st.warning("No database found or empty.")
