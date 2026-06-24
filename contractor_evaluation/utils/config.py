import os
import sys
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Allow secrets set via Streamlit Cloud dashboard to be read as env vars
try:
    import streamlit as st
    for _k, _v in st.secrets.items():
        if isinstance(_v, str):
            os.environ.setdefault(_k, _v)
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma_db"))

# Auto-detect Tesseract: env var > system PATH > Windows default
def _find_tesseract() -> str:
    if sys.platform.startswith("win"):
        return os.getenv("TESSERACT_CMD", r"C:/Program Files/Tesseract-OCR/tesseract.exe")
    return os.getenv("TESSERACT_CMD", shutil.which("tesseract") or "tesseract")

# Auto-detect Poppler: env var > empty string (system PATH on Linux)
def _find_poppler() -> str:
    if sys.platform.startswith("win"):
        return os.getenv("POPPLER_PATH", r"C:/poppler/Library/bin")
    return os.getenv("POPPLER_PATH", "")

TESSERACT_CMD = _find_tesseract()
POPPLER_PATH = _find_poppler()

DATA_DIR = BASE_DIR / "data"
CRITERIA_DIR = DATA_DIR / "criteria"
BIDDERS_DIR = DATA_DIR / "bidders"
OUTPUTS_DIR = DATA_DIR / "outputs"

for d in [CRITERIA_DIR, BIDDERS_DIR, OUTPUTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
