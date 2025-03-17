from app.config.logging_config import logger
from app.config.settings import TEXT_MODEL
from app.services.ai_client import OllamaClient


def generate_text_summary(text: str, target_language: str = "en") -> str:
    """Generate a summary using the text model"""
    prompt = f"Please summarize the following text concisely. There's no need to emit an opinion. Just summarize it, extracting the key points of the text. The summary must be in the language {target_language}.\n\n{text}"

    try:
        response = OllamaClient.generate(model=TEXT_MODEL, prompt=prompt)
        return response
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise
