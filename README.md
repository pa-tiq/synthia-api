# [synthia-api](https://github.com/pa-tiq/synthia-api)

## Folder Structure:
```
├── .vscode/                     # Vscode files for easy testing and debugging
├── .env                         # Environment variables (not in version control)
├── .gitignore                   # Git ignore file
├── requirements.txt             # Python dependencies
├── app/                         # Main application package
│   ├── worker.py                # Redis Queue worker
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
│   │   ├── translation.py       # Translation operations
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
├── conversion_api/              # Audio conversion API
│   └── main.py                  # Audio conversion API entry point
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
```

## Requirements

### Install FFMPEG and Redis

Linux:

```bash
sudo apt-get install -y ffmpeg redis-server
```

### Run models with Ollama

1. [Install ollama](https://ollama.com/download)

2. Run [DeepSeek](https://ollama.com/library/deepseek-r1:1.5b) for texts:

```bash
ollama run deepseek-r1:1.5b
```

3. Run [LLaVA](https://ollama.com/library/llava:7b) for images:

```bash
ollama run llava:7b
```

### Create and activate the venv, Start Redis, synthia-api's Worker and conversion_api

1. Create and activate the venv with:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install requirements with:

```bash
pip install -r requirements.txt
```

3. Then, start the Redis Server. To check if it's already running, you can launch the `redis-cli` and use the command `ping`. If the response is `PONG`, then the Redis Server is already running.

```bash
redis-server
```

4. Now we launch our worker:

```bash
python app/worker.py
```

5. Finally, launch the conversion_api:

```bash
cd conversion_api
uvicorn main:app --host 0.0.0.0 --port 8001
```


## Run the API

Run with:

```bash
uvicorn app.main:app --reload --port 8000
```

### Helpers

To see if there are any active jobs, use monitor.py:

```bash
python app/monitor.py
```