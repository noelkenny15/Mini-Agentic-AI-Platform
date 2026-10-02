import networkx as nx

class ServiceGraph:
    def __init__(self):
        self.g = nx.DiGraph()
        self.g.add_edges_from([
            ("payment-service", "inventory-service"),
            ("payment-service", "auth-service"),
            ("inventory-service", "database"),
        ])
        self.owners = {"payment-service":"payments-team", "inventory-service":"inventory-team", "auth-service":"identity-team", "database":"platform-team"}
        self.runbooks = {"payment-service":"runbook-payment-latency", "inventory-service":"runbook-inventory"}

    def blast_radius(self, service: str, depth: int = 1):
        affected = {service}
        frontier = {service}
        for _ in range(depth):
            nxt = set()
            for node in frontier: nxt.update(self.g.successors(node))
            affected.update(nxt); frontier = nxt
        return sorted(affected)
