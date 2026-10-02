import json, sqlite3, time
from pathlib import Path
from typing import Any

class TraceStore:
    def __init__(self, path: str = "agent_trace.db"):
        self.path = Path(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS trace (
            id INTEGER PRIMARY KEY AUTOINCREMENT, workflow_id TEXT, agent TEXT,
            step TEXT, kind TEXT, payload TEXT, latency_ms REAL, cost_estimate REAL,
            ts REAL)""")
        self.conn.commit()

    def record(self, workflow_id: str, agent: str, step: str, kind: str,
               payload: Any, latency_ms: float = 0.0, cost_estimate: float = 0.0):
        redacted = self._redact(payload)
        self.conn.execute("INSERT INTO trace(workflow_id,agent,step,kind,payload,latency_ms,cost_estimate,ts) VALUES(?,?,?,?,?,?,?,?)",
                          (workflow_id, agent, step, kind, json.dumps(redacted, default=str), latency_ms, cost_estimate, time.time()))
        self.conn.commit()

    def replay(self, workflow_id: str):
        rows = self.conn.execute("SELECT agent,step,kind,payload,latency_ms,cost_estimate,ts FROM trace WHERE workflow_id=? ORDER BY id", (workflow_id,)).fetchall()
        return [dict(zip(["agent","step","kind","payload","latency_ms","cost_estimate","ts"], r)) for r in rows]

    @staticmethod
    def _redact(value):
        if isinstance(value, dict):
            return {k: ("[REDACTED]" if k.lower() in {"token","password","secret","api_key"} else TraceStore._redact(v)) for k,v in value.items()}
        if isinstance(value, list): return [TraceStore._redact(v) for v in value]
        return value
