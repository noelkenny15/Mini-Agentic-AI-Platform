# Mini Agentic AI Platform

A local prototype for safe, auditable production-incident analysis and simulated remediation.

## Architecture

```text
Incident
   |
   v
Planner Agent ---- structured A2A ----> Investigator/RAG Agent
                                             |
                              BM25 + embeddings + metadata filters
                                             |
                                             v
                                      Evidence + graph
                                             |
                                             v
                                      Verifier Agent
                                  policy + blast radius
                                             |
                              approved / human approval
                                             |
                                             v
                                         Ops Agent
                                             |
                                     Tool abstraction
                                             |
                         simulated restart / scale / metrics
                                             |
                                             v
                                        Trace Store
```

## Requirements mapped

- 4 agents: `app/agents/agents.py`
- Structured A2A messages: `app/core/models.py`
- Explicit state machine: `app/core/state_machine.py`
- Retry/timeout-ready orchestration boundary: `app/core/workflow.py`
- Versioned MCP-style local tools: `app/tools/server.py`
- Hybrid RAG: `app/rag/retriever.py`
- Knowledge graph/blast radius: `app/rag/graph.py`
- Safety gates: `VerifierAgent`
- Replayable traces: `app/core/trace.py`
- Offline evaluation/tests: `tests/`
- CI/eval gate: `.github/workflows/ci.yml`

## Setup

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

The embedding model is downloaded the first time retrieval starts. If it is unavailable, the prototype still runs with the BM25 component and deterministic safety logic.

## Run

```bash
python -m app.main
```

Replay a trace:

```bash
python -m app.main --replay INC-001
```

Demonstrate production safety rejection:

```bash
python -m app.main --env prod
```

Run the local tool server:

```bash
uvicorn app.tools.api:app --reload
```

Run tests:

```bash
python -m pytest -q
```

## Safety model

The Verifier checks environment, blast radius, and evidence before an action can execute. Production incidents are routed to human approval. Agents never receive raw infrastructure SDK access.

## Incident example

`payment-service` has elevated latency and error rate caused by repeated calls timing out against `inventory-service`. The investigator retrieves runbook/log/metric evidence. The verifier checks that the incident is in staging, the blast radius is bounded, and timeout evidence supports the restart. The Ops agent then performs a simulated restart.

## Orchestration safety

Agent calls run through a bounded executor with a timeout and one retry. A failed/timeout agent call raises an error rather than silently advancing the workflow. State transitions remain owned by the workflow state machine.

## Optional local LLM mode

The platform can use a local Ollama model for the Planner and Ops proposal steps:

```bash
pip install -r requirements.txt
ollama pull qwen2.5:7b
python -m app.main --llm
```

The LLM is deliberately not allowed to execute tools. Its structured output is validated with Pydantic and then passed to the deterministic Verifier. Production actions require human approval, and tool execution occurs only after verification.
