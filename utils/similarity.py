import faiss
import numpy as np


def create_vector_store(embeddings):
    """
    Creates a FAISS inner-product index. Embeddings must be L2-normalized,
    so inner product equals cosine similarity.
    """
    embeddings = np.asarray(embeddings, dtype="float32")
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index


def search_vector_store(index, query_embedding, k=5):
    """
    Searches the vector store. Returns (scores, indices) for the top-k matches,
    where scores are cosine similarities in [-1, 1].
    """
    query = np.asarray([query_embedding], dtype="float32")
    scores, indices = index.search(query, k)
    return scores[0], indices[0]


def cosine_similarity(vec1, vec2):
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return 0.0
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
