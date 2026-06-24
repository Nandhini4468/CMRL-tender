from typing import List, Dict
import chromadb
from chromadb.config import Settings

from core.rag.embeddings import EmbeddingModel
from core.rag.chunker import chunk_pages


def _collection_name(bidder_name: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in bidder_name)
    return f"bidder_{safe.lower()}"[:63]


class BidderRetriever:
    def __init__(self, persist_dir: str, bidder_name: str, embedding_model_name: str = "all-MiniLM-L6-v2"):
        self.bidder_name = bidder_name
        self.embedding_model = EmbeddingModel(embedding_model_name)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection_name = _collection_name(bidder_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def index_pages(self, pages: List[Dict], chunk_size: int = 500, chunk_overlap: int = 50):
        """Chunk and index all OCR pages for this bidder."""
        chunks = chunk_pages(pages, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        embeddings = self.embedding_model.embed(texts)
        ids = [c["chunk_id"] for c in chunks]
        metadatas = [
            {
                "source_file": c["source_file"],
                "page": c["page"],
                "chunk_index": c["chunk_index"],
                "ocr_confidence": c["ocr_confidence"],
                "engine_used": c["engine_used"],
            }
            for c in chunks
        ]

        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            self.collection.upsert(
                embeddings=embeddings[i:i+batch_size],
                documents=texts[i:i+batch_size],
                ids=ids[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
            )

    def retrieve(self, query: str, n_results: int = 5) -> List[Dict]:
        """Semantic search: return top-n chunks relevant to the query."""
        if self.collection.count() == 0:
            return []

        query_embedding = self.embedding_model.embed_single(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            similarity = round((1 - dist) * 100, 2)
            chunks.append({
                "text": doc,
                "source_file": meta.get("source_file", ""),
                "page": meta.get("page", 0),
                "ocr_confidence": meta.get("ocr_confidence", 0.0),
                "similarity": similarity,
            })
        return chunks

    def count(self) -> int:
        return self.collection.count()

    def delete(self):
        """Remove this bidder's collection (for re-indexing)."""
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
