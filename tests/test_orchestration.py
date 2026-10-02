import pytest
from app.core.workflow import IncidentWorkflow

def test_timeout_is_enforced():
    def slow():
        import time; time.sleep(0.2)
    with pytest.raises(TimeoutError):
        IncidentWorkflow._invoke(slow, timeout_s=0.01, retries=0)
