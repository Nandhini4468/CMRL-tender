from typing import List, Dict
import fitz  # pymupdf


def extract_text_pymupdf(file_path: str) -> List[Dict]:
    """Extract text from PDF using PyMuPDF (best for digital/searchable PDFs)."""
    results = []
    try:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            blocks = page.get_text("blocks")
            has_images = len(page.get_images()) > 0
            results.append({
                "page": page_num + 1,
                "text": text.strip(),
                "has_images": has_images,
                "block_count": len(blocks),
                "engine": "pymupdf",
                "confidence": 95.0 if text.strip() else 0.0,
            })
        doc.close()
    except Exception as e:
        results.append({"page": 1, "text": "", "engine": "pymupdf", "error": str(e), "confidence": 0.0})
    return results


def extract_images_from_pdf(file_path: str, output_dir: str) -> List[str]:
    """Extract embedded images from a PDF for further OCR processing."""
    import os
    from pathlib import Path

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    image_paths = []

    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]
            ext = base_image["ext"]
            img_path = output_path / f"page{page_num+1}_img{img_index}.{ext}"
            with open(img_path, "wb") as f:
                f.write(img_bytes)
            image_paths.append(str(img_path))
    doc.close()
    return image_paths
