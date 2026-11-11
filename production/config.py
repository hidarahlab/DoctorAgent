from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
PDF_PATH = DATA_DIR / "medical_book.pdf"
CHUNKS_PATH = DATA_DIR / "chunks.json"
INDEX_DIR = ROOT / "index"

FIRST_CONTENT_PAGE = 13 
CHUNK_CHARS = 1200
OVERLAP_CHARS = 200

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_CACHE = ROOT / ".models"
TOP_K = 5
CANDIDATES = 30
RRF_K = 60

MODELS = {
    "planner": "claude-haiku-5-5",
    "rag": "claude-opus-5-5",
    "evaluator": "claude-opus-5-5",
    "summarizer": "claude-haiku-5-5",
}
EFFORT = {
    "planner": "low",
    "rag": "low",
    "evaluator": "medium",
    "summarizer": "low",
}
MAX_TOKENS = {"planner": 1500, "rag": 4000, "evaluator": 6000, "summarizer": 1500}

PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}

ACCEPT_THRESHOLD = 0.70
ESCALATE_THRESHOLD = 0.45
MAX_ATTEMPTS = 2
SUMMARY_EVERY = 3
RECENT_TURNS = 3

CONFIDENCE_WEIGHTS = {"faithfulness": 0.5, "completeness": 0.3, "relevance": 0.2}
