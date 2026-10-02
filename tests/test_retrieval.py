from app.rag.retriever import HybridRetriever

def test_hybrid_retrieval_returns_cited_evidence():
    r=HybridRetriever().search("payment timeout inventory", "payment-service", "staging", "v1.4")
    assert r and r[0].source_id
