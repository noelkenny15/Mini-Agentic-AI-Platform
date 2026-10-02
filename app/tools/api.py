from fastapi import FastAPI
from pydantic import BaseModel
from app.tools.server import ToolServer

app=FastAPI(title="Mini Agentic Tool Server", version="1.0")
tools=ToolServer()

class EnvRequest(BaseModel):
    service:str
    env:str

@app.get("/tools")
def list_tools(): return {"version":"1.0","tools":[{"name":k,"version":v} for k,v in tools.__class__.__dict__.items() if callable(v) and not k.startswith("_") and k in {"get_logs","get_metrics","simulate_restart","simulate_scale","get_dependency_graph"}]}

@app.post("/tools/logs")
def logs(req: EnvRequest): return tools.get_logs(req.service,"15m",req.env)
@app.post("/tools/metrics")
def metrics(req: EnvRequest): return tools.get_metrics(req.service,req.env)
