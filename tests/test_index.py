import os
import shutil
import json
from pathlib import Path
from src.app.ingestion.index import (
    get_chroma_client,
    get_mf_collection,
    index_chunks,
    update_scheme_metadata_index,
    METADATA_INDEX_FILE
)

TEST_DB_PATH = Path("data/test_index")

def setup_module(module):
    """Clean up any leftover test databases before running tests."""
    if TEST_DB_PATH.exists():
        try:
            shutil.rmtree(TEST_DB_PATH, ignore_errors=True)
        except Exception:
            pass

def teardown_module(module):
    """Clean up test databases after tests run."""
    if TEST_DB_PATH.exists():
        try:
            shutil.rmtree(TEST_DB_PATH, ignore_errors=True)
        except Exception:
            pass

def test_chroma_indexing():
    """Verify that we can initialize ChromaDB, insert chunks, and query them."""
    chunks = [
        {
            "id": "test-fund#identity#0",
            "text": "Scheme Name: Test Fund. Expense ratio is 1.05%.",
            "metadata": {
                "slug": "test-fund",
                "scheme_name": "Test Fund",
                "section": "identity",
                "source_url": "https://groww.in/test-fund",
                "last_updated": "2026-06-22"
            }
        }
    ]
    
    # 1. Index chunks in test directory
    index_chunks(chunks, db_path=TEST_DB_PATH)
    
    # 2. Re-establish connection and verify collection size
    client = get_chroma_client(db_path=TEST_DB_PATH)
    collection = get_mf_collection(client)
    
    assert collection.count() == 1
    
    # 3. Query documents and verify details
    results = collection.get(ids=["test-fund#identity#0"])
    assert len(results["documents"]) == 1
    assert "Test Fund" in results["documents"][0]
    assert results["metadatas"][0]["slug"] == "test-fund"

def test_metadata_index_registry():
    """Verify that the metadata lookup JSON register is created and updated correctly."""
    processed_data = {
        "slug": "test-fund",
        "source_url": "https://groww.in/test-fund",
        "last_updated": "2026-06-22",
        "sections": {
            "identity": {
                "scheme_name": "Test Fund",
                "category": "Equity",
                "sub_category": "Large Cap"
            },
            "performance_pricing": {
                "nav": "₹150.00",
                "nav_date": "19-Jun-2026"
            }
        }
    }
    
    update_scheme_metadata_index(processed_data, db_path=TEST_DB_PATH)
    
    meta_file = TEST_DB_PATH / METADATA_INDEX_FILE
    assert meta_file.exists()
    
    with open(meta_file, "r", encoding="utf-8") as f:
        meta_index = json.load(f)
        
    assert "test-fund" in meta_index
    entry = meta_index["test-fund"]
    assert entry["scheme_name"] == "Test Fund"
    assert entry["category"] == "Equity — Large Cap"
    assert entry["source_url"] == "https://groww.in/test-fund"
    assert entry["nav"] == "₹150.00"
