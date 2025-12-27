from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
import uuid
import time

app = FastAPI(title="DexScrapper Hive Mind (Queen Bee)")

# In-memory storage (For V16 MVP)
drones = {}  # {drone_id: last_seen}
task_queue = [] # List of {"id": str, "url": "...", "config": {}}
results = [] # List of results

class DroneRegister(BaseModel):
    drone_id: str
    capabilities: List[str]

class TaskResult(BaseModel):
    task_id: str
    drone_id: str
    data: List[Dict]

@app.get("/")
def home():
    return {"status": "Queen Bee Online", "drones_active": len(drones), "queue_size": len(task_queue)}

@app.post("/register")
def register_drone(drone: DroneRegister):
    drones[drone.drone_id] = time.time()
    return {"status": "Registered", "command": "Await Orders"}

@app.get("/get_task")
def get_task(drone_id: str):
    # Update heartbeat
    drones[drone_id] = time.time()
    
    if task_queue:
        task = task_queue.pop(0)
        return {"task": task}
    return {"task": None}

@app.post("/submit_result")
def submit_result(result: TaskResult):
    results.append(result.dict())
    return {"status": "Accepted", "credits": 1}

# Management Endpoints (For Dashboard)
@app.post("/add_task")
def add_task(url: str, mode: str = "Static"):
    task_id = str(uuid.uuid4())
    task_queue.append({
        "id": task_id, 
        "url": url, 
        "mode": mode,
        "created_at": time.time()
    })
    return {"task_id": task_id, "queue_pos": len(task_queue)}

@app.get("/stats")
def get_stats():
    # Clean dead drones (> 60s silence)
    now = time.time()
    active_drones = {k: v for k, v in drones.items() if now - v < 60}
    return {
        "active_drones": len(active_drones),
        "queued_tasks": len(task_queue),
        "results_collected": len(results),
        "drones": list(active_drones.keys())
    }

if __name__ == "__main__":
    # Run on 0.0.0.0 to be accessible by other machines
    uvicorn.run(app, host="0.0.0.0", port=8000)
