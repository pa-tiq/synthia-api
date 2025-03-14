from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

# Define the Ollama API endpoint
OLLAMA_API_URL = "http://localhost:11434/api/generate"

@app.post("/generate/")
async def generate(prompt: str):
    # Prepare the payload for the Ollama API
    payload = {
        "model": "deepseek-r1:32b",
        "prompt": prompt,
        "stream": False  # Set to True if you want streaming responses
    }

    try:
        # Send the request to the Ollama API
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the response
        result = response.json()
        return {"response": result.get("response", "")}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)