from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Request
from app.core.enums import FileType
from app.core.models import SummaryResponse, JobStatusResponse, JobStatus
from app.config.logging_config import logger
from app.services.file_service import save_upload_file, cleanup_file
from app.services.summarization.text import generate_text_summary
from app.services.summarization.image import generate_image_summary
from app.services.summarization.pdf import summarize_pdf
from app.services.summarization.audio import summarize_audio
from rq import Queue, job
import redis

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
async def summarize_file(
    request: Request,
    file: UploadFile = File(...),
    file_type: FileType = Form(...),
    file_name: str = Form(...),
    target_language: str = Form("en"),
):
    """Universal endpoint for submitting files for summarization."""
    file_path = await save_upload_file(file, file_name)
    queue: Queue = request.app.state.redis_queue
    job = queue.enqueue(
        process_summarization, file_path, file_type, file_name, target_language
    )
    return {"job_id": job.id}


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


@router.post("/summarize/text", response_model=SummaryResponse)
async def summarize_text(
    request: Request, text: str = Form(...), target_language: str = Form("en")
):
    """Summarize directly provided text via queue."""
    if target_language == "pt":
        target_language = "pt-br"
    queue: Queue = request.app.state.redis_queue
    job = queue.enqueue(generate_text_summary, text, target_language)
    return {"job_id": job.id}
