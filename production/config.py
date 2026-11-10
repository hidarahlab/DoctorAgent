"""Central configuration - every tunable parameter of the system lives here."""
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")  # puts ANTHROPIC_API_KEY into the environment

# ---------------------------------------------------------------- paths
DATA_DIR = ROOT / "data"
PDF_PATH = DATA_DIR / "medical_book.pdf"
CHUNKS_PATH = DATA_DIR / "chunks.json"
INDEX_DIR = ROOT / "index"

# ---------------------------------------------------------------- ingestion
FIRST_CONTENT_PAGE = 13  # 0-based; pages before this are front matter
CHUNK_CHARS = 1200       # target chunk size (~300 tokens)
OVERLAP_CHARS = 200      # overlap between consecutive sub-chunks of one section

# ---------------------------------------------------------------- retrieval
EMBED_MODEL = "BAAI/bge-small-en-v1.5"  # 384-dim, runs locally on CPU via ONNX (free)
EMBED_CACHE = ROOT / ".models"           # downloaded embedding model lives here
TOP_K = 5                # chunks handed to the RAG agent
CANDIDATES = 30          # candidates taken from each retriever before fusion
RRF_K = 60               # Reciprocal Rank Fusion constant

# ---------------------------------------------------------------- LLMs
# "Cost-saving mix": cheap fast model for routing/summarising,
# strongest model where medical accuracy matters (answering + fact-checking).
MODELS = {
    "planner": "claude-haiku-5-5",
    "rag": "claude-opus-5-5",
    "evaluator": "claude-opus-5-5",
    "summarizer": "claude-haiku-5-5",
}
EFFORT = {  # thinking depth per agent: low | medium | high
    "planner": "low",
    "rag": "low",
    "evaluator": "medium",
    "summarizer": "low",
}
MAX_TOKENS = {"planner": 1500, "rag": 4000, "evaluator": 6000, "summarizer": 1500}

# USD per 1M tokens (input, output) - used for the live cost counter
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}

# ---------------------------------------------------------------- planner policy
ACCEPT_THRESHOLD = 0.70    # confidence >= this -> show answer
ESCALATE_THRESHOLD = 0.45  # still below this after re-query -> escalate
MAX_ATTEMPTS = 2           # 1 answer + at most 1 re-query
SUMMARY_EVERY = 3          # Summarizer runs every N turns
RECENT_TURNS = 3           # raw turns kept next to the running summary

# confidence = weighted mix of the Evaluator's scores
CONFIDENCE_WEIGHTS = {"faithfulness": 0.5, "completeness": 0.3, "relevance": 0.2}
