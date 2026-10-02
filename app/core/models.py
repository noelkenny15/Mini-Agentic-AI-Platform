from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class AgentName(str, Enum):
    planner = "planner"
    investigator = "investigator"
    ops = "ops"
    verifier = "verifier"

class MessageType(str, Enum):
    incident = "incident"
    plan = "plan"
    evidence = "evidence"
    action_proposal = "action_proposal"
    verification = "verification"
    result = "result"

class A2AMessage(BaseModel):
    message_id: str
    workflow_id: str
    sender: AgentName
    recipient: AgentName | None = None
    type: MessageType
    schema_version: str = "1.0"
    payload: dict[str, Any]

class Incident(BaseModel):
    incident_id: str
    description: str
    service: str
    env: str = "staging"
    version: str = "unknown"
    severity: str = "SEV-2"

class Evidence(BaseModel):
    source_id: str
    source_type: str
    service: str
    env: str
    version: str | None = None
    text: str
    score: float

class Plan(BaseModel):
    steps: list[str] = Field(min_length=1, max_length=10)
    objective: str

class ActionProposal(BaseModel):
    action: str
    service: str
    env: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)

class VerificationResult(BaseModel):
    approved: bool
    reasons: list[str]
    blast_radius_services: list[str]
    autonomy_tier: str
    action: ActionProposal

class ToolEnvelope(BaseModel):
    ok: bool
    tool: str
    version: str = "1.0"
    data: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] | None = None
