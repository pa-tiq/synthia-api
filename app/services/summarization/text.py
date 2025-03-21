from app.config.logging_config import logger
from app.config.settings import TEXT_MODEL
from app.services.ai_client import OllamaClient
from app.services.translation import translate_pt_to_en, translate_en_to_pt


def generate_text_summary(text: str, target_language: str = "en") -> str:
    """
    Generate a summary using the text model with translation support.

    Args:
        text: The text to summarize
        target_language: The target language code ('en' for English, 'pt' for Portuguese)

    Returns:
        A summary in the target language
    """
    try:
        # Step 1: If target language is Portuguese, translate to English first
        input_text = text
        # needs_translation = target_language.lower() != "pt"
        needs_translation = False

        if needs_translation:
            logger.info("Translating Portuguese input to English for summarization")
            input_text = translate_pt_to_en(text)
            logger.info(f"Translation complete: {len(input_text)} characters")

        # Step 2: Generate summary using the English model
        prompt = f"Please summarize the following text concisely without emitting opinions:\n\n{input_text}"
        logger.info(f"Generating summary using {TEXT_MODEL}")
        summary = OllamaClient.generate(model=TEXT_MODEL, prompt=prompt)

        # Step 3: If target language is Portuguese, translate summary back
        if needs_translation:
            logger.info("Translating summary back to Portuguese")
            summary = translate_en_to_pt(summary)
            logger.info(f"Summary translation complete: {len(summary)} characters")

        return summary
    except Exception as e:
        logger.error(f"Error in generate_text_summary: {e}")
        raise
