import uuid
from app.core.models import *


class PlannerAgent:
    name = AgentName.planner

    def __init__(self, llm=None):
        self.llm = llm

    def run(self, incident: Incident):
        fallback = [
            "retrieve logs and metrics",
            "inspect runbook and dependencies",
            "propose lowest-risk remediation",
            "verify policy and blast radius",
            "execute only if approved",
            "validate result",
        ]
        objective = "Diagnose the incident, select the lowest-risk remediation, verify safety, and validate the result."
        if self.llm:
            try:
                plan = self.llm.json(
                    system=(
                        "You are the Planner Agent in a production incident platform. "
                        "Return JSON only with keys 'steps' (array of concise strings) and 'objective' (string). "
                        "Do not execute tools or invent evidence. Keep the plan to 4-8 steps."
                    ),
                    prompt=f"Incident:\n{incident.model_dump_json(indent=2)}",
                    schema=Plan,
                )
                fallback = plan["steps"]
                objective = plan["objective"]
            except Exception:
                # LLM failure must degrade safely to the deterministic plan.
                pass
        return A2AMessage(
            message_id=str(uuid.uuid4()),
            workflow_id=incident.incident_id,
            sender=self.name,
            recipient=AgentName.investigator,
            type=MessageType.plan,
            payload={"steps": fallback, "objective": objective, "incident": incident.model_dump()},
        )


class InvestigatorAgent:
    name = AgentName.investigator

    def __init__(self, retriever, tools, graph):
        self.retriever, self.tools, self.graph = retriever, tools, graph

    def run(self, incident: Incident):
        evidence = self.retriever.search(incident.description, incident.service, incident.env, incident.version)
        logs = self.tools.get_logs(incident.service, "15m", incident.env)
        metrics = self.tools.get_metrics(incident.service, incident.env)
        deps = self.graph.blast_radius(incident.service)
        return A2AMessage(
            message_id=str(uuid.uuid4()),
            workflow_id=incident.incident_id,
            sender=self.name,
            recipient=AgentName.ops,
            type=MessageType.evidence,
            payload={
                "evidence": [e.model_dump() for e in evidence],
                "logs": logs.model_dump(),
                "metrics": metrics.model_dump(),
                "blast_graph": deps,
            },
        )


class OpsAgent:
    name = AgentName.ops

    def __init__(self, tools, llm=None):
        self.tools = tools
        self.llm = llm

    def propose(self, incident: Incident, evidence_msg: A2AMessage):
        evidence = evidence_msg.payload["evidence"]
        default = ActionProposal(
            action="restart",
            service=incident.service,
            env=incident.env,
            rationale="Restart is the documented remediation for this timeout incident.",
            evidence_ids=[e["source_id"] for e in evidence[:3]],
        )
        if not self.llm:
            return default
        try:
            result = self.llm.json(
                system=(
                    "You are the Infra/Ops Agent. Propose one concrete remediation action based only on supplied evidence. "
                    "Return JSON matching the requested schema. Allowed actions are restart or scale. "
                    "Never claim you executed anything. Never change the environment or service from the incident."
                ),
                prompt=(
                    f"Incident:\n{incident.model_dump_json(indent=2)}\n\n"
                    f"Evidence:\n{evidence_msg.model_dump_json(indent=2)}"
                ),
                schema=ActionProposal,
            )
            proposal = ActionProposal.model_validate(result)
            # Defense-in-depth: normalize immutable execution context from trusted incident data.
            proposal.service = incident.service
            proposal.env = incident.env
            proposal.evidence_ids = [x for x in proposal.evidence_ids if x in {e["source_id"] for e in evidence}]
            if proposal.action not in {"restart", "scale"}:
                return default
            return proposal
        except Exception:
            return default

    def run(self, action: ActionProposal):
        if action.action == "restart":
            return self.tools.simulate_restart(action.service, action.env)
        if action.action == "scale":
            try:
                replicas = int(action.parameters["replicas"])
            except (KeyError, TypeError, ValueError):
                return ToolEnvelope(ok=False, tool="simulate_scale", error={"code": "INVALID_PARAMETERS", "message": "replicas is required"})
            return self.tools.simulate_scale(action.service, replicas, action.env)
        return ToolEnvelope(ok=False, tool="unknown", error={"code": "UNKNOWN_ACTION", "message": action.action})


class VerifierAgent:
    name = AgentName.verifier

    def __init__(self, graph):
        self.graph = graph

    def run(self, incident: Incident, evidence_msg: A2AMessage, action: ActionProposal):
        evidence = evidence_msg.payload["evidence"]
        deps = self.graph.blast_radius(incident.service)
        reasons = []
        approved = True
        env = incident.env.lower()
        if env in {"prod", "production"}:
            approved = False
            reasons.append("Production actions require human approval")
        if len(deps) > 3:
            approved = False
            reasons.append("Blast radius exceeds autonomous limit")
        if action.action == "restart" and not any("timeout" in e["text"].lower() for e in evidence):
            approved = False
            reasons.append("No timeout evidence supporting restart")
        if action.service != incident.service or action.env.lower() != incident.env.lower():
            approved = False
            reasons.append("Action scope does not match incident scope")
        if action.action == "scale":
            replicas = action.parameters.get("replicas")
            if not isinstance(replicas, int) or not 1 <= replicas <= 10:
                approved = False
                reasons.append("Scale replicas must be an integer from 1 to 10")
        if approved:
            reasons.append("Policy, environment, and blast-radius checks passed")
        action.rationale = action.rationale.replace("this staging timeout incident", "this timeout incident")
        return VerificationResult(
            approved=approved,
            reasons=reasons,
            blast_radius_services=deps,
            autonomy_tier="AUTO" if approved else "HUMAN_APPROVAL",
            action=action,
        )
