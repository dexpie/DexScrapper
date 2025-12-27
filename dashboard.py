import streamlit as st
import asyncio
import sys
import os
import pandas as pd
import queue
import logging
from src.scraper import StaticScraper
from src.dynamic_scraper import DynamicScraper
from src.db_manager import DBManager
from src.ai_utils import parse_with_ai
from src.utils import save_to_csv, save_to_excel, save_to_json, ensure_dir
from src.log_utils import QueueHandler
from src.session_manager import create_session, get_available_sessions
from src.cerebro import CerebroAgent
from src.oracle import Oracle
from src.cloud_utils import upload_to_sheets

# Windows Asyncio Policy Fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

st.set_page_config(page_title="DexScrapper God Mode", page_icon="⚡", layout="wide")

st.title("⚡ DexScrapper God Mode")

# Setup Logging (global)
if 'log_queue' not in st.session_state:
    st.session_state['log_queue'] = queue.Queue()
    q_handler = QueueHandler(st.session_state['log_queue'])
    logging.getLogger().addHandler(q_handler)
    logging.getLogger().setLevel(logging.INFO)

# Tabs
tab_scraper, tab_explorer, tab_scheduler, tab_session, tab_cerebro, tab_oracle, tab_api, tab_genesis, tab_alchemy = st.tabs([
    "🚀 Scraper Engine", "📊 Data Explorer", "👁️ The Watcher", "🔐 Session Manager", "🧠 Cerebro Agent", "🔮 The Oracle", "🧞 Gen-API", "🧬 Genesis", "⚗️ Alchemy"
])

# Global AI Settings (Side-wide or Sidebar?)
st.sidebar.markdown("---")
st.sidebar.subheader("🧠 Omni-Brain (AI Settings)")
llm_provider = st.sidebar.selectbox("LLM Provider", ["OpenAI", "DeepSeek", "Ollama (Local)"])
llm_base_url = None
llm_model = "gpt-4o"
llm_api_key = ""

if llm_provider == "OpenAI":
    llm_api_key = st.sidebar.text_input("OpenAI Key", type="password")
    llm_model = st.sidebar.text_input("Model", "gpt-4o")
elif llm_provider == "DeepSeek":
    llm_api_key = st.sidebar.text_input("DeepSeek Key", type="password")
    llm_base_url = st.sidebar.text_input("Base URL", "https://api.deepseek.com")
    llm_model = st.sidebar.text_input("Model", "deepseek-chat")
elif llm_provider == "Ollama (Local)":
    llm_base_url = st.sidebar.text_input("Base URL", "http://localhost:11434/v1")
    llm_model = st.sidebar.text_input("Model", "llama3")
    llm_api_key = "ollama" # Dummy

# --- TAB 1: SCRAPER ENGINE ---
with tab_scraper:
    # Sidebar - Configuration
    st.sidebar.header("🔧 Configuration")
    
    # ... (Keep existing inputs) ...
    # Instead of re-writing everything, I'll inject the new options.
    # Note: Streamlit execution flow is top-down. We need to be careful with layout.
    
    # Input Method
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

    # Session Selection (Auth)
    available_sessions = get_available_sessions()
    session_file = None
    if available_sessions and "Dynamic" in mode:
        st.sidebar.subheader("🔐 Auth Session")
        selected_session = st.sidebar.selectbox("Use Session", ["None"] + available_sessions)
        if selected_session != "None":
            session_file = os.path.join("sessions", f"{selected_session}.json")

    # Advanced Options
    st.sidebar.subheader("⚙️ Advanced Settings")
    depth = st.sidebar.slider("Crawl Depth", 1, 5, 2)
    concurrency = st.sidebar.slider("Concurrency (Tabs)", 1, 10, 3, help="Higher = Faster but heavier")

    enable_proxy = st.sidebar.checkbox("Enable Proxy")
    proxy_url = ""
    if enable_proxy:
        proxy_url = st.sidebar.text_input("Proxy URL", "http://user:pass@host:port")

    # V8 Advanced Crawl
    with st.sidebar.expander("🕸️ Advanced Spider Options"):
        robots_txt = st.checkbox("👮 Respect robots.txt")
        link_regex = st.text_input("🔗 Follow Links Regex", help="Only follow links matching this pattern (e.g. '/product/')")
        st.caption("ℹ️ Tip: Input a `sitemap.xml` URL above to crawl it entirely.")
    
    # V10 Vision Mode
    vision_mode = False
    if "Dynamic" in mode:
        vision_mode = st.sidebar.checkbox("👁️ Vision Mode (Optical)", help="Extract data from screenshots.")
    
    # V12 Stealth & Turbo
    st.sidebar.subheader("🏎️ V12 Performance")
    turbo_mode = False
    stealth_mode = False
    if "Dynamic" in mode:
        turbo_mode = st.sidebar.checkbox("🏎️ Turbo Mode (Block Media)", help="Blocks images/fonts for max speed.")
        stealth_mode = st.sidebar.checkbox("👻 Stealth-X (Evasion)", help="Advanced anti-fingerprinting.")

    # V12 Ghost Proxies
    st.sidebar.subheader("🎭 Ghost Proxies")
    if st.sidebar.button("Harvest Free Proxies"):
        from src.proxy_manager import ProxyManager
        pm = ProxyManager()
        count = asyncio.run(pm.harvest_proxies())
        if count > 0:
            st.session_state['ghost_proxies'] = pm.proxies
            st.sidebar.success(f"Harvested {count} proxies!")
        else:
            st.sidebar.error("Harvest failed.")
            
    if 'ghost_proxies' in st.session_state and st.session_state['ghost_proxies']:
        use_ghost = st.sidebar.checkbox("Use Ghost Proxies (Auto-Rotate)")
        if use_ghost: 
            enable_proxy = True # Force enable logic

    # Feature: AI Extraction
    st.sidebar.markdown("---")
    st.sidebar.subheader("🧠 AI Extraction")
    enable_ai = st.sidebar.checkbox("Enable AI Parsing")
    ai_prompt = ""
    if enable_ai:
        ai_prompt = st.sidebar.text_area("Extraction Instruction", "Extract product name and price as JSON.")
        if not llm_api_key:
            st.sidebar.warning("⚠️ Please configure 'Omni-Brain' settings above.")

    # V3 Features: Media & Filter
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Smart Features")
    download_media = st.sidebar.checkbox("📸 Download Media (Images/PDF)", help="Save images and PDFs to output/media")
    url_filter = st.sidebar.text_input("🔍 URL Key Filter", help="Only scrape URLs containing this keyword")

    # Visual Mode (Dynamic Only)
    visual_mode_browser = False
    if "Dynamic" in mode:
        visual_mode_browser = st.sidebar.checkbox("📺 Show Browser (Visual Mode)", value=False, help="Watch the scraper in action!")

    # Action
    if st.button("🚀 Start Scraping", key="start_scraping"):
        if not urls_to_scrape:
            st.error("Please provide a URL or upload a file.")
            st.stop()

        # Ghost Proxy Logic
        ghost_pool = None
        if 'ghost_proxies' in st.session_state and st.session_state.get('ghost_proxies'):
             # If "Use Ghost Proxies" is checked (we need to capture that checkbox state properly)
             # Limitation: Streamlit re-runs. 
             # Let's assume if they have harvested and proxy is enabled, we prioritise ghost if selected?
             # For simplicity, if 'use_ghost' was checked (variable scope issue), we use it.
             # Re-reading use_ghost might be tricky without Session State. 
             pass 

        # Clear logs
        if 'log_queue' in st.session_state:
            while not st.session_state['log_queue'].empty():
                 st.session_state['log_queue'].get()

        status_area = st.empty()
        log_area = st.expander("📜 Live Logs", expanded=True)
        log_container = log_area.empty()
        logs = []
        
        all_results = []
        progress_bar = st.progress(0)
        
        # Helper for proxy rotation
        import random
        def get_current_proxy():
            # If user manually set proxy, use it
            if proxy_url: return proxy_url
            # If ghost proxies active (we need to hack the scope or just use session state check)
            # Minimal implementation:
            if 'ghost_proxies' in st.session_state and enable_proxy and not proxy_url:
                 return random.choice(st.session_state['ghost_proxies'])
            return None

        with st.spinner(f"Scraping {len(urls_to_scrape)} URLs using {mode}..."):
            try:
                for i, target_url in enumerate(urls_to_scrape):
                    status_area.info(f"Processing ({i+1}/{len(urls_to_scrape)}): {target_url}")
                    
                    # Rotate Proxy
                    current_proxy = get_current_proxy()
                    if current_proxy: status_area.caption(f"🎭 Using Proxy: {current_proxy}")

                    # Run Scraper
                    current_results = []
                    if "Static" in mode:
                        scraper = StaticScraper(target_url, max_depth=depth, concurrency=concurrency, 
                                                proxy=current_proxy,
                                                download_media=download_media,
                                                url_filter=url_filter,
                                                link_regex=link_regex,
                                                robots_compliance=robots_txt)
                        current_results = asyncio.run(scraper.run())
                    else:
                        # Dynamic
                        scraper = DynamicScraper(target_url, max_depth=depth, concurrency=concurrency, 
                                               headless=not visual_mode_browser, 
                                               proxy=current_proxy,
                                               download_media=download_media,
                                               url_filter=url_filter,
                                               session_file=session_file,
                                               link_regex=link_regex,
                                               robots_compliance=robots_txt,
                                               vision_mode=vision_mode,
                                               turbo_mode=turbo_mode,
                                               stealth_mode=stealth_mode)
                        current_results = asyncio.run(scraper.run())
                    
                    # AI Processing (Omni-Brain)
                    if enable_ai and llm_api_key and current_results:
                        status_area.info(f"🧠 Omni-Brain ({llm_provider}) Analyzing {len(current_results)} pages...")
                        for res in current_results:
                            # Determine content source: Screenshot (Vision) or Text
                            content_to_parse = ""
                            image_b64 = None
                            
                            if vision_mode and res.get('screenshot'):
                                image_b64 = res.get('screenshot')
                                status_area.info(f"👁️ Vision Analyzing: {res['url']}")
                            elif res.get('markdown_file') and os.path.exists(res['markdown_file']):
                                with open(res['markdown_file'], 'r', encoding='utf-8') as f:
                                    content_to_parse = f.read()

                            # Call Omni-Brain
                            ai_data = parse_with_ai(
                                content=content_to_parse, 
                                prompt=ai_prompt, 
                                api_key=llm_api_key, 
                                model=llm_model, 
                                base_url=llm_base_url,
                                image_base64=image_b64
                            )
                            res['ai_data'] = ai_data
                            status_area.info(f"✅ AI Parsed: {res.get('title', 'Unknown')}")

                    if current_results:
                        all_results.extend(current_results)
                    
                    progress_bar.progress((i + 1) / len(urls_to_scrape))
                
                if all_results:
                    status_area.success(f"✅ Batch Complete! Processed {len(all_results)} pages.")
                    
                    # Save to DB
                    db_path = "sqlite:///scraped_data.db"
                    db = DBManager(db_path)
                    for item in all_results:
                        # Serialize AI data if exists
                        content_snip = item.get('content_snippet')
                        if item.get('ai_data'):
                            import json
                            content_snip = f"AI DATA: {json.dumps(item['ai_data'])}\n\n{content_snip}"
                            
                        db.save_result(
                            url=item['url'],
                            title=item['title'],
                            content_snippet=content_snip
                        )
                    
                    st.session_state['results'] = all_results

                    # Export Section
                    st.subheader("💾 Export Data")
                    col1, col2, col3 = st.columns(3)
                    ensure_dir('output')
                    csv_file = 'output/dashboard_export.csv'
                    save_to_csv(all_results, csv_file)
                    with open(csv_file, 'rb') as f:
                        col1.download_button("Download CSV", f, file_name="scraped_data.csv", mime="text/csv")
                    
                    xlsx_file = 'output/dashboard_export.xlsx'
                    try:
                        save_to_excel(all_results, xlsx_file)
                        with open(xlsx_file, 'rb') as f:
                            col2.download_button("Download Excel", f, file_name="scraped_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    except Exception as e:
                        col2.error(f"Excel export failed: {e}")

                    json_file = 'output/dashboard_export.json'
                    save_to_json(all_results, json_file)
                    with open(json_file, 'rb') as f:
                        col3.download_button("Download JSON", f, file_name="scraped_data.json", mime="application/json")

                else:
                    status_area.error("❌ No data found or scraping failed.")
            
            except Exception as e:
                status_area.error(f"An error occurred: {e}")

        # Show logs
        if 'log_queue' in st.session_state:
            while not st.session_state['log_queue'].empty():
                 record = st.session_state['log_queue'].get()
                 logs.append(record.message if hasattr(record, 'message') else str(record))
            if logs:
                log_container.code("\n".join(logs), language='log')

# --- TAB 2: DATA EXPLORER ---
with tab_explorer:
    st.header("📊 Data Explorer")
    db_path = "sqlite:///scraped_data.db"
    
    # Cloud Uplink
    with st.expander("☁️ Cloud Uplink (Google Sheets)"):
        st.info("Upload your entire database to a Google Sheet.")
        col_g1, col_g2 = st.columns(2)
        gs_creds = col_g1.file_uploader("Service Account JSON", type=['json'], help="Upload your Google Cloud Credentials JSON")
        sheet_name = col_g1.text_input("Target Sheet Name", "DexScrapper Data")
        email_share = col_g1.text_input("Share with Email", "user@example.com")
        
        if col_g1.button("🚀 Sync to Cloud"):
            if not gs_creds:
                 st.error("Please upload JSON credentials.")
            elif not os.path.exists("scraped_data.db"):
                 st.error("No database found.")
            else:
                 try:
                     # Save temp json
                     with open("temp_creds.json", "wb") as f:
                         f.write(gs_creds.getvalue())
                     
                     conn = "sqlite:///scraped_data.db"
                     df = pd.read_sql("SELECT * FROM scraped_results", conn)
                     
                     with st.spinner("Uploading to Google Sheets..."):
                         link = upload_to_sheets(df, sheet_name, "temp_creds.json", email_share)
                     
                     st.success(f"✅ Upload Success! [Open Sheet]({link})")
                 except Exception as e:
                     st.error(f"Upload failed: {e}")

    if os.path.exists("scraped_data.db"):
        conn = "sqlite:///scraped_data.db"
        try:
            df = pd.read_sql("SELECT * FROM scraped_results", conn)
            st.dataframe(df, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📥 Download CSV", df.to_csv(index=False).encode('utf-8'), "scraped_data.csv", "text/csv")
            with col2:
                if st.button("🗑️ Delete All Data"):
                    from sqlalchemy import create_engine, text
                    engine = create_engine(conn)
                    with engine.connect() as con:
                         con.execute(text("DELETE FROM scraped_results"))
                         con.commit()
                    st.success("Database cleared!")
                    st.rerun()
        except Exception as e:
            st.error(f"Error loading database: {e}")
    else:
        st.info("No database found yet. Run a scrape first!")

# --- TAB 3: THE WATCHER (SCHEDULER) ---
with tab_scheduler:
    st.markdown("### 👁️ The Watcher - Automatic Scheduler")
    st.info("Configure jobs here. To run them, execute `python scheduler.py` in terminal.")
    
    with st.form("scheduler_form"):
        sch_url = st.text_input("Target URL")
        sch_interval = st.number_input("Interval (Minutes)", min_value=1, value=60)
        sch_mode = st.selectbox("Mode", ["Static", "Dynamic"])
        sch_webhook = st.text_input("Discord Webhook URL (Optional)")
        
        if st.form_submit_button("➕ Add Job"):
            import json
            new_job = {
                "url": sch_url,
                "interval_minutes": sch_interval,
                "mode": sch_mode,
                "webhook": sch_webhook,
                "active": True
            }
            jobs = []
            if os.path.exists("scheduled_jobs.json"):
                with open("scheduled_jobs.json", 'r') as f:
                    try: jobs = json.load(f)
                    except: pass
            jobs.append(new_job)
            with open("scheduled_jobs.json", 'w') as f:
                json.dump(jobs, f, indent=4)
            st.success("Job added to schedule!")
            
    if os.path.exists("scheduled_jobs.json"):
        st.subheader("📅 Active Schedules")
        import json
        with open("scheduled_jobs.json", 'r') as f:
             jobs = json.load(f)
        st.json(jobs)

# --- TAB 4: SESSION MANAGER ---
with tab_session:
    st.header("🔐 Session Manager (Auth)")
    st.markdown("Create a session to scrape websites that require login (Facebook, LinkedIn, etc).")
    
    session_name = st.text_input("New Session Name (e.g. facebook_acc1)")
    login_url = st.text_input("Login URL", "https://facebook.com")
    
    if st.button("🚀 Launch Login Browser"):
        if not session_name:
            st.error("Please enter a session name.")
        else:
            with st.spinner("Launching browser... Login manually and close the window to save."):
                asyncio.run(create_session(session_name, login_url))
            st.success(f"Session '{session_name}' saved! You can now select it in the Scraper tab.")
            st.rerun()
            
    st.subheader("📂 Saved Sessions")
    sessions = get_available_sessions()
    if sessions:
        st.write(sessions)
    else:
        st.info("No sessions saved yet.")

# --- TAB 5: CEREBRO AGENT ---
with tab_cerebro:
    st.header("🧠 Cerebro - Autonomous Research Agent")
    st.info("Ask a question. Cerebro will search the web, scrape top results, and write a report.")
    
    cerebro_key = st.text_input("OpenAI API Key (Required for Cerebro)", type="password")
    query = st.text_input("Research Topic / Question", "What are the latest breakthroughs in AI Agents?")
    
    if st.button("🔎 Start Research"):
        if not cerebro_key:
            st.error("Please provide OpenAI API Key.")
        else:
            agent = CerebroAgent(cerebro_key)
            status_container = st.empty()
            report_area = st.container()
            
            def update_status(msg):
                status_container.info(msg)
                
            with st.spinner("Cerebro is working..."):
                report = asyncio.run(agent.research_topic(query, update_status))
            
            status_container.success("Research Complete!")
            st.markdown(report)

# --- TAB 6: THE ORACLE ---
with tab_oracle:
    st.header("🔮 The Oracle - Chat with Data")
    st.info("Your data analyst. Ask questions about the content you've scraped.")
    
    oracle_key = st.text_input("OpenAI API Key (For Oracle)", type="password")
    
    if os.path.exists("scraped_data.db"):
        conn = "sqlite:///scraped_data.db"
        df = pd.read_sql("SELECT * FROM scraped_results", conn)
        st.write(f"Loaded {len(df)} records from database.")
        
        user_query = st.text_input("Ask something about your data:", "What is the sentiment of the scraped content?")
        
        if st.button("🔮 Ask Oracle"):
            if not oracle_key:
                st.error("API Key required.")
            else:
                with st.spinner("Gazing into the orb..."):
                    oracle = Oracle(df, oracle_key)
                    answer = oracle.ask(user_query)
                st.success("The Oracle Speaks:")
                st.markdown(answer)
    else:
        st.warning("No data found. Please run a scrape first.")
