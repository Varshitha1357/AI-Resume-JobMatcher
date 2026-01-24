import fitz  # PyMuPDF

def parse_pdf(file_path):
    """
    Parses a PDF file and extracts the text.
    """
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text
