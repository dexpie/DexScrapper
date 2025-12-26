import streamlit as st
import pandas as pd
import asyncio
import os
from src.scraper import StaticScraper
from src.dynamic_scraper import DynamicScraper
from src.db_manager import DBManager
from src.utils import save_to_csv, save_to_excel, save_to_json, ensure_dir

# Setup Page
st.set_page_config(page_title="DexScrapper Ultimate", page_icon="🕷️", layout="wide")

st.title("🕷️ DexScrapper Ultimate - Gacor Edition")
st.markdown("### Professional Web Scraping Dashboard")

# Sidebar - Configuration
st.sidebar.header("Configuration")
url = st.sidebar.text_input("Target URL", "https://example.com")
mode = st.sidebar.radio("Scraping Mode", ["Static (Fast)", "Dynamic (JS Support)"])
depth = st.sidebar.slider("Crawl Depth", 1, 5, 2)
enable_proxy = st.sidebar.checkbox("Enable Proxy")
proxy_url = ""
if enable_proxy:
    proxy_url = st.sidebar.text_input("Proxy URL", "http://user:pass@host:port")

# Action
if st.sidebar.button("🚀 Start Scraping"):
    with st.spinner(f"Scraping {url} in {mode}..."):
        # Run Scraper based on mode
        results = []
        try:
            if "Static" in mode:
                scraper = StaticScraper(url, max_depth=depth, proxy=proxy_url if enable_proxy else None)
                results = asyncio.run(scraper.run())
            else:
                scraper = DynamicScraper(url, max_depth=depth, proxy=proxy_url if enable_proxy else None)
                results = asyncio.run(scraper.run())
            
            if results:
                st.success(f"Successfully scraped {len(results)} pages!")
                
                # Save to DB
                db_path = "sqlite:///scraped_data.db"
                db = DBManager(db_path)
                for item in results:
                    db.save_result(
                        url=item['url'],
                        title=item['title'],
                        content_snippet=item.get('content_snippet')
                    )
                
                # Store in session state for display
                st.session_state['results'] = results
            else:
                st.error("No data found or scraping failed.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

# Display Results
if 'results' in st.session_state and st.session_state['results']:
    data = st.session_state['results']
    df = pd.DataFrame(data)
    
    # Clean up for display
    display_df = df[['title', 'url', 'links']]
    display_df['links_count'] = display_df['links'].apply(len)
    display_df = display_df.drop(columns=['links'])

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
