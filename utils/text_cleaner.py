import re


def clean_text(text):
    """
    Lowercases and normalizes whitespace while preserving tech tokens
    like C++, C#, Node.js, .NET, and CI/CD.
    """
    text = text.lower()
    text = re.sub(r"[^\w\s+#./-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
