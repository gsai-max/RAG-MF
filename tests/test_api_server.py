from fastapi.testclient import TestClient
from src.app.api_server import app, rate_limiter_dep

def test_health_endpoint():
    """Verify that the health check endpoint returns a 200 status and ok status."""
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "env" in data

def test_chat_factual_query():
    """Verify that a standard factual query runs through the RAG pipeline and returns successfully."""
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"message": "What is the exit load of ICICI Prudential Large Cap Fund?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["is_refusal"] is False
        assert data["disclaimer"] == "Facts-only. No investment advice."
        assert "citation_url" in data
        assert "groww.in" in data["citation_url"]
        assert "last_updated" in data

def test_chat_advisory_query():
    """Verify that an advisory query is intercepted and routed to the Refusal Handler."""
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"message": "Should I invest in ICICI Prudential Large Cap Fund?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_refusal"] is True
        assert "cannot provide investment advice" in data["answer"]
        assert "sebi.gov.in" in data["citation_url"]

def test_chat_pii_scrubbing():
    """Verify that PII patterns are scrubbed from queries before pipeline execution."""
    with TestClient(app) as client:
        # Pass a query containing PAN pattern and Aadhaar pattern
        response = client.post(
            "/api/chat",
            json={
                "message": "Who is the fund manager of ICICI Prudential Commodities Fund? PAN ABCDE1234F Aadhaar 1234-5678-9012"
            }
        )
        assert response.status_code == 200
        data = response.json()
        # The query should resolve the fund manager section properly and succeed
        assert data["is_refusal"] is False
        assert "citation_url" in data
        assert "commodities" in data["citation_url"]

def test_rate_limiter():
    """Verify that rate limiter successfully triggers HTTP 429 Too Many Requests."""
    # Backup original values
    original_requests = rate_limiter_dep.limiter.requests
    original_window = rate_limiter_dep.limiter.window
    
    # Configure tight rate limit for testing: 2 requests per 10 seconds
    rate_limiter_dep.limiter.requests = 2
    rate_limiter_dep.limiter.window = 10
    rate_limiter_dep.limiter.history = {}
    
    try:
        with TestClient(app) as client:
            # Request 1: Should pass
            res1 = client.post("/api/chat", json={"message": "What is the exit load of ICICI Prudential Large Cap Fund?"})
            assert res1.status_code == 200
            
            # Request 2: Should pass
            res2 = client.post("/api/chat", json={"message": "What is the exit load of ICICI Prudential Large Cap Fund?"})
            assert res2.status_code == 200
            
            # Request 3: Should fail with 429
            res3 = client.post("/api/chat", json={"message": "What is the exit load of ICICI Prudential Large Cap Fund?"})
            assert res3.status_code == 429
            assert "Rate limit exceeded" in res3.json()["detail"]
    finally:
        # Restore configuration and clean history
        rate_limiter_dep.limiter.requests = original_requests
        rate_limiter_dep.limiter.window = original_window
        rate_limiter_dep.limiter.history = {}

def test_validation_errors():
    """Verify that invalid request body yields structured 422 HTTP validation errors."""
    with TestClient(app) as client:
        # Scenario 1: Empty dict payload
        res1 = client.post("/api/chat", json={})
        assert res1.status_code == 422
        data1 = res1.json()
        assert "Invalid request payload format" in data1["detail"]
        assert "errors" in data1

        # Scenario 2: Wrong attribute name
        res2 = client.post("/api/chat", json={"query": "What is the exit load?"})
        assert res2.status_code == 422
        data2 = res2.json()
        assert "Invalid request payload format" in data2["detail"]

def test_get_funds_endpoint():
    """Verify that the GET /api/funds endpoint returns the fund metadata registry list."""
    with TestClient(app) as client:
        response = client.get("/api/funds")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        first_fund = data[0]
        assert "slug" in first_fund
        assert "scheme_name" in first_fund
        assert "category" in first_fund
        assert "source_url" in first_fund
        assert "nav" in first_fund
        assert "nav_date" in first_fund

def test_chat_multiple_selected_funds():
    """Verify that `/api/chat` successfully processes selected_funds in payload and answers correctly."""
    with TestClient(app) as client:
        selected = [
            "icici-prudential-commodities-fund-direct-growth",
            "icici-prudential-technology-fund-direct-growth"
        ]
        response = client.post(
            "/api/chat",
            json={
                "message": "exit load of both",
                "selected_funds": selected
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["is_refusal"] is False
        assert "citation_url" in data
        urls = data["citation_url"].split(",")
        assert len(urls) == 2
        assert any("commodities" in u for u in urls)
        assert any("technology" in u for u in urls)
        assert "last_updated" in data

