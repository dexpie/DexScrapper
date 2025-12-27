from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import uuid
import logging
from src.scraper import StaticScraper
from src.dynamic_scraper import DynamicScraper
from src.db_manager import DBManager

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DexAPI")

app = FastAPI(title="DexScrapper API", version="1.0.0")

# In-memory job store
jobs = {}

class ScrapeRequest(BaseModel):
    url: str
    mode: str = "static"  # static or dynamic
    depth: int = 1
    concurrency: int = 3
    download_media: bool = False
    url_filter: Optional[str] = None
    ai_prompt: Optional[str] = None  # Future AI integration

class JobStatus(BaseModel):
    id: str
    status: str
    processed: int
    results_count: int
    message: Optional[str] = None

async def process_scrape_job(job_id: str, request: ScrapeRequest):
    jobs[job_id]['status'] = 'running'
    try:
        results = []
        if request.mode.lower() == "static":
            scraper = StaticScraper(
                request.url, 
                max_depth=request.depth, 
                concurrency=request.concurrency,
                download_media=request.download_media,
                url_filter=request.url_filter
            )
            results = await scraper.run()
        else:
            scraper = DynamicScraper(
                request.url, 
                max_depth=request.depth, 
                concurrency=request.concurrency,
                headless=True,
                download_media=request.download_media,
                url_filter=request.url_filter
            )
            results = await scraper.run()
        
        # Save to DB
        db = DBManager("sqlite:///scraped_data.db")
        for item in results:
            db.save_result(
                url=item['url'],
                title=item['title'],
                content_snippet=item.get('content_snippet')
            )
            
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['results'] = results
        jobs[job_id]['results_count'] = len(results)
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['message'] = str(e)

@app.post("/scrape", response_model=dict)
async def submit_scrape_job(request: ScrapeRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "id": job_id,
        "status": "pending",
        "processed": 0,
        "results_count": 0,
        "results": [],
        "request": request.dict()
    }
    
    background_tasks.add_task(process_scrape_job, job_id, request)
    return {"job_id": job_id, "message": "Job submitted successfully"}

@app.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = jobs[job_id]
    return JobStatus(
        id=job['id'],
        status=job['status'],
        processed=job.get('processed', 0),
        results_count=job.get('results_count', 0),
        message=job.get('message')
    )

@app.get("/results/{job_id}")
async def get_job_results(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if jobs[job_id]['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Job not completed yet")
        
    return jobs[job_id]['results']

# --- GEN-API ENDPOINT ---
@app.get("/data")
def get_scraped_data(
    limit: int = 100, 
    offset: int = 0, 
    search: Optional[str] = None
):
    """
    Gen-API: Serve scraped data dynamically.
    """
    try:
        conn = DBManager("sqlite:///scraped_data.db").engine.connect()
        query = "SELECT * FROM scraped_results"
        params = {}
        
        if search:
            query += " WHERE title LIKE :search OR content_snippet LIKE :search"
            params['search'] = f"%{search}%"
            
        query += " LIMIT :limit OFFSET :offset"
        params['limit'] = limit
        params['offset'] = offset
        
        from sqlalchemy import text
        result = conn.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
        conn.close()
        
        return {
            "count": len(data),
            "limit": limit,
            "offset": offset,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
