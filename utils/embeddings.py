"""
Text embeddings for semantic matching.

Backend priority:
1. Gemini embeddings API (if GEMINI_API_KEY is set — no local compute,
   ideal for weak free-tier hosts; free at https://aistudio.google.com/apikey)
2. fastembed (ONNX, no torch — works without Windows Long Path support)
3. sentence-transformers (if installed)
4. TF-IDF fallback (keyword-only, no semantic understanding)

All embeddings are L2-normalized float32, so inner product == cosine similarity.
"""
import os

import numpy as np

_embed_fn = None
_backend = None
_vectorizer = None
_gemini_failed = False


def _normalize(emb):
    emb = np.asarray(emb, dtype="float32")
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return emb / norms


GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
GEMINI_CHUNK_SIZE = 25


def _gemini_embed(texts, api_key):
    """
    Embeds via the Gemini API in small chunks. The free tier rate-limits
    aggressively, so 429s are retried with a wait before giving up.
    """
    import time

    import requests

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{GEMINI_EMBED_MODEL}:batchEmbedContents?key={api_key}"
    )
    vectors = []
    for i in range(0, len(texts), GEMINI_CHUNK_SIZE):
        chunk = texts[i:i + GEMINI_CHUNK_SIZE]
        payload = {
            "requests": [
                {
                    "model": f"models/{GEMINI_EMBED_MODEL}",
                    "content": {"parts": [{"text": t or " "}]},
                    "outputDimensionality": 768,
                }
                for t in chunk
            ]
        }
        for attempt in range(4):
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 429 and attempt < 3:
                wait = 15 * (attempt + 1)
                print(f"Gemini rate limit hit; retrying in {wait}s...")
                time.sleep(wait)
                continue
            response.raise_for_status()
            break
        vectors.extend(e["values"] for e in response.json()["embeddings"])
    # Truncated gemini embeddings aren't pre-normalized; _normalize fixes that
    return _normalize(vectors)


def _load_backend():
    global _embed_fn, _backend
    if _backend is not None:
        return _backend

    api_key = os.getenv("GEMINI_API_KEY")
    prefer_local = os.getenv("EMBED_BACKEND", "").lower() in ("local", "fastembed")
    if api_key and not _gemini_failed and not prefer_local:
        print(f"Using Gemini embeddings API ({GEMINI_EMBED_MODEL})")
        _embed_fn = lambda texts: _gemini_embed(texts, api_key)
        _backend = "gemini"
        return _backend

    try:
        from fastembed import TextEmbedding
        print("Loading fastembed model (BAAI/bge-small-en-v1.5)...")
        model = TextEmbedding("BAAI/bge-small-en-v1.5")
        _embed_fn = lambda texts: _normalize(list(model.embed(texts)))
        _backend = "fastembed"
        return _backend
    except Exception as e:
        print(f"fastembed unavailable ({e})")

    try:
        from sentence_transformers import SentenceTransformer
        print("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        _embed_fn = lambda texts: np.asarray(
            model.encode(texts, normalize_embeddings=True, show_progress_bar=False),
            dtype="float32",
        )
        _backend = "sentence-transformers"
        return _backend
    except Exception as e:
        print(f"sentence-transformers unavailable ({e}); falling back to TF-IDF")

    _backend = "tfidf"
    return _backend


def get_backend():
    """Returns the active embedding backend name: 'gemini', 'fastembed', 'sentence-transformers', or 'tfidf'."""
    return _load_backend()


def fit_corpus(texts):
    """
    Prepare the embedder for a corpus of documents.
    No-op for semantic backends; fits the vectorizer for the TF-IDF fallback.
    """
    global _vectorizer
    if _load_backend() == "tfidf":
        from sklearn.feature_extraction.text import TfidfVectorizer
        _vectorizer = TfidfVectorizer(max_features=768, stop_words="english")
        _vectorizer.fit(texts)


def get_embeddings(texts):
    """
    Returns L2-normalized float32 embeddings.
    Accepts a single string (returns 1D array) or a list of strings (returns 2D array).
    """
    global _backend, _gemini_failed

    single = isinstance(texts, str)
    if single:
        texts = [texts]

    if _load_backend() != "tfidf":
        try:
            emb = _embed_fn(texts)
        except Exception as e:
            if _backend == "gemini":
                # API hiccup or quota — drop to the next local backend and retry
                print(f"Gemini embeddings failed ({e}); switching to local backend")
                _gemini_failed = True
                _backend = None
                return get_embeddings(texts[0] if single else texts)
            raise
    else:
        if _vectorizer is None:
            raise RuntimeError("TF-IDF fallback requires fit_corpus() before get_embeddings()")
        emb = _normalize(_vectorizer.transform(texts).toarray())

    return emb[0] if single else emb
