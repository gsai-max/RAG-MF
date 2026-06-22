import os
import json
import logging
from pathlib import Path
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from src.app.config import load_settings

logger = logging.getLogger(__name__)

# Constants
COLLECTION_NAME = "mutual_funds"
METADATA_INDEX_FILE = "scheme_metadata.json"

def get_embedding_function():
    """Get BGE-small embedding function."""
    logger.info("Initializing BGE-small embedding function...")
    return SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-small-en-v1.5")

def get_chroma_client(db_path: Path | str = None):
    """Create a persistent ChromaDB client."""
    if db_path is None:
        settings = load_settings()
        db_path = settings.chroma_db_path
        
    db_path = Path(db_path)
    db_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Connecting to persistent ChromaDB client at: {db_path}")
    return chromadb.PersistentClient(path=str(db_path))

def get_mf_collection(client, embedding_fn=None):
    """Retrieve or create the mutual funds collection."""
    if embedding_fn is None:
        embedding_fn = get_embedding_function()
        
    logger.info(f"Retrieving or creating Chroma collection: {COLLECTION_NAME}")
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity as per architecture plan
    )

def index_chunks(chunks: list[dict], db_path: Path | str = None):
    """
    Insert or update chunks into the Chroma collection.
    """
    if not chunks:
        logger.warning("No chunks provided for indexing.")
        return
        
    client = get_chroma_client(db_path)
    collection = get_mf_collection(client)
    
    ids = []
    documents = []
    metadatas = []
    
    for chunk in chunks:
        ids.append(chunk["id"])
        documents.append(chunk["text"])
        metadatas.append(chunk["metadata"])
        
    logger.info(f"Upserting {len(chunks)} chunks into Chroma...")
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    logger.info("Chroma indexing complete.")

def update_scheme_metadata_index(processed_data: dict, db_path: Path | str = None):
    """
    Update the metadata lookup registry file.
    """
    if db_path is None:
        settings = load_settings()
        db_path = settings.chroma_db_path
        
    db_path = Path(db_path)
    db_path.mkdir(parents=True, exist_ok=True)
    meta_path = db_path / METADATA_INDEX_FILE
    
    # Load existing metadata
    meta_index = {}
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta_index = json.load(f)
        except Exception as e:
            logger.error(f"Error reading metadata index file: {e}")
            
    slug = processed_data.get("slug")
    sections = processed_data.get("sections", {})
    identity = sections.get("identity", {})
    performance = sections.get("performance_pricing", {})
    
    # Update scheme data entry
    meta_index[slug] = {
        "slug": slug,
        "scheme_name": identity.get("scheme_name", slug),
        "category": f"{identity.get('category', 'N/A')} — {identity.get('sub_category', 'N/A')}",
        "source_url": processed_data.get("source_url"),
        "last_fetched_at": processed_data.get("last_updated"),
        "nav": performance.get("nav", "N/A"),
        "nav_date": performance.get("nav_date", "N/A")
    }
    
    # Write back to file
    try:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_index, f, indent=2, ensure_ascii=False)
        logger.info(f"Updated metadata index registry file at: {meta_path}")
    except Exception as e:
        logger.error(f"Failed to write metadata index registry: {e}")
