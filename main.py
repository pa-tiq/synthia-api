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
import time
import uuid

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


def filter_model_response(response: str) -> str:
    """Filter out model's 'thinking' process from the response."""
    # Check if response contains <think> tags
    if "<think>" in response and "</think>" in response:
        # Extract only the part after </think>
        filtered_response = response.split("</think>")[-1].strip()
        return filtered_response
    return response


# Then modify your generate_text_summary function:
def generate_text_summary(text: str, target_language: str) -> str:
    """Generate a summary using the text model"""
    prompt = f"Please, in the language {target_language}, summarize the following text concisely:\n\n{text}"

    payload = {
        "model": TEXT_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        raw_response = result.get("response", "")

        # Filter out the thinking process
        filtered_response = filter_model_response(raw_response)
        return filtered_response
    except requests.exceptions.RequestException as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error generating summary: {str(e)}"
        )


def generate_image_summary(image_path: str, target_language: str) -> str:
    """Generate a summary of an image using LLaVA"""
    try:
        # Read the image file as base64
        with open(image_path, "rb") as img_file:
            import base64

            image_base64 = base64.b64encode(img_file.read()).decode("utf-8")

        # Prepare the payload for LLaVA
        payload = {
            "model": LLAVA_MODEL,
            "prompt": f"Please describe this image in detail and summarize its key elements in the language {target_language}:",
            "images": [image_base64],  # Send as base64 string
            "stream": False,
        }

        # Send to Ollama API
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        logger.debug(f"Image summary: {response}")
        result = response.json()
        return result.get("response", "")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error generating image summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error generating image summary: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during image processing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during image processing: {str(e)}",
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
    """Transcribe audio using Whisper with centralized temp directory"""
    try:
        import shutil

        # Create a dedicated temp directory if it doesn't exist
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
        os.makedirs(temp_dir, exist_ok=True)

        # Get unique filename for this transcription
        file_basename = os.path.basename(audio_path)
        file_name, file_ext = os.path.splitext(file_basename)
        unique_id = f"{file_name}_{int(time.time())}"
        temp_wav_path = os.path.join(temp_dir, f"{unique_id}.wav")

        # Check if ffmpeg is installed
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            logger.warning("ffmpeg not found in system PATH")
            # Try common installation paths
            for possible_path in [
                "/usr/bin/ffmpeg",
                "/usr/local/bin/ffmpeg",
                "/opt/homebrew/bin/ffmpeg",
            ]:
                if os.path.exists(possible_path):
                    ffmpeg_path = possible_path
                    break

            if not ffmpeg_path:
                raise Exception(
                    "ffmpeg not found. Please install ffmpeg and ensure it's in your PATH."
                )

        logger.info(f"Using ffmpeg at: {ffmpeg_path}")

        # Convert audio to WAV format if it's not already (Whisper works best with WAV)
        if file_ext.lower() not in [".wav"]:
            # Convert to WAV using ffmpeg
            convert_cmd = [
                ffmpeg_path,
                "-i",
                audio_path,
                "-ar",
                "16000",  # 16kHz sample rate (recommended for Whisper)
                "-ac",
                "1",  # mono
                "-c:a",
                "pcm_s16le",  # 16-bit PCM
                "-y",  # overwrite output file
                temp_wav_path,
            ]

            logger.info(f"Converting audio to WAV format: {' '.join(convert_cmd)}")
            conversion_result = subprocess.run(
                convert_cmd, capture_output=True, text=True
            )

            if conversion_result.returncode != 0:
                logger.error(f"Audio conversion failed: {conversion_result.stderr}")
                raise Exception(
                    f"Failed to convert audio file: {conversion_result.stderr}"
                )

            logger.info("Audio conversion successful")
            processed_audio_path = temp_wav_path
        else:
            # If it's already WAV, copy to temp dir
            processed_audio_path = temp_wav_path
            shutil.copy2(audio_path, processed_audio_path)

        # Use Whisper Python package
        import whisper

        logger.info("Loading Whisper model")
        model = whisper.load_model("base")

        logger.info(f"Transcribing audio file: {processed_audio_path}")
        result = model.transcribe(processed_audio_path)

        # The transcript is in the 'text' field of the result
        transcript = result["text"]
        logger.info(f"Transcription successful: {len(transcript)} characters")

        # Clean up temporary files
        try:
            os.remove(processed_audio_path)
            logger.info(f"Removed temporary file: {processed_audio_path}")
        except Exception as e:
            logger.warning(f"Could not remove temporary file: {e}")

        return transcript
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error transcribing audio: {str(e)}"
        )


def get_temp_dir():
    """Get or create the application's temp directory"""
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


@app.post("/summarize", response_model=SummaryResponse)
async def summarize_file(
    file: UploadFile = File(...),
    file_type: FileType = Form(...),
    file_name: str = Form(...),
    target_language: str = Form("en"),
):
    """
    Universal endpoint for summarizing files.
    This endpoint handles different file types and routes them to the appropriate processor.
    """
    logger.info(f"Received file: {file_name}, type: {file_type}")
    if target_language == "pt":
        target_language = "pt-br"
    # Create a unique filename to avoid collisions
    unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
    file_extension = os.path.splitext(file_name)[1]
    unique_filename = f"{unique_id}{file_extension}"

    # Get the temp directory
    temp_dir = get_temp_dir()
    file_path = os.path.join(temp_dir, unique_filename)

    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Saved uploaded file to: {file_path}")
        summary = ""

        # Process based on file type
        if file_type == FileType.PDF:
            text = extract_text_from_pdf(file_path)
            summary = generate_text_summary(text, target_language)

        elif file_type == FileType.AUDIO:
            transcript = transcribe_audio(file_path)
            summary = generate_text_summary(transcript, target_language)

        elif file_type == FileType.IMAGE:
            summary = generate_image_summary(file_path, target_language)

        elif file_type == FileType.TEXT:
            with open(file_path, "r") as text_file:
                text = text_file.read()
            summary = generate_text_summary(text, target_language)

        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported file type: {file_type}"
            )

        # Clean up the temporary file
        try:
            os.remove(file_path)
            logger.info(f"Removed temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not remove temporary file: {e}")

        return SummaryResponse(
            summary=summary, file_type=file_type, file_name=file_name
        )
    except Exception as e:
        # Clean up on error too
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

        logger.error(f"Error processing {file_type} file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Add a cleanup job at application startup
@app.on_event("startup")
async def startup_event():
    """Clean up any leftover temporary files at startup"""
    temp_dir = get_temp_dir()
    try:
        # Delete files older than 1 hour
        current_time = time.time()
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getctime(file_path)
                # Delete if older than 1 hour (3600 seconds)
                if file_age > 3600:
                    os.remove(file_path)
                    logger.info(f"Cleaned up old temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Error during temp file cleanup: {e}")


# Add a scheduled cleanup function that runs periodically (if you want)
@app.on_event("startup")
async def setup_periodic_cleanup():
    """Set up periodic cleanup of temporary files"""
    import asyncio

    async def periodic_cleanup():
        while True:
            try:
                temp_dir = get_temp_dir()
                current_time = time.time()
                for filename in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, filename)
                    if os.path.isfile(file_path):
                        file_age = current_time - os.path.getctime(file_path)
                        # Delete if older than 1 hour (3600 seconds)
                        if file_age > 3600:
                            os.remove(file_path)
                            logger.info(f"Cleaned up old temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Error during periodic temp file cleanup: {e}")

            # Wait for 30 minutes before next cleanup
            await asyncio.sleep(1800)

    # Start the cleanup task
    asyncio.create_task(periodic_cleanup())


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
