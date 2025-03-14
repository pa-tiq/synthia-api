# [synthia-api](https://github.com/pa-tiq/synthia-api)

## Run DeepSeek

1. [Install ollama](https://ollama.com/download)

2. Run the [the model](https://ollama.com/library/deepseek-r1:1.5b):

```bash
ollama run deepseek-r1:1.5b
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
