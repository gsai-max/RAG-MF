import logging

logger = logging.getLogger(__name__)

def reconstruct_section_text(section_name: str, fields: dict, scheme_name: str) -> list[str]:
    """
    Reconstruct raw section details into semantic, readable text paragraphs.
    For fund_management, returns a list of separate manager texts to keep profiles distinct.
    """
    texts = []
    
    if section_name == "identity":
        texts.append(
            f"Scheme Name: {fields.get('scheme_name', scheme_name)}. "
            f"Fund House: {fields.get('fund_house', 'N/A')}. "
            f"ISIN: {fields.get('isin', 'N/A')}. "
            f"Category: {fields.get('category', 'N/A')} — {fields.get('sub_category', 'N/A')}. "
            f"Plan Type: {fields.get('plan_type', 'Direct')}. "
            f"Option: {fields.get('option', 'Growth')}. "
            f"Launch Date: {fields.get('launch_date', 'N/A')}."
        )
        
    elif section_name == "performance_pricing":
        returns = fields.get("returns", {})
        returns_text = ", ".join([f"{k}: {v}" for k, v in returns.items() if v != "N/A"])
        texts.append(
            f"Scheme: {scheme_name}. "
            f"Net Asset Value (NAV): {fields.get('nav', 'N/A')} as of {fields.get('nav_date', 'N/A')}. "
            f"Historical Returns: {returns_text or 'N/A'}."
        )
        
    elif section_name == "expense_ratio":
        texts.append(
            f"Scheme: {scheme_name}. "
            f"Expense Ratio is {fields.get('value', 'N/A')}. "
            f"Description: {fields.get('definition', '')}"
        )
        
    elif section_name == "exit_load":
        texts.append(
            f"Scheme: {scheme_name}. "
            f"Exit Load Details: {fields.get('exit_load_text', 'N/A')}. "
            f"Entry Load Details: {fields.get('entry_load', '0.00% (No Entry Load)')}."
        )
        
    elif section_name == "minimum_investment":
        sip_dates = fields.get("sip_dates", [])
        dates_text = f" Available SIP dates: {', '.join(map(str, sip_dates))}." if sip_dates else ""
        texts.append(
            f"Scheme: {scheme_name}. "
            f"Minimum SIP investment: {fields.get('min_sip', 'N/A')}. "
            f"Minimum lumpsum investment: {fields.get('min_lumpsum', 'N/A')}.{dates_text}"
        )
        
    elif section_name == "benchmark":
        texts.append(
            f"Scheme: {scheme_name}. "
            f"Benchmark Index Name: {fields.get('name', 'N/A')} (Benchmark Code: {fields.get('code', 'N/A')})."
        )
        
    elif section_name == "tax":
        texts.append(
            f"Scheme: {scheme_name}. "
            f"Taxation Rules: {fields.get('tax_impact', 'N/A')}"
        )
        
    elif section_name == "fund_management":
        # Keep manager profiles distinct by generating one text block per manager
        for mgr in fields.get("managers", []):
            texts.append(
                f"Scheme: {scheme_name}. "
                f"Fund Manager: {mgr.get('name', 'N/A')} (managing since {mgr.get('date_from', 'N/A')}). "
                f"Education: {mgr.get('education', 'N/A')}. "
                f"Experience: {mgr.get('experience', 'N/A')}."
            )
            
    elif section_name == "risk_metrics":
        texts.append(
            f"Scheme: {scheme_name}. "
            f"Riskometer Level: {fields.get('riskometer_level', 'N/A')}. "
            f"Risk Metrics: Standard Deviation is {fields.get('standard_deviation', 'N/A')}, "
            f"Sharpe Ratio is {fields.get('sharpe_ratio', 'N/A')}, "
            f"Sortino Ratio is {fields.get('sortino_ratio', 'N/A')}, "
            f"Beta is {fields.get('beta', 'N/A')}, "
            f"Alpha is {fields.get('alpha', 'N/A')}."
        )
        
    elif section_name == "portfolio_composition":
        holdings = fields.get("top_holdings", [])
        holdings_list = []
        for idx, h in enumerate(holdings):
            holdings_list.append(f"{idx+1}. {h.get('company_name')} in {h.get('sector_name')} ({h.get('allocation_pct') or 0.0:.2f}%)")
        holdings_text = "; ".join(holdings_list)
        
        texts.append(
            f"Scheme: {scheme_name}. "
            f"Assets Under Management (AUM / Fund Size): {fields.get('aum', 'N/A')}. "
            f"Portfolio Turnover Ratio: {fields.get('portfolio_turnover', 'N/A')}. "
            f"Top Holdings: {holdings_text or 'N/A'}."
        )
        
    elif section_name == "investment_objective":
        texts.append(
            f"Scheme: {scheme_name}. "
            f"Investment Objective / Fund Strategy: {fields.get('objective', 'N/A')}"
        )
        
    elif section_name == "fund_house":
        texts.append(
            f"Fund House (AMC): {fields.get('name', 'N/A')}. "
            f"Official Website: {fields.get('website', 'N/A')}. "
            f"Incorporation Date: {fields.get('incorporation_date', 'N/A')}."
        )
        
    return texts

def generate_chunks_from_processed_json(processed_data: dict) -> list[dict]:
    """
    Read parsed JSON structure and yield structured semantic chunk objects.
    """
    slug = processed_data.get("slug")
    url = processed_data.get("source_url")
    last_updated = processed_data.get("last_updated")
    sections = processed_data.get("sections", {})
    
    # Try to find scheme name
    scheme_name = sections.get("identity", {}).get("scheme_name", slug)
    
    chunks = []
    
    for section_name, fields in sections.items():
        reconstructed_texts = reconstruct_section_text(section_name, fields, scheme_name)
        for idx, text in enumerate(reconstructed_texts):
            chunks.append({
                "id": f"{slug}#{section_name}#{idx}",
                "text": text,
                "metadata": {
                    "slug": slug,
                    "scheme_name": scheme_name,
                    "section": section_name,
                    "source_url": url,
                    "last_updated": last_updated
                }
            })
            
    return chunks
