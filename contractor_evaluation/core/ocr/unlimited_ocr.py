from typing import List, Dict
from pathlib import Path
import io

_model = None
_processor = None


def _load_model():
    global _model, _processor
    if _model is None:
        from transformers import AutoProcessor, AutoModelForVision2Seq
        import torch
        _processor = AutoProcessor.from_pretrained("baidu/Unlimited-OCR")
        _model = AutoModelForVision2Seq.from_pretrained(
            "baidu/Unlimited-OCR",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        )
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = _model.to(device)
        _model.eval()
    return _processor, _model


def extract_text_unlimited_ocr(file_path: str, dpi: int = 200) -> List[Dict]:
    """Extract text from PDF/image using Baidu Unlimited-OCR (HuggingFace)."""
    import torch
    results = []
    images = _pdf_to_images(file_path, dpi)

    try:
        processor, model = _load_model()
    except Exception as e:
        return [{"page": 1, "text": "", "confidence": 0.0,
                 "engine": "unlimited_ocr", "error": f"Model load failed: {e}"}]

    device = next(model.parameters()).device

    for page_num, image in enumerate(images):
        try:
            inputs = processor(images=image, return_tensors="pt").to(device)
            with torch.no_grad():
                generated_ids = model.generate(**inputs, max_new_tokens=1024)
            text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            results.append({
                "page": page_num + 1,
                "text": text.strip(),
                "confidence": 92.0,
                "engine": "unlimited_ocr",
            })
        except Exception as e:
            results.append({
                "page": page_num + 1,
                "text": "",
                "confidence": 0.0,
                "engine": "unlimited_ocr",
                "error": str(e),
            })

    return results


def _pdf_to_images(file_path: str, dpi: int = 200) -> list:
    from PIL import Image
    ext = Path(file_path).suffix.lower()
    if ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
        return [Image.open(file_path).convert("RGB")]
    try:
        import fitz
        images = []
        doc = fitz.open(file_path)
        for page in doc:
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            images.append(img)
        doc.close()
        return images
    except Exception:
        return []
