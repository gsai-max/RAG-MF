import os
import json
import re
import logging
from pathlib import Path

from src.app.config import load_settings
from src.app.ingestion.index import get_chroma_client, get_mf_collection

logger = logging.getLogger(__name__)

class MFRetriever:
    """
    Service responsible for scheme name resolution and retrieving 
    grounding chunks from ChromaDB with optional metadata filtering.
    """
    
    STOP_WORDS = {
        "icici", "prudential", "mutual", "fund", "direct", "plan", "growth", 
        "regular", "etf", "fof", "index", "saving", "savings", "tax", "saver", 
        "option", "type", "theme", "hybrid", "equity", "debt", "liquid", 
        "opportunities", "opportunity", "strategy", "fund-direct-growth",
        "what", "is", "a", "an", "the", "on", "of", "to", "in", "and", "or", 
        "who", "whose", "which", "where", "when", "why", "that", "this", 
        "these", "those", "how", "for", "with", "about", "at", "by"
    }

    def __init__(self, db_path: Path | str = None):
        from src.app.config import get_active_index_path
        self.db_path = Path(db_path or get_active_index_path())
        self.metadata_index_path = self.db_path / "scheme_metadata.json"
        self.metadata_registry = self._load_metadata_registry()
        
        # Connect to Chroma
        self.chroma_client = get_chroma_client(self.db_path)
        self.collection = get_mf_collection(self.chroma_client)

    def _load_metadata_registry(self) -> dict:
        """Load the scheme metadata index file if it exists."""
        if self.metadata_index_path.exists():
            try:
                with open(self.metadata_index_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load scheme metadata index: {e}")
        return {}

    def _clean_text(self, text: str) -> str:
        """Lowercase and remove non-alphanumeric characters."""
        return re.sub(r'[^a-z0-9\s-]', '', text.strip().lower())

    def resolve_scheme(self, query: str) -> str | None:
        """
        Fuzzy matches the query string to a scheme slug in the registry.
        Uses keyword token intersection and scores candidate schemes.
        """
        if not self.metadata_registry:
            return None

        query_clean = self._clean_text(query)
        query_words = set(query_clean.replace("-", " ").split())
        query_words = query_words - self.STOP_WORDS

        if not query_words:
            return None

        best_slug = None
        best_score = 0.0

        for slug, meta in self.metadata_registry.items():
            scheme_name = meta.get("scheme_name", "")
            scheme_clean = self._clean_text(scheme_name)
            
            # Extract distinctive words from slug & scheme name
            scheme_words = set(scheme_clean.replace("-", " ").split())
            slug_words = set(slug.replace("-", " ").split())
            
            distinct_words = (scheme_words | slug_words) - self.STOP_WORDS
            
            if not distinct_words:
                continue

            # Calculate intersection
            intersection = query_words & distinct_words
            score = len(intersection) / len(distinct_words)

            # Boost if a full distinctive word is a direct substring match
            # E.g. "bluechip" matches "icici-prudential-bluechip-fund-direct-growth"
            for word in query_words:
                if len(word) > 2 and (word in slug or word in scheme_clean):
                    score += 0.2

            if score > best_score:
                best_score = score
                best_slug = slug

        # Confident threshold matching
        if best_score >= 0.35:
            logger.info(f"Resolved query to scheme: {best_slug} (score: {best_score:.2f})")
            return best_slug

        logger.info(f"Could not confidently resolve query to a specific scheme. Best score: {best_score:.2f}")
        return None

    def retrieve_chunks(self, query: str, limit: int = 3, selected_funds: list[str] = None) -> list[dict]:
        """
        Retrieves top-k relevant chunks from ChromaDB.
        Filters by selected funds if provided, otherwise by resolved scheme slug if one is detected.
        """
        # Dynamic database path swap check
        from src.app.config import get_active_index_path
        current_active_path = Path(get_active_index_path())
        if current_active_path != self.db_path:
            logger.info(f"Database swap detected. Reloading connection from {self.db_path} to {current_active_path}...")
            self.db_path = current_active_path
            self.metadata_index_path = self.db_path / "scheme_metadata.json"
            self.metadata_registry = self._load_metadata_registry()
            self.chroma_client = get_chroma_client(self.db_path)
            self.collection = get_mf_collection(self.chroma_client)

        cleaned_funds = []
        if selected_funds:
            cleaned_funds = list(dict.fromkeys(s for s in selected_funds if s))
            
        where_filters = []
        if cleaned_funds:
            resolved_slug = self.resolve_scheme(query)
            if resolved_slug and resolved_slug in cleaned_funds:
                where_filters = [{"slug": resolved_slug}]
            else:
                where_filters = [{"slug": slug} for slug in cleaned_funds]
        else:
            resolved_slug = self.resolve_scheme(query)
            if resolved_slug:
                where_filters = [{"slug": resolved_slug}]
            else:
                where_filters = [None]

        chunks = []
        for where_filter in where_filters:
            logger.info(f"Querying ChromaDB for: '{query}' with filter: {where_filter}")
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit,
                    where=where_filter
                )
                chunks.extend(self._parse_query_results(results))
            except Exception as e:
                logger.error(f"Error querying ChromaDB with filter {where_filter}: {e}")
                
        return chunks

    def _parse_query_results(self, results: dict) -> list[dict]:
        """Helper to parse raw ChromaDB query results into standardized chunk dicts."""
        chunks = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metadatas = results["metadatas"][0]
            ids = results["ids"][0]
            distances = results.get("distances", [[]])[0] if results.get("distances") else [0.0] * len(docs)
            
            for doc, meta, cid, dist in zip(docs, metadatas, ids, distances):
                similarity = 1.0 - dist
                if similarity < 0.48:
                    logger.warning(f"Chunk {cid} filtered out due to low similarity score: {similarity:.4f} (distance: {dist:.4f})")
                    continue
                chunks.append({
                    "id": cid,
                    "text": doc,
                    "slug": meta.get("slug"),
                    "scheme_name": meta.get("scheme_name"),
                    "section": meta.get("section"),
                    "source_url": meta.get("source_url"),
                    "last_updated": meta.get("last_updated")
                })
        return chunks
