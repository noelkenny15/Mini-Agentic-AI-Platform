# Demo Script

1. Install dependencies and run tests.
2. Start the simulated tool API: `uvicorn app.tools.api:app --reload`.
3. Run the incident workflow with the default staging incident.
4. Point out the Planner -> Investigator -> Verifier -> Ops sequence.
5. Show retrieved evidence IDs and text.
6. Show the verifier's deterministic safety reasons and blast-radius list.
7. Show the simulated restart response proving no real infrastructure was touched.
8. Replay the workflow with `python -m app.main --replay INC-001`.
9. Run the same incident with `--env prod` and show that autonomous execution is rejected.
