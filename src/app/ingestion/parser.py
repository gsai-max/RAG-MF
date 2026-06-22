import logging
import json
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class GrowwParser:
    def __init__(self):
        pass

    def parse_html(self, html_content: str, url: str = "", fetch_date: str = None) -> dict | None:
        """
        Parse Groww HTML content and return a dictionary of normalized sections.
        """
        if not fetch_date:
            fetch_date = datetime.utcnow().strftime("%Y-%m-%d")

        soup = BeautifulSoup(html_content, "html.parser")
        
        # Try Next.js JSON extraction first
        data = self._parse_next_data(soup)
        if data:
            try:
                return self._normalize_next_data(data, url, fetch_date)
            except Exception as e:
                logger.error(f"Error normalizing NEXT_DATA JSON: {e}")
                # If normalization fails, fall through to fallback

        # Fallback to standard selector parsing
        logger.info("Falling back to BeautifulSoup selector parsing")
        return self._parse_with_selectors(soup, url, fetch_date)

    def _parse_next_data(self, soup: BeautifulSoup) -> dict | None:
        """Extract JSON data from __NEXT_DATA__ script tag."""
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if not script_tag or not script_tag.string:
            # Try to search scripts containing mfServerSideData
            for tag in soup.find_all("script"):
                if tag.string and "mfServerSideData" in tag.string:
                    try:
                        # Extract JSON structure from string if possible
                        # Usually it is standard __NEXT_DATA__ JSON, but let's be careful
                        start_idx = tag.string.find("{")
                        end_idx = tag.string.rfind("}")
                        if start_idx != -1 and end_idx != -1:
                            return json.loads(tag.string[start_idx:end_idx + 1])
                    except Exception:
                        pass
            return None
        
        try:
            return json.loads(script_tag.string)
        except Exception as e:
            logger.error(f"Failed to parse JSON inside __NEXT_DATA__ script: {e}")
            return None

    def _normalize_next_data(self, next_data: dict, url: str, fetch_date: str) -> dict:
        """Normalize JSON state from Next.js data props."""
        props = next_data.get("props", {})
        page_props = props.get("pageProps", {})
        mf_data = page_props.get("mfServerSideData", {})
        
        stp_details = mf_data.get("stp_details", {})
        amc_info = mf_data.get("amc_info", {})
        category_info = mf_data.get("category_info", {})
        
        return_stats_list = mf_data.get("return_stats", [])
        return_stats = return_stats_list[0] if return_stats_list else {}
        simple_return = mf_data.get("simple_return", {})

        # Extract manager list
        managers = []
        for mgr in mf_data.get("fund_manager_details", []):
            managers.append({
                "name": mgr.get("person_name", "N/A"),
                "education": mgr.get("education", "N/A"),
                "experience": mgr.get("experience", "N/A"),
                "date_from": mgr.get("date_from", "")[:10] if mgr.get("date_from") else "N/A"
            })

        # Extract holdings list (first 10 holdings)
        holdings = []
        for hld in mf_data.get("holdings", [])[:10]:
            holdings.append({
                "company_name": hld.get("company_name", "N/A"),
                "sector_name": hld.get("sector_name", "N/A"),
                "allocation_pct": hld.get("corpus_per", 0.0),
                "instrument": hld.get("instrument_name", "N/A")
            })

        # Format Returns dictionary
        returns = {
            "1M": return_stats.get("return1m") or simple_return.get("return1m"),
            "3M": return_stats.get("return3m") or simple_return.get("return3m"),
            "6M": return_stats.get("return6m") or simple_return.get("return6m"),
            "1Y": return_stats.get("return1y") or simple_return.get("return1y"),
            "3Y": return_stats.get("return3y") or simple_return.get("return3y"),
            "5Y": return_stats.get("return5y") or simple_return.get("return5y"),
            "10Y": return_stats.get("return10y") or simple_return.get("return10y"),
            "since_inception": return_stats.get("return_since_created") or simple_return.get("return_since_created")
        }

        # Normalize returns keys (some returns might be float or None)
        for key in list(returns.keys()):
            if isinstance(returns[key], (int, float)):
                returns[key] = f"{returns[key]:.2f}%"
            elif not returns[key]:
                returns[key] = "N/A"

        # Build normalized structure
        return {
            "slug": (mf_data.get("search_id") or url.split('/')[-1] if url else "").replace(":", "-"),
            "source_url": url,
            "last_updated": fetch_date,
            "sections": {
                "identity": {
                    "scheme_name": mf_data.get("scheme_name") or mf_data.get("fund_name") or "N/A",
                    "fund_house": mf_data.get("fund_house") or amc_info.get("name") or "N/A",
                    "isin": mf_data.get("isin") or "N/A",
                    "category": mf_data.get("category") or "N/A",
                    "sub_category": mf_data.get("sub_category") or "N/A",
                    "plan_type": mf_data.get("plan_type") or "Direct",
                    "option": mf_data.get("scheme_type") or "Growth",
                    "launch_date": mf_data.get("launch_date") or "N/A"
                },
                "performance_pricing": {
                    "nav": f"₹{mf_data.get('nav')}" if mf_data.get("nav") else "N/A",
                    "nav_date": mf_data.get("nav_date") or "N/A",
                    "returns": returns
                },
                "expense_ratio": {
                    "value": f"{mf_data.get('expense_ratio')}%" if mf_data.get("expense_ratio") else "N/A",
                    "definition": "A fee payable to a mutual fund house for managing your mutual fund investments."
                },
                "exit_load": {
                    "exit_load_text": mf_data.get("exit_load") or "N/A",
                    "entry_load": "0.00% (No Entry Load)"
                },
                "minimum_investment": {
                    "min_sip": f"₹{mf_data.get('min_sip_investment')}" if mf_data.get("min_sip_investment") else "N/A",
                    "min_lumpsum": f"₹{mf_data.get('min_investment_amount')}" if mf_data.get("min_investment_amount") else "N/A",
                    "sip_dates": stp_details.get("stp_dates") or []
                },
                "benchmark": {
                    "name": mf_data.get("benchmark_name") or "N/A",
                    "code": mf_data.get("benchmark") or "N/A"
                },
                "tax": {
                    "tax_impact": category_info.get("tax_impact") or "Factual taxation rules apply as per holding duration."
                },
                "fund_management": {
                    "managers": managers
                },
                "risk_metrics": {
                    "standard_deviation": f"{return_stats.get('standard_deviation')}" if return_stats.get("standard_deviation") else "N/A",
                    "sharpe_ratio": f"{return_stats.get('sharpe_ratio')}" if return_stats.get("sharpe_ratio") else "N/A",
                    "sortino_ratio": f"{return_stats.get('sortino_ratio')}" if return_stats.get("sortino_ratio") else "N/A",
                    "beta": f"{return_stats.get('beta')}" if return_stats.get("beta") else "N/A",
                    "alpha": f"{return_stats.get('alpha')}" if return_stats.get("alpha") else "N/A",
                    "riskometer_level": return_stats.get("risk") or mf_data.get("nfo_risk") or "N/A"
                },
                "portfolio_composition": {
                    "aum": f"₹{mf_data.get('aum'):,.2f} Cr" if isinstance(mf_data.get("aum"), (int, float)) else "N/A",
                    "top_holdings": holdings,
                    "portfolio_turnover": f"{mf_data.get('portfolio_turnover')}%" if mf_data.get("portfolio_turnover") else "N/A"
                },
                "investment_objective": {
                    "objective": mf_data.get("description") or "N/A"
                },
                "fund_house": {
                    "name": amc_info.get("name") or mf_data.get("fund_house") or "N/A",
                    "website": amc_info.get("vro_website") or "N/A",
                    "incorporation_date": amc_info.get("launch_date") or "N/A"
                }
            }
        }

    def _parse_with_selectors(self, soup: BeautifulSoup, url: str, fetch_date: str) -> dict:
        """BeautifulSoup-only fallback scraping heuristics."""
        title = soup.find("title")
        scheme_name = title.text.split("-")[0].strip() if title else "N/A"
        h1 = soup.find("h1")
        if h1:
            scheme_name = h1.text.strip()

        # Simple helpers to extract label/value divs
        def extract_val(label_text):
            elem = soup.find(string=lambda t: t and label_text in t)
            if elem:
                pp = elem.parent.parent
                divs = pp.find_all("div", recursive=False)
                if len(divs) >= 2:
                    return divs[1].text.strip()
            return "N/A"

        nav_text = extract_val("NAV:")
        min_sip = extract_val("Min. for SIP")
        aum_text = extract_val("Fund size (AUM)")
        expense_ratio = extract_val("Expense ratio")

        # Exclude currency symbol and extract clean string if possible
        return {
            "slug": (url.split('/')[-1] if url else "").replace(":", "-"),
            "source_url": url,
            "last_updated": fetch_date,
            "sections": {
                "identity": {
                    "scheme_name": scheme_name,
                    "fund_house": "ICICI Prudential Mutual Fund",
                    "isin": "N/A",
                    "category": "N/A",
                    "sub_category": "N/A",
                    "plan_type": "Direct",
                    "option": "Growth",
                    "launch_date": "N/A"
                },
                "performance_pricing": {
                    "nav": nav_text,
                    "nav_date": fetch_date,
                    "returns": {
                        "1M": "N/A", "3M": "N/A", "6M": "N/A", "1Y": "N/A", "3Y": "N/A", "5Y": "N/A", "since_inception": "N/A"
                    }
                },
                "expense_ratio": {
                    "value": expense_ratio,
                    "definition": "A fee payable to a mutual fund house for managing your mutual fund investments."
                },
                "exit_load": {
                    "exit_load_text": "N/A",
                    "entry_load": "0.00% (No Entry Load)"
                },
                "minimum_investment": {
                    "min_sip": min_sip,
                    "min_lumpsum": "N/A",
                    "sip_dates": []
                },
                "benchmark": {
                    "name": "N/A",
                    "code": "N/A"
                },
                "tax": {
                    "tax_impact": "Factual taxation rules apply as per holding duration."
                },
                "fund_management": {
                    "managers": []
                },
                "risk_metrics": {
                    "standard_deviation": "N/A",
                    "sharpe_ratio": "N/A",
                    "sortino_ratio": "N/A",
                    "beta": "N/A",
                    "alpha": "N/A",
                    "riskometer_level": "N/A"
                },
                "portfolio_composition": {
                    "aum": aum_text,
                    "top_holdings": [],
                    "portfolio_turnover": "N/A"
                },
                "investment_objective": {
                    "objective": "N/A"
                },
                "fund_house": {
                    "name": "ICICI Prudential Mutual Fund",
                    "website": "N/A",
                    "incorporation_date": "N/A"
                }
            }
        }
