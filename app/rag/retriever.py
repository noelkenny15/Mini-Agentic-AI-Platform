import numpy as np
import math
from collections import Counter

class BM25Okapi:
    def __init__(self, corpus, k1=1.5, b=0.75):
        self.corpus = corpus; self.k1=k1; self.b=b
        self.avgdl = sum(len(x) for x in corpus) / max(1,len(corpus))
        self.df=Counter()
        for doc in corpus:
            self.df.update(set(doc))
        self.n=len(corpus)
    def get_scores(self, query):
        q=list(query); scores=[]
        for doc in self.corpus:
            tf=Counter(doc); dl=len(doc); score=0.0
            for term in q:
                if term not in tf: continue
                idf=math.log(1+(self.n-self.df[term]+0.5)/(self.df[term]+0.5))
                score += idf * (tf[term]*(self.k1+1))/(tf[term]+self.k1*(1-self.b+self.b*dl/max(self.avgdl,1)))
            scores.append(score)
        return scores
from app.core.models import Evidence

DOCUMENTS = [
    {"id":"runbook-payment-latency","type":"runbook","service":"payment-service","env":"staging","version":"v1.4","text":"For elevated payment latency, inspect error rate and downstream inventory-service dependency. A rolling restart is allowed in staging when blast radius is limited to payment-service."},
    {"id":"log-payment-001","type":"log","service":"payment-service","env":"staging","version":"v1.4","text":"ERROR payment timeout calling inventory-service; upstream request exceeded 3000ms. Repeated timeout observed across payment pods."},
    {"id":"metric-payment-001","type":"metric","service":"payment-service","env":"staging","version":"v1.4","text":"p95 latency 3.8s; error rate 7.2%; pod CPU 81%; replicas 4."},
    {"id":"runbook-inventory","type":"runbook","service":"inventory-service","env":"staging","version":"v2.1","text":"Inventory-service is a dependency of payment-service. Do not restart inventory-service for payment incidents without owner approval."},
    {"id":"prod-policy","type":"policy","service":"payment-service","env":"prod","version":"v1.4","text":"Production restart requires human approval. Maximum one service may be affected by an autonomous action."},
]

class HybridRetriever:
    def __init__(self):
        self.docs = DOCUMENTS
        self.tokens = [d["text"].lower().split() for d in self.docs]
        self.bm25 = BM25Okapi(self.tokens)
        self._emb = None
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self._emb = self.model.encode([d["text"] for d in self.docs], normalize_embeddings=True)
        except Exception:
            self.model = None

    def search(self, query: str, service: str, env: str, version: str | None = None, k: int = 5):
        candidates = [i for i,d in enumerate(self.docs) if d["service"] == service and d["env"] == env and (version is None or d["version"] == version)]
        if not candidates:
            candidates = [i for i,d in enumerate(self.docs) if d["service"] == service and d["env"] == env]
        bm = self.bm25.get_scores(query.lower().split())
        if self.model is not None:
            q = self.model.encode([query], normalize_embeddings=True)[0]
            sem = np.asarray(self._emb) @ q
        else:
            sem = np.zeros(len(self.docs))
        results = []
        for i in candidates:
            score = 0.55 * float(bm[i]) + 0.45 * float(sem[i])
            results.append(Evidence(source_id=self.docs[i]["id"], source_type=self.docs[i]["type"], service=service, env=env, version=self.docs[i]["version"], text=self.docs[i]["text"], score=score))
        return sorted(results, key=lambda x: x.score, reverse=True)[:k]
