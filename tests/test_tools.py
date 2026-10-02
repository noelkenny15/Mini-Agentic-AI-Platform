from app.tools.server import ToolServer

def test_tool_scope_and_contract():
    t=ToolServer(); r=t.get_metrics("payment-service","staging")
    assert r.ok and r.tool=="get_metrics" and "error_rate" in r.data

def test_scale_limit():
    t=ToolServer(); r=t.simulate_scale("payment-service",99,"staging")
    assert not r.ok and r.error["code"]=="REPLICA_LIMIT"

def test_cross_env_rejected():
    t=ToolServer(); r=t.get_logs("payment-service","15m","dev")
    assert not r.ok and r.error["code"]=="INVALID_ENV"
