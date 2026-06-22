from src.app.services.response_validator import ResponseValidator
from src.app.services.refusal_handler import RefusalHandler

def test_validator_sentence_truncation():
    response = {
        "answer": "This is sentence one. This is sentence two. This is sentence three. This is sentence four that will be removed.",
        "citation_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
        "last_updated": "2026-06-22",
        "is_refusal": False
    }
    
    validated = ResponseValidator.validate_and_format("test query", response, [])
    assert validated["is_refusal"] is False
    assert "sentence four" not in validated["answer"]
    assert "sentence three" in validated["answer"]

def test_validator_citation_url_correction():
    response = {
        "answer": "The expense ratio is 1.05%.",
        "citation_url": "https://invalid-url.com/wrong-fund",
        "last_updated": "2026-06-22",
        "is_refusal": False
    }
    
    mock_chunks = [
        {
            "id": "icici-prudential-large-cap-fund-direct-growth#expense_ratio#0",
            "text": "Expense Ratio is 1.05%.",
            "slug": "icici-prudential-large-cap-fund-direct-growth",
            "section": "expense_ratio",
            "source_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
            "last_updated": "2026-06-22"
        }
    ]
    
    validated = ResponseValidator.validate_and_format("test query", response, mock_chunks)
    assert validated["citation_url"] == "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth"

def test_validator_advisory_leakage():
    response = {
        "answer": "The expense ratio of the fund is 1.05%, which means you should definitely buy it.",
        "citation_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
        "last_updated": "2026-06-22",
        "is_refusal": False
    }
    
    validated = ResponseValidator.validate_and_format("test query", response, [])
    assert validated["is_refusal"] is True
    assert "cannot provide investment advice" in validated["answer"]
    assert validated["citation_url"] == RefusalHandler.SEBI_URL

def test_validator_grounding_pass():
    response = {
        "answer": "The expense ratio of the fund is 1.05% with standard deviation of 18.85.",
        "citation_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
        "last_updated": "2026-06-22",
        "is_refusal": False
    }
    
    mock_chunks = [
        {
            "text": "Scheme details: Expense Ratio is 1.05%. The standard deviation is 18.85.",
            "slug": "icici-prudential-large-cap-fund-direct-growth",
            "section": "expense_ratio",
            "source_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
            "last_updated": "2026-06-22"
        }
    ]
    
    validated = ResponseValidator.validate_and_format("test query", response, mock_chunks)
    assert validated["is_refusal"] is False
    assert "1.05%" in validated["answer"]

def test_validator_grounding_fail():
    response = {
        "answer": "The expense ratio of the fund is 0.50% with standard deviation of 18.85.",
        "citation_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
        "last_updated": "2026-06-22",
        "is_refusal": False
    }
    
    mock_chunks = [
        {
            "text": "Scheme details: Expense Ratio is 1.05%. The standard deviation is 18.85.",
            "slug": "icici-prudential-large-cap-fund-direct-growth",
            "section": "expense_ratio",
            "source_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
            "last_updated": "2026-06-22"
        }
    ]
    
    validated = ResponseValidator.validate_and_format("test query", response, mock_chunks)
    assert validated["is_refusal"] is True
    assert "could not be verified" in validated["answer"]
