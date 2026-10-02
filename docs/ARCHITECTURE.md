# Architecture Notes

## Control flow

The workflow owns state transitions. Agent messages are data, not executable control flow. Every stage records a trace event before moving to the next deterministic state.

## A2A contract

Every inter-agent message has `message_id`, `workflow_id`, sender, recipient, message type, schema version, and a typed payload. This prevents free-form chat from becoming an implicit protocol.

## Tool contract

Tools return a common `ToolEnvelope` containing success state, tool name/version, structured data, or structured error. Tool calls receive an explicit environment scope.

## Retrieval

Candidate documents are metadata-filtered by service/environment/version. BM25 provides lexical relevance and sentence-transformer embeddings provide semantic relevance. Scores are fused before evidence is returned.

## Safety

The verifier is deterministic: production is never autonomously executed, blast radius is bounded, and an action requires supporting timeout evidence. This is intentionally stricter than trusting model-generated reasoning.

## Replay

SQLite records workflow, agent, step, event kind, redacted payload, latency, cost estimate, and timestamp. A workflow can therefore be inspected after execution and replayed from its recorded trace.

## Versioning and Rollback

The prototype uses explicit version identifiers for tool contracts and A2A
schemas. The current artifact versions are:

- Platform: 1.0
- Planner Agent: 1.0
- Investigator Agent: 1.0
- Ops Agent: 1.0
- Verifier Agent: 1.0
- Prompt set: 1.0
- A2A schema: 1.0
- Tool contracts: 1.0

Agent, prompt, and tool changes are tracked through Git commits.

Rollback strategy:
1. Identify the last known-good Git commit/tag.
2. Restore that version of the agents, prompts, and tool contracts.
3. Run the complete offline test/evaluation suite.
4. Promote the restored version only after the CI gate passes.