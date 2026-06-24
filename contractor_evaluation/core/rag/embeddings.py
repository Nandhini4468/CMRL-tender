from typing import List
from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """Singleton-style wrapper around sentence-transformers."""

    _instance = None
    _model_name = None

    def __new__(cls, model_name: str = "all-MiniLM-L6-v2"):
        if cls._instance is None or cls._model_name != model_name:
            cls._instance = super().__new__(cls)
            cls._instance.model = SentenceTransformer(model_name)
            cls._model_name = model_name
        return cls._instance

    def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_single(self, text: str) -> List[float]:
        return self.embed([text])[0]
