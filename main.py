from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import tempfile
import shutil
from enum import Enum
import logging
from typing import Optional
import subprocess
import fitz  # PyMuPDF
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Synthia API", description="API for summarizing various types of files"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Flutter app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define file types
class FileType(str, Enum):
    PDF = "pdf"
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"


# Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
LLAVA_MODEL = "llava:7b"
TEXT_MODEL = "deepseek-r1:1.5b"


# Models for responses
class SummaryResponse(BaseModel):
    summary: str
    file_type: FileType
    file_name: str


# Helper functions
def generate_text_summary(text: str) -> str:
    """Generate a summary using the text model"""
    prompt = f"Please summarize the following text concisely:\n\n{text}"

    payload = {
        "model": TEXT_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error generating summary: {str(e)}"
        )


def generate_image_summary(image_path: str) -> str:
    """Generate a summary of an image using LLaVA"""
    prompt = "Please describe this image in detail and summarize its key elements."

    payload = {
        "model": LLAVA_MODEL,
        "prompt": prompt,
        "images": [image_path],
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error generating image summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error generating image summary: {str(e)}"
        )


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file using PyMuPDF"""
    try:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error extracting text from PDF: {str(e)}"
        )


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using Whisper"""
    try:
        # Run whisper command
        result = subprocess.run(
            ["whisper", audio_path, "--model", "base"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Get the output file (same name but .txt extension)
        txt_path = os.path.splitext(audio_path)[0] + ".txt"

        if os.path.exists(txt_path):
            with open(txt_path, "r") as f:
                transcript = f.read()
            return transcript
        else:
            return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error transcribing audio: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during audio transcription: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during audio transcription: {str(e)}",
        )


# Endpoints
@app.post("/summarize", response_model=SummaryResponse)
async def summarize_file(
    file: UploadFile = File(...),
    file_type: FileType = Form(...),
    file_name: str = Form(...),
):
    """
    Universal endpoint for summarizing files.
    This endpoint handles different file types and routes them to the appropriate processor.
    """
    logger.info(f"Received file: {file_name}, type: {file_type}")

    # Create temp directory to store the file
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, file_name)

        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        summary = ""

        # Process based on file type
        if file_type == FileType.PDF:
            text = extract_text_from_pdf(file_path)
            summary = generate_text_summary(text)

        elif file_type == FileType.AUDIO:
            transcript = transcribe_audio(file_path)
            summary = generate_text_summary(transcript)

        elif file_type == FileType.IMAGE:
            summary = generate_image_summary(file_path)

        elif file_type == FileType.TEXT:
            with open(file_path, "r") as text_file:
                text = text_file.read()
            summary = generate_text_summary(text)

        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported file type: {file_type}"
            )

    return SummaryResponse(summary=summary, file_type=file_type, file_name=file_name)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# For direct text input
@app.post("/summarize/text", response_model=SummaryResponse)
async def summarize_text(text: str = Form(...)):
    """Summarize directly provided text"""
    summary = generate_text_summary(text)
    return SummaryResponse(
        summary=summary, file_type=FileType.TEXT, file_name="direct_input.txt"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
