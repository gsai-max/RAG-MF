import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import BaseModel
import yaml

# Resolve root path of the project (assuming config.py is at src/app/config.py)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    env: str = "dev"
    port: int = 8000
    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    chroma_db_path: str = "data/index/"
    log_level: str = "INFO"
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    scheduler_hour: int = 10
    scheduler_minute: int = 0

    model_config = {
        "env_file": str(ROOT_DIR / ".env"),
        "extra": "ignore"
    }

class SchemeConfig(BaseModel):
    slug: str
    scheme_name: str
    source_url: str

class CorpusConfig(BaseModel):
    schemes: list[SchemeConfig]

def load_settings() -> Settings:
    """Load settings from environment variables and .env file."""
    return Settings()

def load_corpus(corpus_path: Path | None = None) -> list[SchemeConfig]:
    """Load and validate the schemes corpus from corpus.yaml."""
    if corpus_path is None:
        corpus_path = ROOT_DIR / "config" / "corpus.yaml"
    
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus configuration file not found at: {corpus_path}")
        
    with open(corpus_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    corpus = CorpusConfig.model_validate(data)
    return corpus.schemes

def get_active_index_path() -> Path:
    """
    Get the path to the currently active index directory.
    Uses data/active_index.txt if it exists, otherwise falls back to data/index.
    """
    active_txt = ROOT_DIR / "data" / "active_index.txt"
    if active_txt.exists():
        try:
            with open(active_txt, "r", encoding="utf-8") as f:
                name = f.read().strip()
                if name in ["index", "index_A", "index_B"]:
                    return ROOT_DIR / "data" / name
        except Exception:
            pass
    
    # Fallback to data/index if it exists, otherwise data/index_A
    index_path = ROOT_DIR / "data" / "index"
    if index_path.exists():
        return index_path
    return ROOT_DIR / "data" / "index_A"

def set_active_index_name(name: str):
    """
    Set the active index name ('index_A' or 'index_B') in the active_index.txt pointer file.
    """
    if name not in ["index", "index_A", "index_B"]:
        raise ValueError("Invalid index directory name. Must be 'index', 'index_A', or 'index_B'.")
    active_txt = ROOT_DIR / "data" / "active_index.txt"
    active_txt.parent.mkdir(parents=True, exist_ok=True)
    with open(active_txt, "w", encoding="utf-8") as f:
        f.write(name)

