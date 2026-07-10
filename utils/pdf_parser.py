import fitz  # PyMuPDF


def parse_pdf(file_path):
    """Parses a PDF file from disk and extracts the text."""
    with fitz.open(file_path) as doc:
        return "".join(page.get_text() for page in doc)


def parse_pdf_bytes(data):
    """
    Parses a PDF from raw bytes and extracts the text.
    Used for uploads so resumes are never written to disk.
    """
    with fitz.open(stream=data, filetype="pdf") as doc:
        return "".join(page.get_text() for page in doc)
