import os
from typing import List

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# CORS settings
CORS_ORIGINS: List[str] = ["*"]  # In production, specify your Flutter app's domain

# Ollama API settings
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
LLAVA_MODEL = os.getenv("LLAVA_MODEL", "llava:7b")
TEXT_MODEL = os.getenv("TEXT_MODEL", "deepseek-r1:1.5b")

# Temp directory settings
TEMP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "temp"
)
TEMP_FILE_MAX_AGE = 3600  # 1 hour in seconds
TEMP_CLEANUP_INTERVAL = 1800  # 30 minutes in seconds
