import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from app.core.models import Incident
from app.core.state_machine import State
from app.core.trace import TraceStore
from app.agents.agents import PlannerAgent, InvestigatorAgent, VerifierAgent, OpsAgent
from app.rag.retriever import HybridRetriever
from app.rag.graph import ServiceGraph
from app.tools.server import ToolServer
from app.llm.ollama_service import OllamaLLM


class IncidentWorkflow:
    @staticmethod
    def _invoke(fn, *args, timeout_s=5, retries=1):
        last = None
        for attempt in range(retries + 1):
            try:
                with ThreadPoolExecutor(max_workers=1) as ex:
                    return ex.submit(fn, *args).result(timeout=timeout_s)
            except Exception as exc:
                last = exc
                if attempt < retries:
                    time.sleep(0.05)
        raise last

    def __init__(self, trace_path="agent_trace.db", use_llm=False, llm_model="qwen2.5:7b"):
        self.trace = TraceStore(trace_path)
        self.tools = ToolServer()
        self.graph = ServiceGraph()
        self.retriever = HybridRetriever()
        self.llm = OllamaLLM(llm_model) if use_llm else None
        self.planner = PlannerAgent(self.llm)
        self.investigator = InvestigatorAgent(self.retriever, self.tools, self.graph)
        self.ops = OpsAgent(self.tools, self.llm)
        self.verifier = VerifierAgent(self.graph)

    def run(self, incident: Incident):
        wid = incident.incident_id
        state = State.START
        self.trace.record(wid, "workflow", "start", "state", incident.model_dump())

        state = State.PLAN
        t = time.perf_counter()
        plan = self._invoke(self.planner.run, incident)
        self.trace.record(wid, "planner", "plan", "a2a", plan.model_dump(), (time.perf_counter() - t) * 1000)

        state = State.INVESTIGATE
        t = time.perf_counter()
        evidence = self._invoke(self.investigator.run, incident)
        self.trace.record(wid, "investigator", "retrieve", "a2a", evidence.model_dump(), (time.perf_counter() - t) * 1000)

        state = State.PROPOSE if hasattr(State, "PROPOSE") else State.VERIFY
        t = time.perf_counter()
        proposal = self._invoke(self.ops.propose, incident, evidence)
        proposal_msg = {
            "message_id": f"proposal-{wid}",
            "workflow_id": wid,
            "sender": "ops",
            "recipient": "verifier",
            "type": "action_proposal",
            "schema_version": "1.0",
            "payload": proposal.model_dump(),
        }
        self.trace.record(wid, "ops", "propose", "a2a", proposal_msg, (time.perf_counter() - t) * 1000)

        state = State.VERIFY
        t = time.perf_counter()
        verification = self._invoke(self.verifier.run, incident, evidence, proposal)
        self.trace.record(wid, "verifier", "policy_check", "decision", verification.model_dump(), (time.perf_counter() - t) * 1000)
        if not verification.approved:
            self.trace.record(wid, "workflow", "rejected", "state", {"reasons": verification.reasons})
            return {"state": State.REJECTED, "plan": plan.model_dump(), "evidence": evidence.model_dump(), "verification": verification.model_dump()}

        state = State.EXECUTE
        t = time.perf_counter()
        result = self._invoke(self.ops.run, verification.action)
        self.trace.record(wid, "ops", "execute", "tool_call", result.model_dump(), (time.perf_counter() - t) * 1000)

        state = State.VALIDATE
        self.trace.record(wid, "workflow", "validate", "state", {"status": "simulated post-action validation passed"})
        state = State.COMPLETE
        return {
            "state": state,
            "plan": plan.model_dump(),
            "evidence": evidence.model_dump(),
            "proposal": proposal.model_dump(),
            "verification": verification.model_dump(),
            "action_result": result.model_dump(),
        }
