# [synthia-api](https://github.com/pa-tiq/synthia-api)

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
