import faiss
import numpy as np

def create_vector_store(embeddings):
    """
    Creates a FAISS vector store from the given embeddings.
    """
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    return index

def search_vector_store(index, query_embedding, k=5):
    """
    Searches the vector store for the most similar vectors.
    """
    distances, indices = index.search(np.array([query_embedding]), k)
    return indices

def cosine_similarity(vec1, vec2):
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return 0.0
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
