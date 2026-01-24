from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import pickle
import os

# Global vectorizer instance
vectorizer = None

def get_or_create_vectorizer():
    global vectorizer
    if vectorizer is None:
        vectorizer_path = "data/vector_store/tfidf_vectorizer.pkl"
        if os.path.exists(vectorizer_path):
            with open(vectorizer_path, 'rb') as f:
                vectorizer = pickle.load(f)
        else:
            vectorizer = TfidfVectorizer(max_features=384, stop_words='english')
    return vectorizer

def fit_vectorizer(text_list):
    """
    Fits the vectorizer on the given text data.
    """
    global vectorizer
    vectorizer = TfidfVectorizer(max_features=384, stop_words='english')
    vectorizer.fit(text_list)
    return vectorizer

def get_embeddings(text):
    """
    Generates embeddings for the given text using TF-IDF.
    """
    vec = get_or_create_vectorizer()
    if isinstance(text, str):
        return vec.transform([text]).toarray()[0]
    else:
        return vec.transform(text).toarray()

