# [synthia-api](https://github.com/pa-tiq/synthia-api)

## Folder Structure:

├── .env                         # Environment variables (not in version control)
├── .gitignore                   # Git ignore file
├── requirements.txt             # Python dependencies
├── app/                         # Main application package
│   ├── main.py                  # Application entry point
│   ├── config/                  # Configuration
│   │   ├── settings.py          # App settings and constants
│   │   └── logging_config.py    # Logging configuration
│   ├── api/                     # API routes
│   │   ├── endpoints/           # API endpoint modules
│   │   │   └── summarize.py     # Summarization endpoints
│   │   └── dependencies.py      # Shared API dependencies
│   ├── core/                    # Core application code
│   │   ├── models.py            # Pydantic models
│   │   └── enums.py             # Enum definitions (like FileType)
│   ├── services/                # Business logic services
│   │   ├── file_service.py      # File handling operations
│   │   ├── summarization/       # Summarization services
│   │   │   ├── base.py          # Base class/interface for summarizers
│   │   │   ├── text.py          # Text summarization
│   │   │   ├── image.py         # Image summarization
│   │   │   ├── pdf.py           # PDF processing
│   │   │   └── audio.py         # Audio transcription and summarization
│   │   └── ai_client.py         # Ollama API client wrapper
│   └── utils/                   # Utility functions
│       ├── file_helpers.py      # File handling utilities
│       └── temp_manager.py      # Temporary file management
└── tests/                       # Unit and integration tests
    ├── conftest.py              # Test fixtures
    ├── test_api/                # API tests
    │   └── test_summarize.py
    └── test_services/           # Service tests
        ├── test_file_service.py
        └── test_summarization/
            ├── test_text.py
            ├── test_image.py
            ├── test_pdf.py
            └── test_audio.py

## Install FFMPEG

Linux:

```bash
sudo apt-get install ffmpeg
```

## Run models with Ollama

1. [Install ollama](https://ollama.com/download)

2. Run [DeepSeek](https://ollama.com/library/deepseek-r1:1.5b):

```bash
ollama run deepseek-r1:1.5b
```

3. Run [LLaVA](https://ollama.com/library/llava:7b):

```bash
ollama run llava:7b
```

## Run the API

1. Create and activate venv with:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install requirements with:

```bash
pip install -r requirements.txt
```

3. Run with:

```bash
uvicorn main:app --reload
```
