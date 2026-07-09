"""
Text embeddings for semantic matching.

Backend priority:
1. fastembed (ONNX, no torch — works without Windows Long Path support)
2. sentence-transformers (if installed)
3. TF-IDF fallback (keyword-only, no semantic understanding)

All embeddings are L2-normalized float32, so inner product == cosine similarity.
"""
import numpy as np

_embed_fn = None
_backend = None
_vectorizer = None


def _normalize(emb):
    emb = np.asarray(emb, dtype="float32")
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return emb / norms


def _load_backend():
    global _embed_fn, _backend
    if _backend is not None:
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
    single = isinstance(texts, str)
    if single:
        texts = [texts]

    if _load_backend() != "tfidf":
        emb = _embed_fn(texts)
    else:
        if _vectorizer is None:
            raise RuntimeError("TF-IDF fallback requires fit_corpus() before get_embeddings()")
        emb = _normalize(_vectorizer.transform(texts).toarray())

    return emb[0] if single else emb
