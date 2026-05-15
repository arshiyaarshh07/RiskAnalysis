import pdfplumber
import fitz

def extract_text_pdf(file_path):
    text = ""

    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

        if len(text.strip()) > 50:
            return text

        return fallback_pymupdf(file_path)

    except Exception as e:
        return fallback_pymupdf(file_path)


def fallback_pymupdf(file_path):
    text = ""

    doc = fitz.open(file_path)

    for page in doc:
        text += page.get_text()

    return text