import fitz  # PyMuPDF
from app.config.logging_config import logger
from app.services.summarization.text import generate_text_summary


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file using PyMuPDF"""
    try:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise


def summarize_pdf(pdf_path: str, target_language: str = "en") -> str:
    """Extract text from PDF and generate a summary"""
    text = extract_text_from_pdf(pdf_path)
    return generate_text_summary(text, target_language)
