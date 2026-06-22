import re
from typing import Literal

QueryClass = Literal["factual", "advisory", "comparison", "speculative", "out_of_scope"]

class QueryClassifier:
    """
    Classifier to identify the intent of the user query.
    Ensures compliance by filtering out advisory, comparison, speculative,
    and out-of-scope queries before retrieval.
    """
    
    # Patterns for Advisory
    ADVISORY_PATTERNS = [
        re.compile(r'\bshould\s+(?:i|we)\b', re.IGNORECASE),
        re.compile(r'\bgood\s+fund\b', re.IGNORECASE),
        re.compile(r'\bbest\s+fund\b', re.IGNORECASE),
        re.compile(r'\brecommend(?:ation)?s?\b', re.IGNORECASE),
        re.compile(r'\badvice\b', re.IGNORECASE),
        re.compile(r'\badvise\b', re.IGNORECASE),
        re.compile(r'\bopinion\b', re.IGNORECASE),
        re.compile(r'\bsuggest(?:ion)?s?\b', re.IGNORECASE),
        re.compile(r'\bwhere\s+.*?\binvest\b', re.IGNORECASE),
        re.compile(r'\bbuy\s+(?:or|and)\s+sell\b', re.IGNORECASE),
        re.compile(r'\bwhether\s+to\s+buy\b', re.IGNORECASE),
        re.compile(r'\bis\s+.*?\bgood\s+(?:fund|investment|choice|to\s+buy)\b', re.IGNORECASE),
        re.compile(r'\bmake\s+sense\s+(?:to|for)\b', re.IGNORECASE),
        re.compile(r'\bworth\s+(?:buying|investing|to\s+buy)\b', re.IGNORECASE),
        re.compile(r'\bsuitable\s+for\b', re.IGNORECASE),
        re.compile(r'\bfit\s+for\b', re.IGNORECASE),
        re.compile(r'\bwould\s+.*?\b(?:buy|invest)\b', re.IGNORECASE),
        re.compile(r'\bshould\s+.*?\b(?:buy|invest)\b', re.IGNORECASE),
        re.compile(r'\bcan\s+i\s+buy\b', re.IGNORECASE),
    ]
    
    # Patterns for Comparison
    COMPARISON_PATTERNS = [
        re.compile(r'\bvs\b', re.IGNORECASE),
        re.compile(r'\bversus\b', re.IGNORECASE),
        re.compile(r'\bcompare\b', re.IGNORECASE),
        re.compile(r'\bbetter\s+than\b', re.IGNORECASE),
        re.compile(r'\bwhich\s+is\s+better\b', re.IGNORECASE),
        re.compile(r'\bwhich\s+(?:one|fund|scheme)\s+is\s+better\b', re.IGNORECASE),
        re.compile(r'\bcap\s+vs\s+\b', re.IGNORECASE),
    ]
    
    # Patterns for Speculative / Performance-seeking Calculations
    SPECULATIVE_PATTERNS = [
        re.compile(r'\bexpected\s+returns?\b', re.IGNORECASE),
        re.compile(r'\bprojected\s+returns?\b', re.IGNORECASE),
        re.compile(r'\bfuture\s+returns?\b', re.IGNORECASE),
        re.compile(r'\bwhat\s+returns\s+(?:will|can)\s+i\s+get\b', re.IGNORECASE),
        re.compile(r'\bcalculat(?:or|e)\b', re.IGNORECASE),
        re.compile(r'\bsip\s+calculator\b', re.IGNORECASE),
        re.compile(r'\blumpsum\s+calculator\b', re.IGNORECASE),
        re.compile(r'\bswp\s+calculator\b', re.IGNORECASE),
        re.compile(r'\bgoal-based\b', re.IGNORECASE),
    ]
    
    # Patterns for competitor AMCs
    COMPETITOR_AMCS = [
        r'\bhdfc\b', r'\bsbi\b', r'\baxis\b', r'\bnippon\b', r'\btata\b', 
        r'\bmirae\b', r'\bkotak\b', r'\bquant\b', r'\bparag\s+parikh\b', 
        r'\bppfas\b', r'\buti\b', r'\baditya\s+birla\b', r'\babsl\b', 
        r'\bdsp\b', r'\bmotilal\b', r'\bhsbc\b', r'\bcanara\b', r'\brobeco\b', 
        r'\binvesco\b', r'\bsundaram\b', r'\bbandhan\b', r'\bidfc\b', 
        r'\bfranklin\b'
    ]
    COMPETITOR_PATTERNS = [re.compile(p, re.IGNORECASE) for p in COMPETITOR_AMCS]
    
    # Core mutual fund keyword tokens to verify if query is about mutual funds at all
    FUND_CONTEXT_KEYWORDS = [
        "fund", "nav", "scheme", "sip", "lumpsum", "returns", "expense", "exit load", 
        "manager", "aum", "holdings", "portfolio", "tax", "benchmark", "risk", 
        "icici", "prudential", "growth", "dividend", "idcw", "equity", "debt", 
        "hybrid", "large cap", "mid cap", "small cap", "elss", "mutual", "invest"
    ]
    
    @classmethod
    def classify(cls, query: str) -> QueryClass:
        """
        Classify the query into one of the QueryClass intents.
        """
        query_clean = query.strip().lower()
        if not query_clean:
            return "out_of_scope"
            
        # 1. Check for Competitor AMC first (Out of Scope takes precedence)
        for pattern in cls.COMPETITOR_PATTERNS:
            if pattern.search(query_clean):
                return "out_of_scope"
                
        # 2. Check for Advisory
        for pattern in cls.ADVISORY_PATTERNS:
            if pattern.search(query_clean):
                return "advisory"
                
        # 3. Check for Comparison
        for pattern in cls.COMPARISON_PATTERNS:
            if pattern.search(query_clean):
                return "comparison"
                
        # 4. Check for Speculative / Performance Calculations
        for pattern in cls.SPECULATIVE_PATTERNS:
            if pattern.search(query_clean):
                return "speculative"
                
        # 5. Check if query is completely off-topic (unrelated to mutual funds)
        has_context = any(keyword in query_clean for keyword in cls.FUND_CONTEXT_KEYWORDS)
        if not has_context:
            return "out_of_scope"
            
        # Default fallback to factual if it has context and doesn't match refusal triggers
        return "factual"

