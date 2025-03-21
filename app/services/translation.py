# app/services/translation.py
from transformers import MarianMTModel, MarianTokenizer
import torch
from app.config.logging_config import logger
from app.config.settings import MODELS_DIR
import os

# Global variables to store models and tokenizers
pt_to_en_model = None
pt_to_en_tokenizer = None
en_to_pt_model = None
en_to_pt_tokenizer = None


def load_translation_models():
    """
    Load translation models and tokenizers.
    Models are loaded on-demand and kept in memory.
    """
    global pt_to_en_model, pt_to_en_tokenizer, en_to_pt_model, en_to_pt_tokenizer

    # Create models directory if it doesn't exist
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Check if models are already loaded
    if pt_to_en_model is None:
        try:
            logger.info("Loading Portuguese-to-English translation model")
            pt_to_en_model_name = "Helsinki-NLP/opus-mt-pt-en"
            # Cache models in the MODELS_DIR
            pt_to_en_tokenizer = MarianTokenizer.from_pretrained(
                pt_to_en_model_name, cache_dir=MODELS_DIR
            )
            pt_to_en_model = MarianMTModel.from_pretrained(
                pt_to_en_model_name, cache_dir=MODELS_DIR
            )
            logger.info("Successfully loaded Portuguese-to-English model")
        except Exception as e:
            logger.error(f"Failed to load Portuguese-to-English model: {e}")
            raise

    if en_to_pt_model is None:
        try:
            logger.info("Loading English-to-Portuguese translation model")
            en_to_pt_model_name = "Helsinki-NLP/opus-mt-en-pt"
            en_to_pt_tokenizer = MarianTokenizer.from_pretrained(
                en_to_pt_model_name, cache_dir=MODELS_DIR
            )
            en_to_pt_model = MarianMTModel.from_pretrained(
                en_to_pt_model_name, cache_dir=MODELS_DIR
            )
            logger.info("Successfully loaded English-to-Portuguese model")
        except Exception as e:
            logger.error(f"Failed to load English-to-Portuguese model: {e}")
            raise


def translate_pt_to_en(text):
    """Translate Portuguese text to English"""
    global pt_to_en_model, pt_to_en_tokenizer

    # Load models if not already loaded
    if pt_to_en_model is None:
        load_translation_models()

    try:
        # For long texts, split into chunks and process separately
        if len(text) > 1000:
            logger.info("Long text detected, splitting into chunks for translation")
            chunks = [text[i : i + 1000] for i in range(0, len(text), 1000)]
            translated_chunks = []

            for chunk in chunks:
                inputs = pt_to_en_tokenizer(chunk, return_tensors="pt", padding=True)
                with torch.no_grad():
                    outputs = pt_to_en_model.generate(**inputs)
                chunk_translation = pt_to_en_tokenizer.batch_decode(
                    outputs, skip_special_tokens=True
                )[0]
                translated_chunks.append(chunk_translation)

            return " ".join(translated_chunks)
        else:
            inputs = pt_to_en_tokenizer(text, return_tensors="pt", padding=True)
            with torch.no_grad():
                outputs = pt_to_en_model.generate(**inputs)
            return pt_to_en_tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
    except Exception as e:
        logger.error(f"Error translating from Portuguese to English: {e}")
        raise


def translate_en_to_pt(text):
    """Translate English text to Portuguese"""
    global en_to_pt_model, en_to_pt_tokenizer

    # Load models if not already loaded
    if en_to_pt_model is None:
        load_translation_models()

    try:
        # For long texts, split into chunks and process separately
        if len(text) > 1000:
            logger.info("Long text detected, splitting into chunks for translation")
            chunks = [text[i : i + 1000] for i in range(0, len(text), 1000)]
            translated_chunks = []

            for chunk in chunks:
                inputs = en_to_pt_tokenizer(chunk, return_tensors="pt", padding=True)
                with torch.no_grad():
                    outputs = en_to_pt_model.generate(**inputs)
                chunk_translation = en_to_pt_tokenizer.batch_decode(
                    outputs, skip_special_tokens=True
                )[0]
                translated_chunks.append(chunk_translation)

            return " ".join(translated_chunks)
        else:
            inputs = en_to_pt_tokenizer(text, return_tensors="pt", padding=True)
            with torch.no_grad():
                outputs = en_to_pt_model.generate(**inputs)
            return en_to_pt_tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
    except Exception as e:
        logger.error(f"Error translating from English to Portuguese: {e}")
        raise
