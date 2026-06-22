import os
from pathlib import Path
from src.app.ingestion.parser import GrowwParser
from src.app.ingestion.scraper import GrowwScraper

SAMPLE_SLUG = "icici-prudential-technology-fund-direct-growth"

def test_groww_parser_next_data():
    """Verify that the parser correctly extracts structured data from __NEXT_DATA__."""
    html_path = Path("data/raw") / f"{SAMPLE_SLUG}.html"
    assert html_path.exists(), "Sample HTML file is required for this test"
    
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    parser = GrowwParser()
    result = parser.parse_html(html_content, url=f"https://groww.in/mutual-funds/{SAMPLE_SLUG}", fetch_date="2026-06-22")
    
    assert result is not None
    assert result["slug"] == SAMPLE_SLUG
    assert result["last_updated"] == "2026-06-22"
    
    sections = result["sections"]
    
    # Check identity
    identity = sections["identity"]
    assert "Technology" in identity["scheme_name"]
    assert identity["isin"] == "INF109K01Z48"
    assert identity["category"] == "Equity"
    assert identity["sub_category"] == "Sectoral"
    assert identity["plan_type"] == "Direct"
    
    # Check performance & pricing
    perf = sections["performance_pricing"]
    assert perf["nav"] == "₹187.48"
    assert perf["nav_date"] == "19-Jun-2026"
    assert perf["returns"]["1Y"] == "-16.33%"
    assert perf["returns"]["3Y"] == "7.99%"
    assert perf["returns"]["5Y"] == "6.93%"
    
    # Check expense ratio
    assert sections["expense_ratio"]["value"] == "1.26%"
    
    # Check exit load
    assert "Exit load of 1%" in sections["exit_load"]["exit_load_text"]
    
    # Check minimum investment
    min_inv = sections["minimum_investment"]
    assert min_inv["min_sip"] == "₹100"
    assert min_inv["min_lumpsum"] == "₹5000"
    
    # Check benchmark
    assert "BSE Teck" in sections["benchmark"]["name"]
    
    # Check fund management
    managers = sections["fund_management"]["managers"]
    assert len(managers) > 0
    # The managers list contains Sharmila D'Silva
    manager_names = [m["name"] for m in managers]
    assert any("Sharmila" in name for name in manager_names)
    
    # Check risk metrics
    risk = sections["risk_metrics"]
    assert risk["standard_deviation"] == "18.85186406285155"
    assert risk["riskometer_level"] == "Very High"
    
    # Check portfolio composition
    portfolio = sections["portfolio_composition"]
    assert "₹13,358.29 Cr" in portfolio["aum"]
    assert len(portfolio["top_holdings"]) > 0
    assert portfolio["top_holdings"][0]["company_name"] == "Infosys Ltd"
    assert portfolio["top_holdings"][0]["allocation_pct"] > 0.0

def test_groww_scraper_local_cache():
    """Verify that GrowwScraper loads from local cache without making requests."""
    scraper = GrowwScraper(raw_data_dir="data/raw")
    url = f"https://groww.in/mutual-funds/{SAMPLE_SLUG}"
    
    # Should resolve without network requests
    html_content = scraper.fetch_page(url, SAMPLE_SLUG, force=False)
    assert html_content is not None
    assert "<!DOCTYPE html>" in html_content
