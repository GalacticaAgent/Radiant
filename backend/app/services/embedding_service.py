import hashlib
from functools import lru_cache
from typing import List, Optional

from app.core.config import settings
from openai import OpenAI


class EmbeddingService:
    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        dim: Optional[int] = None,
    ):
        self.provider = provider or settings.EMBEDDING_PROVIDER
        self.api_key = api_key or settings.EMBEDDING_API_KEY or settings.DEEPSEEK_API_KEY
        self.base_url = base_url or settings.EMBEDDING_BASE_URL
        self.model = model or settings.EMBEDDING_MODEL
        self.dim = dim or settings.EMBEDDING_DIM

    @staticmethod
    def content_hash(text: str) -> str:
        return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

    def embed_text(self, text: str) -> List[float]:
        if not settings.EMBEDDING_ENABLED:
            raise RuntimeError("Embedding is disabled (EMBEDDING_ENABLED=false)")
        if self.provider == "openai":
            if not self.api_key:
                raise RuntimeError("Embedding API key not configured")
            client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.base_url else OpenAI(api_key=self.api_key)
            resp = client.embeddings.create(model=self.model, input=text)
            vec = resp.data[0].embedding
            if self.dim and len(vec) != self.dim:
                self.dim = len(vec)
            return vec

        if self.provider in {"sentence_transformers", "local"}:
            model = _get_sentence_transformer(self.model)
            vec = model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0].tolist()
            if self.dim and len(vec) != self.dim:
                self.dim = len(vec)
            return vec

        raise RuntimeError(f"Unsupported embedding provider: {self.provider}")


@lru_cache(maxsize=2)
def _get_sentence_transformer(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise RuntimeError(
            "Local embeddings require sentence-transformers. "
            "Install backend/requirements-embeddings-local.txt or switch EMBEDDING_PROVIDER=openai."
        ) from e

    return SentenceTransformer(model_name)
