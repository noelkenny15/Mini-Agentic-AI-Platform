from app.core.workflow import IncidentWorkflow
from app.core.models import Incident

def test_staging_incident_auto_remediates(tmp_path):
    wf=IncidentWorkflow(str(tmp_path/"trace.db"))
    r=wf.run(Incident(incident_id="T1",description="payment timeout inventory-service",service="payment-service",env="staging",version="v1.4"))
    assert r["state"]=="COMPLETE"
    assert r["verification"]["approved"] is True

def test_prod_requires_human_approval(tmp_path):
    wf=IncidentWorkflow(str(tmp_path/"trace.db"))
    r=wf.run(Incident(incident_id="T2",description="payment timeout inventory-service",service="payment-service",env="prod",version="v1.4"))
    assert r["state"]=="REJECTED"
    assert "human approval" in " ".join(r["verification"]["reasons"]).lower()

def test_verifier_rejects_wrong_service():
    from app.agents.agents import VerifierAgent
    from app.core.models import Incident, A2AMessage, ActionProposal, AgentName, MessageType
    from app.rag.graph import ServiceGraph

    incident = Incident(
        incident_id="INC-UNSAFE",
        description="Payment service latency is high due to inventory timeouts.",
        service="payment-service",
        env="staging",
        version="v1.4",
        severity="SEV-2",
    )

    evidence = A2AMessage(
        message_id="evidence-unsafe",
        workflow_id=incident.incident_id,
        sender=AgentName.investigator,
        recipient=AgentName.verifier,
        type=MessageType.evidence,
        payload={
            "evidence": [
                {
                    "source_id": "timeout-001",
                    "source_type": "log",
                    "service": "payment-service",
                    "env": "staging",
                    "version": "v1.4",
                    "text": "ERROR payment timeout calling inventory-service",
                    "score": 1.0,
                }
            ]
        },
    )

    malicious_proposal = ActionProposal(
        action="restart",
        service="auth-service",
        env="staging",
        rationale="LLM-generated unsafe proposal",
        evidence_ids=["timeout-001"],
    )

    verifier = VerifierAgent(ServiceGraph())
    result = verifier.run(incident, evidence, malicious_proposal)

    assert result.approved is False
    assert "Action scope does not match incident scope" in result.reasons

def test_rejected_workflow_never_executes_ops(tmp_path, monkeypatch):
    wf = IncidentWorkflow(str(tmp_path / "trace.db"))

    def forbidden_execute(*args, **kwargs):
        raise AssertionError("Ops execution must not occur after verifier rejection")

    monkeypatch.setattr(wf.ops, "run", forbidden_execute)

    incident = Incident(
        incident_id="T3",
        description="payment timeout inventory-service",
        service="payment-service",
        env="prod",
        version="v1.4",
    )

    result = wf.run(incident)

    assert result["state"] == "REJECTED"
