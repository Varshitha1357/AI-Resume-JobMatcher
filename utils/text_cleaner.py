import re

def clean_text(text):
    """
    Cleans the text by removing special characters and extra spaces.
    """
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()
