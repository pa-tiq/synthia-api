from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Request
from app.core.enums import FileType
from app.core.models import SummaryResponse, JobStatusResponse, JobStatus
from app.config.logging_config import logger
from app.services.file_service import save_upload_file, cleanup_file
from app.services.summarization.text import generate_text_summary
from app.services.summarization.image import generate_image_summary
from app.services.summarization.pdf import summarize_pdf
from app.services.summarization.audio import summarize_audio
from app.api.endpoints.security import token_manager, encryption_manager
from rq import Queue
import base64
from cryptography.fernet import Fernet
import json


router = APIRouter()


def process_summarization(
    file_path: str, file_type: FileType, file_name: str, target_language: str
):
    """Function to be executed by RQ worker."""
    logger.info(f"Processing file: {file_name}, type: {file_type}")
    try:
        summary = ""
        if file_type == FileType.PDF:
            summary = summarize_pdf(file_path, target_language)
        elif file_type == FileType.AUDIO:
            summary = summarize_audio(file_path, target_language)
        elif file_type == FileType.IMAGE:
            summary = generate_image_summary(file_path, target_language)
        elif file_type == FileType.TEXT:
            with open(file_path, "r") as text_file:
                text = text_file.read()
            summary = generate_text_summary(text, target_language)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        return SummaryResponse(
            summary=summary, file_type=file_type, file_name=file_name
        ).dict()
    except Exception as e:
        logger.error(f"Error processing {file_type} file: {e}")
        raise e
    finally:
        cleanup_file(file_path)


@router.post("/summarize")
async def secure_summarize(
    request: Request,
    user_id: str = Form(...),
    registration_token: str = Form(...),
    encrypted_payload: str = Form(...),
    client_public_key: str = Form(...),
    file: UploadFile = File(...),
    file_type: FileType = Form(...),
    file_name: str = Form(...),
    target_language: str = Form("en"),
):
    """Secure summarization endpoint with user validation and encryption."""
    # Validate user registration
    if not await token_manager.validate_registration(user_id, registration_token):
        raise HTTPException(status_code=403, detail="Invalid or expired registration")

    # Get current symmetric key (will rotate if needed)
    symmetric_key = await token_manager.get_symmetric_key(user_id)
    if not symmetric_key:
        raise HTTPException(status_code=403, detail="Invalid session")

    # Create Fernet cipher for symmetric encryption
    cipher = Fernet(symmetric_key)
    
    try:
        # Decrypt the payload
        decoded_payload = base64.b64decode(encrypted_payload)
        decrypted_payload = cipher.decrypt(decoded_payload)
        
        # You can now use decrypted_payload if needed
        
        # Save uploaded file
        file_path = await save_upload_file(file, file_name)

        # Enqueue summarization job
        queue: Queue = request.app.state.redis_queue
        job = queue.enqueue(
            process_summarization, file_path, file_type, file_name, target_language
        )

        # Encrypt the response
        response_data = {"job_id": job.id}
        encrypted_response = cipher.encrypt(json.dumps(response_data).encode())
        
        # Encrypt new symmetric key with client's public key
        encrypted_key = encryption_manager.encrypt_symmetric_key(
            client_public_key, symmetric_key
        )

        return {
            "encrypted_data": base64.b64encode(encrypted_response).decode(),
            "encrypted_symmetric_key": encrypted_key,
        }

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Encryption/decryption failed: {str(e)}"
        )


@router.post("/summarize/text")
async def secure_text_summarize(
    request: Request,
    user_id: str = Form(...),
    registration_token: str = Form(...),
    text: str = Form(...),
    target_language: str = Form("en"),
):
    """Secure text summarization endpoint."""
    # Validate user registration
    if not await token_manager.validate_registration(user_id, registration_token):
        raise HTTPException(status_code=403, detail="Invalid or expired registration")

    # Enqueue text summarization job
    queue: Queue = request.app.state.redis_queue
    job = queue.enqueue(generate_text_summary, text, target_language)

    return {"job_id": job.id}


# Existing result retrieval endpoint remains the same
@router.get("/result/{job_id}", response_model=JobStatusResponse)
async def get_job_result(request: Request, job_id: str):
    """Endpoint to retrieve the result of a summarization job."""
    queue: Queue = request.app.state.redis_queue
    job = queue.fetch_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.is_finished:
        if job.result:
            return JobStatusResponse(
                status=JobStatus.COMPLETED, job_id=job_id, summary=job.result["summary"]
            )
        else:
            return JobStatusResponse(
                status=JobStatus.FAILED,
                job_id=job_id,
                error="Job finished with no result",
            )

    elif job.is_failed:
        return JobStatusResponse(
            status=JobStatus.FAILED, job_id=job_id, error=str(job.exc_info)
        )
    else:
        return JobStatusResponse(status=JobStatus.PROCESSING, job_id=job_id)
