import re
import logging
from typing import Set

from src.app.config import load_corpus
from src.app.services.refusal_handler import RefusalHandler

logger = logging.getLogger(__name__)

class ResponseValidator:
    """
    Validator to enforce strict output compliance including sentence counts, 
    citation URLs, advisory leakage check, and factual numeric grounding.
    """
    
    # Advisory leakage tokens to check in output
    ADVISORY_TOKENS = {
        "should", "recommend", "opinion", "advice", "advise", "suggest", 
        "buy", "sell", "hold", "invest"
    }

    _allowed_urls_cache: Set[str] = None

    @classmethod
    def _get_allowed_urls(cls) -> Set[str]:
        """Lazy load and cache the allowed corpus URLs."""
        if cls._allowed_urls_cache is None:
            try:
                schemes = load_corpus()
                cls._allowed_urls_cache = {s.source_url for s in schemes}
            except Exception as e:
                logger.error(f"Failed to load corpus URLs for validation: {e}")
                cls._allowed_urls_cache = set()
        return cls._allowed_urls_cache

    @classmethod
    def validate_and_format(cls, query: str, response: dict, chunks: list[dict]) -> dict:
        """
        Validate and format response dictionary.
        Returns a validated response payload.
        """
        disclaimer = "Facts-only. No investment advice."
        last_updated = response.get("last_updated", "N/A")
        
        # 1. Skip validation if it's already classified as a refusal
        if response.get("is_refusal"):
            return response

        # 2. Citation URL Allowlist check
        citation_url = response.get("citation_url")
        allowed_urls = cls._get_allowed_urls()
        # Also include common refusal URLs in allowed_urls
        extended_allowed = allowed_urls | {
            "https://www.amfiindia.com/",
            "https://investor.sebi.gov.in/",
            "https://www.amfiindia.com/investor/knowledge-center-info?faqs"
        }
        
        valid_citations = []
        if citation_url:
            for url in citation_url.split(","):
                url_clean = url.strip()
                if url_clean in extended_allowed:
                    valid_citations.append(url_clean)
        
        if not valid_citations:
            if chunks:
                # Fallback to unique source URLs from chunks
                unique_urls = []
                for c in chunks:
                    u = c.get("source_url")
                    if u and u not in unique_urls:
                        unique_urls.append(u)
                citation_url = ",".join(unique_urls)
            else:
                citation_url = "https://www.amfiindia.com/"
            response["citation_url"] = citation_url
        else:
            response["citation_url"] = ",".join(valid_citations)

        answer = response.get("answer", "").strip()
        if not answer:
            return {
                "answer": "I cannot find the answer in the source pages.",
                "citation_url": citation_url,
                "last_updated": last_updated,
                "is_refusal": True,
                "disclaimer": disclaimer
            }

        # 3. Advisory Leakage Check
        answer_lower = answer.lower()
        words = set(re.findall(r'\b[a-z]+\b', answer_lower))
        if words & cls.ADVISORY_TOKENS:
            logger.warning("Advisory leakage detected in generated response. Routing to refusal handler.")
            return RefusalHandler.get_refusal("advisory", last_updated=last_updated)

        # 4. Sentence Truncation Check (Maximum 3 sentences)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', answer) if s.strip()]
        if len(sentences) > 3:
            logger.warning(f"Response length exceeds 3 sentences ({len(sentences)} detected). Truncating.")
            answer = " ".join(sentences[:3])
            response["answer"] = answer

        # 5. Factual Grounding check on numeric/percentage metrics
        # Regex to match percentages (e.g. 1.05%, 12%), currencies (e.g. ₹13,358.29, ₹500), and decimals (e.g. 18.85)
        metrics = []
        metrics.extend(re.findall(r'\b\d+(?:\.\d+)?%\b', answer))
        metrics.extend(re.findall(r'₹\d+(?:,\d+)*(?:\.\d+)?\b', answer))
        metrics.extend(re.findall(r'\b\d+\.\d+\b', answer))
        
        if chunks:
            context_text = "\n\n".join([c["text"] for c in chunks])
            for metric in metrics:
                # Check if the exact numeric token exists in the context chunks
                if metric not in context_text:
                    logger.warning(f"Grounding check failed: metric '{metric}' not found in retrieved context.")
                    return {
                        "answer": "Factual details for this query could not be verified in the source text. Please check the scheme page directly.",
                        "citation_url": citation_url,
                        "last_updated": last_updated,
                        "is_refusal": True,
                        "disclaimer": disclaimer
                    }

        return response
