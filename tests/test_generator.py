import pytest
from unittest.mock import patch
from src.app.services.generator import LLMGenerator

@pytest.fixture(autouse=True)
def mock_settings():
    with patch("src.app.services.generator.load_settings") as mock:
        from src.app.config import Settings
        mock.return_value = Settings(gemini_api_key=None, groq_api_key=None)
        yield

def test_generator_empty_context():
    res = LLMGenerator.generate("What is the expense ratio?", [])
    assert res["is_refusal"] is True
    assert res["answer"] == "I cannot find the answer in the source pages."
    assert res["citation_url"] == "https://www.amfiindia.com/"

def test_generator_mock_expense_ratio():
    mock_chunks = [
        {
            "id": "icici-prudential-large-cap-fund-direct-growth#expense_ratio#0",
            "text": "Scheme: ICICI Prudential Large Cap Fund. Expense Ratio is 1.05%. This is a fee payable to a mutual fund house for managing your mutual fund investments.",
            "slug": "icici-prudential-large-cap-fund-direct-growth",
            "section": "expense_ratio",
            "source_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
            "last_updated": "2026-06-22"
        }
    ]
    
    res = LLMGenerator.generate("What is the expense ratio of ICICI Prudential Large Cap Fund?", mock_chunks)
    assert res["is_refusal"] is False
    assert "Expense Ratio is 1.05%" in res["answer"]
    assert res["citation_url"] == "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth"
    assert res["last_updated"] == "2026-06-22"
    assert res["disclaimer"] == "Facts-only. No investment advice."
    
    # Check sentence count <= 3
    import re
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', res["answer"]) if s.strip()]
    assert len(sentences) <= 3

def test_generator_mock_exit_load():
    mock_chunks = [
        {
            "id": "icici-prudential-commodities-fund-direct-growth#exit_load#0",
            "text": "Scheme: ICICI Prudential Commodities Fund. Exit Load Details: Exit load of 1% if redeemed within 15 days. Entry Load Details: 0.00% (No Entry Load).",
            "slug": "icici-prudential-commodities-fund-direct-growth",
            "section": "exit_load",
            "source_url": "https://groww.in/mutual-funds/icici-prudential-commodities-fund-direct-growth",
            "last_updated": "2026-06-22"
        }
    ]
    
    res = LLMGenerator.generate("What is the exit load on ICICI Prudential Commodities Fund?", mock_chunks)
    assert res["is_refusal"] is False
    assert "Exit load of 1% if redeemed within 15 days" in res["answer"]
    assert res["citation_url"] == "https://groww.in/mutual-funds/icici-prudential-commodities-fund-direct-growth"
