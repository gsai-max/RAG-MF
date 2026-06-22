from src.app.ingestion.chunk import generate_chunks_from_processed_json

def test_generate_chunks():
    """Verify that chunks are generated correctly from a parsed JSON structure."""
    mock_data = {
        "slug": "icici-prudential-large-cap-fund-direct-growth",
        "source_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
        "last_updated": "2026-06-22",
        "sections": {
            "identity": {
                "scheme_name": "ICICI Prudential Large Cap Fund Direct Growth",
                "fund_house": "ICICI Prudential Mutual Fund",
                "isin": "INF109K016L0",
                "category": "Equity",
                "sub_category": "Large Cap",
                "plan_type": "Direct",
                "option": "Growth",
                "launch_date": "01-Jan-2013"
            },
            "expense_ratio": {
                "value": "1.05%",
                "definition": "A fee payable to a mutual fund house for managing your mutual fund investments."
            },
            "fund_management": {
                "managers": [
                    {
                        "name": "Sankaran Naren",
                        "education": "B.Tech, MBA",
                        "experience": "Managing fund since 2026.",
                        "date_from": "2026-02-04"
                    },
                    {
                        "name": "Vaibhav Dusad",
                        "education": "B.Tech, M.Tech, MBA",
                        "experience": "Prior to joining ICICI Prudential AMC he worked with Morgan Stanley.",
                        "date_from": "2021-01-15"
                    }
                ]
            }
        }
    }
    
    chunks = generate_chunks_from_processed_json(mock_data)
    
    # We expect:
    # - 1 chunk for identity
    # - 1 chunk for expense_ratio
    # - 2 chunks for fund_management (one per manager)
    # Total = 4 chunks
    assert len(chunks) == 4
    
    # Check ID patterns
    expected_ids = {
        "icici-prudential-large-cap-fund-direct-growth#identity#0",
        "icici-prudential-large-cap-fund-direct-growth#expense_ratio#0",
        "icici-prudential-large-cap-fund-direct-growth#fund_management#0",
        "icici-prudential-large-cap-fund-direct-growth#fund_management#1"
    }
    ids = {c["id"] for c in chunks}
    assert ids == expected_ids
    
    # Verify metadata copies correctly
    for c in chunks:
        meta = c["metadata"]
        assert meta["slug"] == mock_data["slug"]
        assert meta["source_url"] == mock_data["source_url"]
        assert meta["last_updated"] == mock_data["last_updated"]
        assert meta["scheme_name"] == "ICICI Prudential Large Cap Fund Direct Growth"
        
    # Check specific texts
    identity_chunk = next(c for c in chunks if c["id"].endswith("identity#0"))
    assert "ISIN: INF109K016L0" in identity_chunk["text"]
    assert "Category: Equity — Large Cap" in identity_chunk["text"]
    
    expense_chunk = next(c for c in chunks if c["id"].endswith("expense_ratio#0"))
    assert "Expense Ratio is 1.05%" in expense_chunk["text"]
    
    # Verify manager profiles are isolated
    mgr_chunks = [c for c in chunks if "fund_management" in c["id"]]
    assert len(mgr_chunks) == 2
    assert "Sankaran Naren" in mgr_chunks[0]["text"]
    assert "Vaibhav Dusad" not in mgr_chunks[0]["text"]
    assert "Vaibhav Dusad" in mgr_chunks[1]["text"]
    assert "Sankaran Naren" not in mgr_chunks[1]["text"]
