# conversion_api/main.py
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
import os
import uuid
import shutil
import subprocess
from pydantic import BaseModel
import time
from typing import Dict, Optional

app = FastAPI(title="Audio Conversion API")

# Configuration
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
OUTPUT_DIR = os.path.join(os.getcwd(), "converted")
ALLOWED_EXTENSIONS = [".mp3", ".ogg", ".m4a", ".flac", ".aac", ".wma", ".opus"]

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# In-memory job tracking
conversion_jobs: Dict[str, Dict] = {}


class ConversionStatus(BaseModel):
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    input_file: str
    output_file: Optional[str] = None
    error: Optional[str] = None
    start_time: float
    end_time: Optional[float] = None


@app.post("/convert/", response_model=ConversionStatus)
async def convert_audio(
    background_tasks: BackgroundTasks, file: UploadFile = File(...)
):
    """Upload and convert audio file to WAV format"""
    # Validate file extension
    filename = file.filename
    file_ext = os.path.splitext(filename)[1].lower()

    if file_ext not in ALLOWED_EXTENSIONS and file_ext != ".wav":
        raise HTTPException(status_code=400, detail="Unsupported file format")

    # If already WAV, no need to convert
    if file_ext == ".wav":
        raise HTTPException(status_code=400, detail="File is already in WAV format")

    # Generate unique job ID and filenames
    job_id = str(uuid.uuid4())
    unique_filename = f"{job_id}{file_ext}"
    upload_path = os.path.join(UPLOAD_DIR, unique_filename)
    output_filename = f"{job_id}.wav"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Save uploaded file
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create job entry
    job_status = ConversionStatus(
        job_id=job_id,
        status="pending",
        input_file=unique_filename,
        start_time=time.time(),
    )
    conversion_jobs[job_id] = job_status.dict()

    # Schedule background conversion
    background_tasks.add_task(convert_file, job_id, upload_path, output_path)

    return job_status


@app.get("/status/{job_id}", response_model=ConversionStatus)
async def get_conversion_status(job_id: str):
    """Get status of a conversion job"""
    if job_id not in conversion_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return conversion_jobs[job_id]


@app.get("/download/{job_id}")
async def download_converted_file(job_id: str):
    """Download a converted WAV file"""
    if job_id not in conversion_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = conversion_jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Conversion job is not completed. Current status: {job['status']}",
        )

    output_path = os.path.join(OUTPUT_DIR, f"{job_id}.wav")

    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Converted file not found")

    return FileResponse(
        path=output_path,
        filename=f"{os.path.splitext(job['input_file'])[0]}.wav",
        media_type="audio/wav",
    )


def convert_file(job_id: str, input_path: str, output_path: str):
    """Background task to convert audio file to WAV"""
    try:
        # Update job status
        conversion_jobs[job_id]["status"] = "processing"

        # Run ffmpeg conversion
        cmd = [
            "ffmpeg",
            "-i",
            input_path,
            "-ar",
            "16000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            "-y",
            output_path,
        ]

        # Run the conversion process with a timeout
        process = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,  # Don't raise exception, we'll handle errors manually
            timeout=120,  # 2-minute timeout
        )

        # Check if conversion was successful
        if process.returncode != 0:
            raise Exception(
                f"ffmpeg error (code {process.returncode}): {process.stderr}"
            )

        # Validate output file exists and has content
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Conversion failed: output file is empty or missing")

        # Update job status to completed
        conversion_jobs[job_id]["status"] = "completed"
        conversion_jobs[job_id]["output_file"] = os.path.basename(output_path)
        conversion_jobs[job_id]["end_time"] = time.time()

        # Cleanup input file
        if os.path.exists(input_path):
            os.remove(input_path)

    except subprocess.TimeoutExpired:
        # Handle timeout
        conversion_jobs[job_id]["status"] = "failed"
        conversion_jobs[job_id]["error"] = "Conversion timed out"
        conversion_jobs[job_id]["end_time"] = time.time()

    except Exception as e:
        # Handle other errors
        conversion_jobs[job_id]["status"] = "failed"
        conversion_jobs[job_id]["error"] = str(e)
        conversion_jobs[job_id]["end_time"] = time.time()

        # Cleanup any partial output
        if os.path.exists(output_path):
            os.remove(output_path)


# Add cleanup task (optional)
@app.on_event("startup")
async def startup_event():
    # Clear any old files from previous runs
    for dir_path in [UPLOAD_DIR, OUTPUT_DIR]:
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error cleaning up file {file_path}: {e}")
