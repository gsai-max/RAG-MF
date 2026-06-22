import os
from pathlib import Path
from src.app.config import load_settings, load_corpus, SchemeConfig

def test_load_settings():
    """Verify that settings are loaded properly with default values."""
    settings = load_settings()
    assert settings.env in ["dev", "staging", "prod"]
    assert isinstance(settings.port, int)
    assert settings.port == 8000

def test_load_corpus():
    """Verify that the corpus.yaml is loaded and contains 110 schemes."""
    schemes = load_corpus()
    assert len(schemes) == 110
    
    # Check typing and structure of the first scheme
    first_scheme = schemes[0]
    assert isinstance(first_scheme, SchemeConfig)
    assert first_scheme.slug is not None
    assert first_scheme.scheme_name is not None
    assert first_scheme.source_url.startswith("https://")
    
    # Verify a specific scheme is in the corpus
    technology_scheme = next((s for s in schemes if "Technology" in s.scheme_name), None)
    assert technology_scheme is not None
    assert technology_scheme.slug == "icici-prudential-technology-fund-direct-growth"
