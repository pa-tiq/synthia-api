# This lets you import all summarization functions directly from the package
from app.services.summarization.text import generate_text_summary
from app.services.summarization.image import generate_image_summary
from app.services.summarization.pdf import summarize_pdf
from app.services.summarization.audio import summarize_audio

__all__ = [
    "generate_text_summary",
    "generate_image_summary",
    "summarize_pdf",
    "summarize_audio",
]
