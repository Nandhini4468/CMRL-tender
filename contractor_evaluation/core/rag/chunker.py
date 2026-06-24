from typing import List, Dict


def chunk_pages(
    pages: List[Dict],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[Dict]:
    """
    Split page-level OCR text into overlapping chunks for vector indexing.
    Each chunk carries source_file, page, and chunk_index metadata.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for page_info in pages:
        text = page_info.get("text", "").strip()
        if not text:
            continue
        splits = splitter.split_text(text)
        for idx, split in enumerate(splits):
            chunk_id = f"{page_info['source_file']}_p{page_info['page']}_c{idx}"
            chunks.append({
                "chunk_id": chunk_id,
                "text": split,
                "source_file": page_info["source_file"],
                "page": page_info["page"],
                "chunk_index": idx,
                "ocr_confidence": page_info.get("confidence", 0.0),
                "engine_used": page_info.get("engine_used", "unknown"),
            })
    return chunks
