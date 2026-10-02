from typing import Any
from app.core.models import ToolEnvelope

TOOLS = {"get_logs":"1.0","get_metrics":"1.0","simulate_restart":"1.0","simulate_scale":"1.0","get_dependency_graph":"1.0"}

class ToolServer:
    def __init__(self):
        self.metrics = {"payment-service":{"p95_ms":3800,"error_rate":7.2,"cpu":81,"replicas":4}}

    def _scope(self, service, env):
        if env not in {"staging", "prod"}: return ToolEnvelope(ok=False, tool="scope", error={"code":"INVALID_ENV","message":"Unsupported environment"})
        return None

    def get_logs(self, service: str, timeframe: str, env: str):
        err=self._scope(service,env)
        if err:return err
        return ToolEnvelope(ok=True, tool="get_logs", data={"service":service,"env":env,"timeframe":timeframe,"logs":["ERROR payment timeout calling inventory-service","Repeated timeout observed across payment pods"]})

    def get_metrics(self, service: str, env: str):
        err=self._scope(service,env)
        if err:return err
        return ToolEnvelope(ok=True, tool="get_metrics", data=self.metrics.get(service,{"p95_ms":120,"error_rate":0.5,"cpu":30,"replicas":2}))

    def simulate_restart(self, service: str, env: str):
        err=self._scope(service,env)
        if err:return err
        return ToolEnvelope(ok=True, tool="simulate_restart", data={"action":"restart","service":service,"env":env,"status":"SIMULATED","message":"Restart simulated; no real infrastructure touched."})

    def simulate_scale(self, service: str, replicas: int, env: str):
        err=self._scope(service,env)
        if err:return err
        if not 1 <= replicas <= 10: return ToolEnvelope(ok=False, tool="simulate_scale", error={"code":"REPLICA_LIMIT","message":"replicas must be 1..10"})
        return ToolEnvelope(ok=True, tool="simulate_scale", data={"action":"scale","service":service,"env":env,"replicas":replicas,"status":"SIMULATED"})

    def get_dependency_graph(self, service: str, env: str):
        from app.rag.graph import ServiceGraph
        err=self._scope(service,env)
        if err:return err
        g=ServiceGraph()
        return ToolEnvelope(ok=True, tool="get_dependency_graph", data={"service":service,"env":env,"dependencies":g.blast_radius(service)})
