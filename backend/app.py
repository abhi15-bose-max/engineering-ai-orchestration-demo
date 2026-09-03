from __future__ import annotations
import os, uuid, threading, tempfile, json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from .task_registry import resolve
from .core.models import build_model, available_models, ModelError
from .core.storage import JsonStore
from .core.orchestrator import Orchestrator

BASE=Path(__file__).resolve().parent.parent
STORE=JsonStore(BASE/"data"/"trajectories")
app=FastAPI(title="Engineering AI Orchestration & Validation Infrastructure")
runs={}; lock=threading.Lock()

class RunRequest(BaseModel):
    domain:str=Field(pattern="^(rtl|ode|logic)$")
    models:list[str]=Field(min_length=1,max_length=2)
    task:str=Field(min_length=1,max_length=6000)
    max_attempts:int=Field(default=3,ge=1,le=5)

def emit(run_id,e):
    with lock: runs[run_id]["events"].append(e); runs[run_id]["latest"]=e

def worker(run_id,req):
    results={}
    for name in req.models:
        try:
            task_adapter,verifier=resolve(req.domain)
            model=build_model(name,allow_mock=os.getenv("DEMO_MODE","0")=="1")
            if model is None: raise ModelError(f"{name} is unavailable; configure its API key.")
            model_dir=BASE/"data"/"runs"/run_id/name; model_dir.mkdir(parents=True,exist_ok=True)
            emit(run_id,{"type":"model_start","model":name})
            t=Orchestrator(STORE).run(run_id+"_"+name,task_adapter,verifier,model,req.task,req.max_attempts,model_dir,lambda e: emit(run_id,dict(e,model=name)))
            results[name]=t.__dict__
        except Exception as e:
            results[name]={"model":name,"status":"ERROR","error":str(e)}
            emit(run_id,{"type":"model_error","model":name,"message":str(e)})
    with lock:
        runs[run_id].update({"status":"complete","results":results})

@app.get("/",response_class=HTMLResponse)
def index(): return (BASE/"frontend"/"index.html").read_text()

@app.get("/api/health")
def health(): return {"status":"ok","models":{"gpt":bool(os.getenv("OPENAI_API_KEY")),"gemini":bool(os.getenv("GEMINI_API_KEY"))},"demo_mode":os.getenv("DEMO_MODE","0")=="1"}

@app.get("/api/models")
def models(): return {"models":[{"id":"gpt","available":bool(os.getenv("OPENAI_API_KEY")) or os.getenv("DEMO_MODE")=="1"},{"id":"gemini","available":bool(os.getenv("GEMINI_API_KEY")) or os.getenv("DEMO_MODE")=="1"}]}

@app.post("/api/runs")
def create_run(req:RunRequest):
    for m in req.models:
        if m not in {"gpt","gemini"}: raise HTTPException(400,"Unsupported model.")
    rid=uuid.uuid4().hex
    with lock: runs[rid]={"status":"queued","events":[]}
    threading.Thread(target=worker,args=(rid,req),daemon=True).start()
    return {"run_id":rid}

@app.get("/api/runs/{run_id}")
def get_run(run_id):
    with lock:
        if run_id not in runs: raise HTTPException(404,"Run not found")
        return runs[run_id]

@app.get("/api/runs/{run_id}/trajectory/{model}")
def get_traj(run_id,model):
    p=STORE.root/(run_id+"_"+model+".json")
    if not p.exists(): raise HTTPException(404,"Trajectory not found")
    return json.loads(p.read_text())

@app.get("/api/runs/{run_id}/export/{model}")
def export(run_id,model):
    p=STORE.root/(run_id+"_"+model+".json")
    if not p.exists(): raise HTTPException(404,"Trajectory not found")
    return FileResponse(p,filename=f"{model}_trajectory.json",media_type="application/json")
