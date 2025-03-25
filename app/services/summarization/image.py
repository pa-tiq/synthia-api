import base64
from app.config.logging_config import logger
from app.config.settings import LLAVA_MODEL
from app.services.ai_client import OllamaClient
from app.services.translation import translate_en_to_pt


def generate_image_summary(image_path: str, target_language: str = "en") -> str:
    """Generate a summary of an image using LLaVA"""
    try:
        # Read the image file as base64
        with open(image_path, "rb") as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode("utf-8")

        # Prepare the prompt for LLaVA
        prompt = f"Please describe this image in detail and summarize its key elements."

        summary = OllamaClient.generate(
            model=LLAVA_MODEL, prompt=prompt, images=[image_base64]
        )

        logger.info(f"Image summary (LLavA): {summary}")

        needs_translation = target_language.lower() != "en"
        if needs_translation:
            logger.info("Translating summary back to Portuguese")
            summary = translate_en_to_pt(summary)
            logger.info(f"Summary translation complete: {len(summary)} characters")
            logger.info(f"#####################################")
            logger.info(f"{summary}")
            logger.info(f"#####################################")

        return summary

    except Exception as e:
        logger.error(f"Error generating image summary: {e}")
        raise
