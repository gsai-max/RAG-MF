import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field

from src.app.config import load_settings
from src.app.services.pii_scrubber import PIIScrubber
from src.app.services.classifier import QueryClassifier
from src.app.services.refusal_handler import RefusalHandler
from src.app.services.retriever import MFRetriever
from src.app.services.generator import LLMGenerator
from src.app.services.response_validator import ResponseValidator

# Configure logging using application settings
settings = load_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api_server")

# Define Custom Rate Limiter
class RateLimiter:
    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window
        self.history = {}  # ip -> list of timestamps

    def check(self, ip: str) -> bool:
        now = time.time()
        timestamps = self.history.get(ip, [])
        # Filter out timestamps older than the window
        timestamps = [t for t in timestamps if now - t < self.window]
        if len(timestamps) >= self.requests:
            return False
        timestamps.append(now)
        self.history[ip] = timestamps
        return True

class RateLimitDependency:
    def __init__(self):
        self.limiter = RateLimiter(
            requests=settings.rate_limit_requests,
            window=settings.rate_limit_window_seconds
        )

    def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        if not self.limiter.check(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )

rate_limiter_dep = RateLimitDependency()

# Lifespan context manager for resource setup/teardown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the retriever database connection on startup
    logger.info("Initializing MFRetriever database connection...")
    app.state.retriever = MFRetriever()
    yield
    logger.info("Shutting down API server...")

# Initialize FastAPI App
app = FastAPI(
    title="Mutual Fund FAQ Assistant (RAGMF) API",
    description="Stateless Facts-only Mutual Fund Q&A endpoint layer.",
    version="1.0.0",
    lifespan=lifespan
)

# Set up CORS middleware to support local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Request/Response Schemas
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user query text")
    selected_funds: list[str] = Field(default_factory=list, description="List of selected scheme slugs")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="The response text")
    citation_url: str = Field(..., description="The URL of the source page or SEBI/AMFI portal")
    last_updated: str = Field(..., description="The date the scheme data was last updated")
    is_refusal: bool = Field(..., description="True if the query violated guidelines and was refused")
    disclaimer: str = Field(..., description="Disclaimer text")

# Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Invalid request payload format. Please ensure you are sending a JSON payload with a 'message' string field.",
            "errors": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."}
    )

# Routes
@app.post("/api/chat", response_model=ChatResponse, dependencies=[Depends(rate_limiter_dep)])
async def chat(payload: ChatRequest, request: Request):
    """
    POST route orchestrating PII scrubbing, query intent classification, 
    vector retrieval, LLM generation, and formatting constraints verification.
    """
    query = payload.message.strip()
    logger.info(f"Received query: '{query}'")

    # 1. Scrub input message for PII
    scrubbed_query = PIIScrubber.scrub_text(query)
    
    # 2. Classify intent
    intent = QueryClassifier.classify(scrubbed_query)
    logger.info(f"Classified intent: '{intent}' (scrubbed query: '{scrubbed_query}')")

    # 3. Route response
    if intent != "factual":
        refusal = RefusalHandler.get_refusal(intent)
        return ChatResponse(
            answer=refusal["answer"],
            citation_url=refusal["citation_url"],
            last_updated=refusal["last_updated"],
            is_refusal=refusal["is_refusal"],
            disclaimer=refusal["disclaimer"]
        )

    try:
        # Retrieve chunks from database
        retriever = request.app.state.retriever
        chunks = retriever.retrieve_chunks(scrubbed_query, selected_funds=payload.selected_funds)
        logger.info(f"Retrieved {len(chunks)} context chunks from ChromaDB.")

        # Generate grounding answer
        gen_resp = LLMGenerator.generate(scrubbed_query, chunks)
        
        # Post-process output validation
        final_resp = ResponseValidator.validate_and_format(scrubbed_query, gen_resp, chunks)
        
        return ChatResponse(
            answer=final_resp["answer"],
            citation_url=final_resp["citation_url"],
            last_updated=final_resp["last_updated"],
            is_refusal=final_resp["is_refusal"],
            disclaimer=final_resp["disclaimer"]
        )
    except Exception as e:
        logger.error(f"Error processing factual RAG query: {e}", exc_info=True)
        return ChatResponse(
            answer="Factual details for this query could not be verified in the source text. Please check the scheme page directly.",
            citation_url="https://www.amfiindia.com/",
            last_updated="N/A",
            is_refusal=True,
            disclaimer="Facts-only. No investment advice."
        )

@app.get("/api/health")
async def health():
    """
    Standard health check endpoint.
    """
    return {
        "status": "ok",
        "env": settings.env
    }

@app.get("/api/funds")
async def get_funds(request: Request):
    """
    GET route to retrieve all mutual funds metadata registry details.
    """
    retriever = getattr(request.app.state, "retriever", None)
    if not retriever:
        from src.app.services.retriever import MFRetriever
        retriever = MFRetriever()

    funds = []
    for slug, meta in retriever.metadata_registry.items():
        funds.append({
            "slug": slug,
            "scheme_name": meta.get("scheme_name"),
            "category": meta.get("category", "N/A"),
            "source_url": meta.get("source_url"),
            "nav": meta.get("nav", "N/A"),
            "nav_date": meta.get("nav_date", "N/A")
        })
    return sorted(funds, key=lambda x: x["scheme_name"])

