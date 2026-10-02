# Trade-offs

## Simplified for the exercise
- Infrastructure actions are simulations; no cloud credentials or real SDKs are used.
- SQLite is used for workflow traces instead of a distributed event store.
- The knowledge graph is an in-memory NetworkX graph instead of Neo4j.
- Hybrid retrieval uses BM25 plus sentence-transformer embeddings locally.
- The state machine is implemented directly in Python rather than introducing a heavier orchestration platform.
- The LLM is not allowed to choose executable control-flow transitions. Deterministic validation owns state transitions and safety decisions.

## Production hardening
- Replace simulated tools with isolated, authenticated tool services.
- Add tenant identity and signed authorization context to every tool call.
- Use a durable workflow engine and append-only audit storage.
- Add human approval UI for production/high-blast-radius actions.
- Add secret management, rate limits, circuit breakers, tool allowlists, and stronger sandboxing.
- Add model/prompt registry with canary releases and rollback.
- Add distributed tracing with OpenTelemetry.
- Expand evaluations to cover adversarial prompts, tool failures, stale evidence, dependency changes, and partial execution.
