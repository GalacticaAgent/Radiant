import builtins

import pytest

from app.services.embedding_service import EmbeddingService


def test_local_embedding_provider_missing_sentence_transformers(monkeypatch):
    orig_import = builtins.__import__

    def blocked_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("sentence_transformers"):
            raise ImportError("blocked for test")
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    monkeypatch.setattr("app.core.config.settings.EMBEDDING_ENABLED", True, raising=False)

    svc = EmbeddingService(provider="local", model="all-MiniLM-L6-v2")
    with pytest.raises(RuntimeError) as e:
        svc.embed_text("hello")
    assert "requirements-embeddings-local.txt" in str(e.value) or "sentence-transformers" in str(e.value)

