from typing import List, Dict
import pytesseract
from PIL import Image
from pathlib import Path


def configure_tesseract(tesseract_cmd: str):
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def extract_text_tesseract(file_path: str, dpi: int = 300, lang: str = "eng") -> List[Dict]:
    """Extract text from PDF/image using Tesseract OCR."""
    results = []
    ext = Path(file_path).suffix.lower()

    if ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
        pages = [Image.open(file_path)]
    else:
        pages = _pdf_to_images(file_path, dpi)

    for page_num, image in enumerate(pages):
        try:
            data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
            text = pytesseract.image_to_string(image, lang=lang)
            confs = [int(c) for c in data["conf"] if str(c).lstrip("-").isdigit() and int(c) >= 0]
            avg_conf = sum(confs) / len(confs) if confs else 0.0
            results.append({
                "page": page_num + 1,
                "text": text.strip(),
                "confidence": round(avg_conf, 2),
                "engine": "tesseract",
            })
        except Exception as e:
            results.append({
                "page": page_num + 1,
                "text": "",
                "confidence": 0.0,
                "engine": "tesseract",
                "error": str(e),
            })
    return results


def extract_text_tesseract_highsens(file_path: str, dpi: int = 400) -> List[Dict]:
    """High-sensitivity re-extraction: higher DPI + PSM 6 (assume uniform block of text)."""
    results = []
    pages = _pdf_to_images(file_path, dpi)
    custom_config = r"--oem 3 --psm 6"
    for page_num, image in enumerate(pages):
        try:
            text = pytesseract.image_to_string(image, config=custom_config)
            data = pytesseract.image_to_data(image, config=custom_config, output_type=pytesseract.Output.DICT)
            confs = [int(c) for c in data["conf"] if str(c).lstrip("-").isdigit() and int(c) >= 0]
            avg_conf = sum(confs) / len(confs) if confs else 0.0
            results.append({
                "page": page_num + 1,
                "text": text.strip(),
                "confidence": round(avg_conf, 2),
                "engine": "tesseract_highsens",
            })
        except Exception as e:
            results.append({
                "page": page_num + 1, "text": "", "confidence": 0.0,
                "engine": "tesseract_highsens", "error": str(e),
            })
    return results


def _pdf_to_images(pdf_path: str, dpi: int) -> list:
    try:
        from pdf2image import convert_from_path
        from utils.config import POPPLER_PATH
        poppler = POPPLER_PATH if Path(POPPLER_PATH).exists() else None
        if poppler:
            return convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler)
        return convert_from_path(pdf_path, dpi=dpi)
    except Exception:
        import fitz
        images = []
        doc = fitz.open(pdf_path)
        for page in doc:
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            images.append(img)
        doc.close()
        return images
