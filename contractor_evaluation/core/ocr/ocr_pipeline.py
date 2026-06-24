from typing import List, Dict, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import docx

from core.ocr.pymupdf_ocr import extract_text_pymupdf
from core.ocr.tesseract_ocr import extract_text_tesseract, extract_text_tesseract_highsens, configure_tesseract
from core.ocr.ocr_cache import get_cached, save_cache

# Pages with fewer characters than this are treated as scanned/image pages
SCANNED_PAGE_THRESHOLD = 80


def run_ocr_pipeline(
    file_path: str,
    tesseract_cmd: str,
    use_engines: Optional[List[str]] = None,
    high_sensitivity: bool = False,
    use_cache: bool = True,
) -> Dict:
    """
    Smart multi-engine OCR with caching.

    Strategy:
      1. Check disk cache — return immediately if hit.
      2. Run PyMuPDF on all pages (fast, milliseconds).
      3. Identify scanned pages (text < SCANNED_PAGE_THRESHOLD chars).
      4. Run Tesseract ONLY on scanned pages — skip for digital pages.
      5. Fuse results and cache.
    """
    configure_tesseract(tesseract_cmd)
    ext = Path(file_path).suffix.lower()

    if ext == ".docx":
        return _extract_docx(file_path)

    # Cache check
    if use_cache:
        cached = get_cached(file_path)
        if cached:
            cached["from_cache"] = True
            return cached

    if use_engines is None:
        use_engines = ["pymupdf", "tesseract"]

    # Step 1: PyMuPDF on all pages (always fast)
    pymupdf_pages = extract_text_pymupdf(file_path) if "pymupdf" in use_engines else []

    # Step 2: Identify which pages need OCR (scanned / image-only)
    scanned_page_nums = [
        p["page"] for p in pymupdf_pages
        if len(p.get("text", "").strip()) < SCANNED_PAGE_THRESHOLD
    ]

    # Step 3: Run Tesseract only on scanned pages
    tesseract_page_map: Dict[int, Dict] = {}
    if "tesseract" in use_engines and scanned_page_nums:
        if high_sensitivity:
            tess_results = extract_text_tesseract_highsens(file_path, dpi=300)
        else:
            tess_results = extract_text_tesseract(file_path, dpi=200)
        for r in tess_results:
            if r["page"] in scanned_page_nums:
                tesseract_page_map[r["page"]] = r

    # Step 4: Fuse — prefer PyMuPDF for text-rich pages, Tesseract for scanned
    fused_pages = []
    for p in pymupdf_pages:
        page_num = p["page"]
        if page_num in tesseract_page_map:
            tess = tesseract_page_map[page_num]
            # Use whichever has more content
            best = tess if len(tess.get("text", "")) > len(p.get("text", "")) else p
            fused_pages.append({
                "page": page_num,
                "text": best.get("text", ""),
                "confidence": best.get("confidence", 0.0),
                "engine_used": best.get("engine", "tesseract"),
            })
        else:
            fused_pages.append({
                "page": page_num,
                "text": p.get("text", ""),
                "confidence": p.get("confidence", 95.0),
                "engine_used": "pymupdf",
            })

    full_text = "\n\n".join(p["text"] for p in fused_pages if p["text"])
    avg_conf = sum(p["confidence"] for p in fused_pages) / len(fused_pages) if fused_pages else 0.0
    scanned_count = len(scanned_page_nums)

    result = {
        "pages": fused_pages,
        "full_text": full_text,
        "avg_confidence": round(avg_conf, 2),
        "total_pages": len(fused_pages),
        "scanned_pages": scanned_count,
        "digital_pages": len(fused_pages) - scanned_count,
        "from_cache": False,
    }

    if use_cache:
        save_cache(file_path, result)

    return result


def extract_all_bidder_docs(
    bidder_files: List[Dict],
    tesseract_cmd: str,
    max_workers: int = 4,
    progress_callback=None,
) -> List[Dict]:
    """
    Process all files for one bidder in parallel threads.
    progress_callback(file_name, status_str) is called after each file completes.
    """
    all_pages: List[Dict] = []
    completed = 0

    def process_file(file_info: Dict):
        result = run_ocr_pipeline(file_info["path"], tesseract_cmd)
        pages = []
        for page in result["pages"]:
            pages.append({
                "source_file": file_info["name"],
                "page": page["page"],
                "text": page["text"],
                "confidence": page["confidence"],
                "engine_used": page["engine_used"],
            })
        return file_info["name"], pages, result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, f): f for f in bidder_files}
        for future in as_completed(futures):
            try:
                file_name, pages, result = future.result()
                all_pages.extend(pages)
                completed += 1
                cache_hit = result.get("from_cache", False)
                status = (
                    f"{'[cache]' if cache_hit else '[ocr]'} "
                    f"{file_name}: {result['total_pages']} pages "
                    f"({result['digital_pages']} digital, {result['scanned_pages']} scanned)"
                )
                if progress_callback:
                    progress_callback(file_name, status)
            except Exception as e:
                file_name = futures[future]["name"]
                if progress_callback:
                    progress_callback(file_name, f"ERROR: {file_name} — {e}")

    # Sort by source file then page number for consistent ordering
    all_pages.sort(key=lambda p: (p["source_file"], p["page"]))
    return all_pages


def _extract_docx(file_path: str) -> Dict:
    doc = docx.Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    full_text = "\n".join(paragraphs)
    return {
        "pages": [{"page": 1, "text": full_text, "confidence": 99.0, "engine_used": "python-docx"}],
        "full_text": full_text,
        "avg_confidence": 99.0,
        "total_pages": 1,
        "scanned_pages": 0,
        "digital_pages": 1,
        "from_cache": False,
    }
