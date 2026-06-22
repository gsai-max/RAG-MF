import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
import json

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import shutil
from src.app.config import load_settings, load_corpus, get_active_index_path, set_active_index_name, ROOT_DIR
from src.app.ingestion.scraper import GrowwScraper
from src.app.ingestion.parser import GrowwParser
from src.app.ingestion.chunk import generate_chunks_from_processed_json
from src.app.ingestion.index import index_chunks, update_scheme_metadata_index

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("ingestion_runner")

def run_ingestion(limit: int = None, force: bool = False, db_path: Path = None):
    lock_file = ROOT_DIR / "crawler.lock"
    if lock_file.exists():
        logger.error(f"Ingestion lock file '{lock_file}' is present. Another instance might be running. Aborting.")
        return False
    try:
        with open(lock_file, "w", encoding="utf-8") as lf:
            lf.write(str(os.getpid()))
        logger.info(f"Created lock file: {lock_file}")
        return _run_ingestion_internal(limit, force, db_path)
    finally:
        if lock_file.exists():
            try:
                lock_file.unlink()
                logger.info(f"Removed lock file: {lock_file}")
            except Exception as e:
                logger.error(f"Failed to remove lock file: {e}")

def _run_ingestion_internal(limit: int = None, force: bool = False, db_path: Path = None):
    """
    Orchestrate fetching, parsing, caching, chunking, and indexing of Groww pages.
    """
    settings = load_settings()
    
    # 1. Load corpus
    try:
        schemes = load_corpus()
    except Exception as e:
        logger.error(f"Failed to load corpus.yaml: {e}")
        return False

    if limit:
        logger.info(f"Limiting ingestion to the first {limit} schemes")
        schemes = schemes[:limit]

    logger.info(f"Starting ingestion run for {len(schemes)} schemes")

    # Determine build directory target and swap parameters
    is_swap_run = False
    if db_path is None:
        active_path = get_active_index_path()
        if active_path.name == "index_B":
            db_path = active_path.parent / "index_A"
        else:
            db_path = active_path.parent / "index_B"
        is_swap_run = True
        logger.info(f"Swap run detected. Active index directory: '{active_path.name}'. Target build directory: '{db_path.name}'.")
    else:
        db_path = Path(db_path)
        logger.info(f"Target build directory manually specified: '{db_path}'")

    # Clean target directory to prevent mixing stale chunks
    if db_path.exists():
        logger.info(f"Cleaning existing target directory: {db_path}")
        try:
            shutil.rmtree(db_path)
        except Exception as e:
            logger.warning(f"Failed to delete target directory: {e}. Retrying file-by-file...")
            for item in db_path.glob("*"):
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception:
                    pass
    db_path.mkdir(parents=True, exist_ok=True)

    # Paths
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Initialize modules
    scraper = GrowwScraper(raw_data_dir=raw_dir)
    parser = GrowwParser()

    stats = {
        "total": len(schemes),
        "fetch_success": 0,
        "fetch_failed": 0,
        "parse_success": 0,
        "parse_failed": 0
    }

    all_chunks = []

    for idx, scheme in enumerate(schemes):
        slug = scheme.slug
        url = scheme.source_url
        logger.info(f"[{idx+1}/{len(schemes)}] Processing: {slug}")

        # Fetch HTML content
        # Get metadata fetch time if cached, otherwise use now
        meta_path = raw_dir / f"{slug}.metadata.json"
        fetch_time = None
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    fetch_time = meta.get("fetched_at")
            except Exception:
                pass
        
        if not fetch_time:
            fetch_time = datetime.utcnow().isoformat() + "Z"

        html_content = scraper.fetch_page(url, slug, force=force)
        if not html_content:
            logger.error(f"Failed to fetch HTML content for: {slug}")
            stats["fetch_failed"] += 1
            continue
        
        stats["fetch_success"] += 1

        # Parse HTML content
        # Extract date string for last_updated footer
        date_str = fetch_time[:10]  # YYYY-MM-DD
        parsed_data = parser.parse_html(html_content, url=url, fetch_date=date_str)
        if not parsed_data:
            logger.error(f"Failed to parse content for: {slug}")
            stats["parse_failed"] += 1
            continue

        # SELECTOR FAIL-SAFE CHECK
        perf_sec = parsed_data.get("sections", {}).get("performance_pricing", {})
        exp_sec = parsed_data.get("sections", {}).get("expense_ratio", {})
        
        parsed_nav = perf_sec.get("nav", "N/A")
        parsed_exp = exp_sec.get("value", "N/A")
        
        if parsed_nav == "N/A" and parsed_exp == "N/A":
            logger.warning(f"SELECTOR FAIL-SAFE TRIGGERED: Key fields (NAV, expense ratio) are empty/N/A for '{slug}'. Checking cached processed JSON.")
            cached_path = processed_dir / f"{slug}.json"
            if cached_path.exists():
                try:
                    with open(cached_path, "r", encoding="utf-8") as f:
                        parsed_data = json.load(f)
                    logger.info(f"Successfully fell back to cached processed data from {cached_path}")
                except Exception as cache_err:
                    logger.error(f"Failed to load cached processed data: {cache_err}. Skipping this scheme.")
                    stats["parse_failed"] += 1
                    continue
            else:
                logger.error(f"No previously cached processed JSON file found for '{slug}'. Skipping this scheme.")
                stats["parse_failed"] += 1
                continue

        stats["parse_success"] += 1

        # Save processed JSON
        out_path = processed_dir / f"{slug}.json"
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved processed data to: {out_path}")
            
            # Generate chunks
            logger.info(f"Generating semantic chunks for: {slug}")
            chunks = generate_chunks_from_processed_json(parsed_data)
            all_chunks.extend(chunks)
            logger.info(f"Generated {len(chunks)} chunks.")
            
            # Update metadata lookup index in the target build directory
            update_scheme_metadata_index(parsed_data, db_path=db_path)

        except Exception as e:
            logger.error(f"Failed to save processed JSON or generate chunks for {slug}: {e}")
            stats["parse_failed"] += 1

    # Bulk index all chunks into ChromaDB
    if all_chunks:
        try:
            # Deduplicate chunks by ID to prevent duplicate chunk ID crashes
            unique_chunks = {c["id"]: c for c in all_chunks}
            all_chunks = list(unique_chunks.values())
            logger.info(f"Starting bulk indexing of {len(all_chunks)} unique chunks into ChromaDB at: {db_path} ...")
            index_chunks(all_chunks, db_path=db_path)
            logger.info("ChromaDB bulk indexing completed successfully.")
        except Exception as e:
            logger.error(f"Error during ChromaDB indexing: {e}")
            return False

    success = stats["parse_success"] == len(schemes)
    
    if success and is_swap_run:
        # Atomic swap active database pointer to the new active directory
        set_active_index_name(db_path.name)
        logger.info(f"Successfully swapped active index pointer to: {db_path.name}")

    logger.info(
        f"Ingestion run completed. Stats: "
        f"Total: {stats['total']}, "
        f"Fetch Success: {stats['fetch_success']}, Ingestion Failed: {stats['fetch_failed']}, "
        f"Parse Success: {stats['parse_success']}, Parse Failed: {stats['parse_failed']}, "
        f"Atomic Swap: {is_swap_run and success}"
    )
    
    return success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mutual Fund FAQ Ingestion Pipeline")
    parser.add_argument("--limit", type=int, help="Limit number of schemes to process for debugging")
    parser.add_argument("--force", action="store_true", help="Force fetching fresh content instead of using cache")
    args = parser.parse_args()

    success = run_ingestion(limit=args.limit, force=args.force)
    sys.exit(0 if success else 1)
