"""
Simple disk-based OCR cache keyed by file MD5.
Avoids re-running OCR on files that haven't changed.
"""
import json
import hashlib
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "ocr_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _file_md5(file_path: str) -> str:
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_cached(file_path: str):
    key = _file_md5(file_path)
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_cache(file_path: str, result: dict):
    key = _file_md5(file_path)
    cache_file = CACHE_DIR / f"{key}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
