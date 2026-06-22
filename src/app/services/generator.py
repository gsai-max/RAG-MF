import os
import requests
import logging
import re
from typing import Optional

from src.app.config import load_settings

logger = logging.getLogger(__name__)

class LLMGenerator:
    """
    LLM generation connector executing RAG context-grounded queries.
    Utilizes REST endpoints for Gemini or Groq, with a smart Mock fallback 
    for offline/keyless local testing environments.
    """

    SYSTEM_PROMPT = (
        "You are an objective, facts-only Q&A assistant for ICICI Prudential mutual fund schemes. "
        "Your responses must strictly contain only factual information from the provided context. "
        "Do not provide investment advice, opinions, recommendations, or speculative projections. "
        "Enforce strict brevity: write at most 3 sentences in your answer. "
        "Include no more than one URL in your answer. "
        "If the context is insufficient or does not contain the answer, state: "
        "'I cannot find the answer in the source pages.' and point the user to the scheme page."
    )

    @classmethod
    def generate(cls, query: str, chunks: list[dict]) -> dict:
        """
        Generate a RAG grounded response for the query using the context chunks.
        """
        disclaimer = "Facts-only. No investment advice."
        
        # 1. Handle empty context scenario
        if not chunks:
            return {
                "answer": "I cannot find the answer in the source pages.",
                "citation_url": "https://www.amfiindia.com/",
                "last_updated": "N/A",
                "is_refusal": True,
                "disclaimer": disclaimer
            }

        # 2. Extract metadata from all chunks (deduplicated while preserving order)
        unique_urls = []
        for c in chunks:
            url = c.get("source_url")
            if url and url not in unique_urls:
                unique_urls.append(url)
        citation_url = ",".join(unique_urls) if unique_urls else "https://groww.in/"

        unique_dates = []
        for c in chunks:
            dt = c.get("last_updated")
            if dt and dt not in unique_dates:
                unique_dates.append(dt)
        last_updated = ", ".join(unique_dates) if unique_dates else "N/A"

        # 3. Load configurations & check for API keys
        settings = load_settings()
        gemini_key = settings.gemini_api_key
        groq_key = settings.groq_api_key

        # 4. Prompt Assembly
        context_text = "\n\n".join([c["text"] for c in chunks])
        prompt = (
            f"System Instructions:\n{cls.SYSTEM_PROMPT}\n\n"
            f"Context Chunks:\n{context_text}\n\n"
            f"User Question: {query}\n"
            f"Answer:"
        )

        # 5. Call LLM (Gemini or Groq) if key is present
        if gemini_key:
            logger.info("Calling Gemini REST API...")
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.0,
                        "maxOutputTokens": 250
                    }
                }
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()
                text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return {
                    "answer": text,
                    "citation_url": citation_url,
                    "last_updated": last_updated,
                    "is_refusal": False,
                    "disclaimer": disclaimer
                }
            except Exception as e:
                logger.error(f"Gemini API request failed: {e}. Falling back to mock generator.")

        elif groq_key:
            logger.info("Calling Groq REST API...")
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 250
                }
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                text = response.json()["choices"][0]["message"]["content"].strip()
                return {
                    "answer": text,
                    "citation_url": citation_url,
                    "last_updated": last_updated,
                    "is_refusal": False,
                    "disclaimer": disclaimer
                }
            except Exception as e:
                logger.error(f"Groq API request failed: {e}. Falling back to mock generator.")

        # 6. Smart Mock Fallback (Dry Run/Local mode)
        logger.info("Executing Smart Mock generator (no API key detected).")
        query_lower = query.lower()
        
        # Heuristic retrieval search over context chunks
        matched_text = ""
        
        if "expense ratio" in query_lower:
            matched_text = cls._find_chunk_text_by_section(chunks, "expense_ratio")
        elif "exit load" in query_lower or "entry load" in query_lower:
            matched_text = cls._find_chunk_text_by_section(chunks, "exit_load")
        elif "manager" in query_lower or "manages" in query_lower or "managed by" in query_lower:
            matched_text = cls._find_chunk_text_by_section(chunks, "fund_management")
        elif "holding" in query_lower or "holdings" in query_lower or "portfolio" in query_lower:
            matched_text = cls._find_chunk_text_by_section(chunks, "portfolio_composition")
        elif "nav" in query_lower or "net asset value" in query_lower:
            matched_text = cls._find_chunk_text_by_section(chunks, "performance_pricing")
            
        if not matched_text:
            # Fallback to the top chunk's first sentences
            matched_text = primary_chunk["text"]

        # Limit to 3 sentences
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', matched_text) if s.strip()]
        answer = " ".join(sentences[:3])

        return {
            "answer": answer,
            "citation_url": citation_url,
            "last_updated": last_updated,
            "is_refusal": False,
            "disclaimer": disclaimer
        }

    @staticmethod
    def _find_chunk_text_by_section(chunks: list[dict], section_name: str) -> str:
        """Helper to find the text of all chunks matching a section name, combined."""
        matched_texts = []
        for c in chunks:
            if c.get("section") == section_name:
                matched_texts.append(c["text"])
        return " ".join(matched_texts) if matched_texts else ""
