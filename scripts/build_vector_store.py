import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import faiss
import pickle

def build_vector_store():
    """
    Builds a FAISS vector store from the job dataset.
    """
    df = pd.read_csv("data/jobs_dataset.csv")
    df.dropna(subset=['description'], inplace=True)
    
    job_descriptions = df['description'].tolist()
    
    print("Generating TF-IDF embeddings for job descriptions...")
    vectorizer = TfidfVectorizer(max_features=384, stop_words='english')
    job_embeddings = vectorizer.fit_transform(job_descriptions).toarray()
    
    embedding_dim = job_embeddings.shape[1]
    index = faiss.IndexFlatL2(embedding_dim)
    
    index.add(np.array(job_embeddings).astype('float32'))
    
    os.makedirs("data/vector_store", exist_ok=True)
    faiss.write_index(index, "data/vector_store/jobs.index")
    
    # Save the vectorizer for later use
    with open("data/vector_store/tfidf_vectorizer.pkl", 'wb') as f:
        pickle.dump(vectorizer, f)
    
    df.to_pickle("data/vector_store/jobs_data.pkl")
    
    print(f"Vector store built successfully with {len(job_descriptions)} jobs.")
    print(f"Embedding dimension: {embedding_dim}")

if __name__ == "__main__":
    build_vector_store()
