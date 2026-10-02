import argparse, json
from app.core.models import Incident
from app.core.workflow import IncidentWorkflow

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--incident", default="Payment service latency is high and error rate crossed 5% due to repeated inventory-service timeouts.")
    p.add_argument("--service", default="payment-service")
    p.add_argument("--env", default="staging")
    p.add_argument("--version", default="v1.4")
    p.add_argument("--trace", default="agent_trace.db")
    p.add_argument("--replay")
    p.add_argument("--llm", action="store_true", help="Use local Ollama/Qwen reasoning for planning and action proposals")
    p.add_argument("--model", default="qwen2.5:7b")
    args = p.parse_args()
    wf = IncidentWorkflow(args.trace, use_llm=args.llm, llm_model=args.model)
    if args.replay:
        print(json.dumps(wf.trace.replay(args.replay), indent=2))
        return
    incident = Incident(incident_id="INC-001", description=args.incident, service=args.service, env=args.env, version=args.version)
    print(json.dumps(wf.run(incident), indent=2, default=str))

if __name__ == "__main__":
    main()
