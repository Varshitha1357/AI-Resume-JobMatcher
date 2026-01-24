import faiss
import numpy as np
import pandas as pd
from utils.embeddings import get_embeddings
import os

def retrieve_relevant_jobs(resume_text, k=5):
    """
    Retrieves the most relevant job descriptions from the vector store.
    """
    index_path = "data/vector_store/jobs.index"
    data_path = "data/vector_store/jobs_data.pkl"
    
    if not os.path.exists(index_path) or not os.path.exists(data_path):
        return []

    index = faiss.read_index(index_path)
    df = pd.read_pickle(data_path)
    
    resume_embedding = get_embeddings(resume_text)
    
    # Ensure embedding is 2D for FAISS
    if len(resume_embedding.shape) == 1:
        resume_embedding = resume_embedding.reshape(1, -1)
    
    distances, indices = index.search(resume_embedding.astype('float32'), k)
    
    relevant_jobs = df.iloc[indices[0]].to_dict(orient='records')
    return relevant_jobs
