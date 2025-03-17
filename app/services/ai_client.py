import requests
from fastapi import HTTPException
from app.config.logging_config import logger
from app.config.settings import OLLAMA_API_URL


def filter_model_response(response: str) -> str:
    """Filter out model's 'thinking' process from the response."""
    if "<think>" in response and "</think>" in response:
        filtered_response = response.split("</think>")[-1].strip()
        return filtered_response
    return response


class OllamaClient:
    """Client for interacting with Ollama API"""

    @staticmethod
    def generate(model: str, prompt: str, images=None) -> str:
        """Send a generate request to Ollama API"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }

        if images:
            payload["images"] = images

        try:
            response = requests.post(OLLAMA_API_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            raw_response = result.get("response", "")

            # Filter out the thinking process
            filtered_response = filter_model_response(raw_response)
            return filtered_response
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error generating content: {str(e)}"
            )
