from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from app.core.enums import FileType
from app.core.models import SummaryResponse
from app.config.logging_config import logger
from app.services.file_service import save_upload_file, cleanup_file
from app.services.summarization.text import generate_text_summary
from app.services.summarization.image import generate_image_summary
from app.services.summarization.pdf import summarize_pdf
from app.services.summarization.audio import summarize_audio

router = APIRouter()


@router.post("/summarize", response_model=SummaryResponse)
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

    # Handle Brazilian Portuguese language code
    if target_language == "pt":
        target_language = "pt-br"

    # Save the uploaded file
    file_path = await save_upload_file(file, file_name)

    try:
        summary = ""

        # Process based on file type
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
            raise HTTPException(
                status_code=400, detail=f"Unsupported file type: {file_type}"
            )

        return SummaryResponse(
            summary=summary, file_type=file_type, file_name=file_name
        )
    except Exception as e:
        logger.error(f"Error processing {file_type} file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary file
        cleanup_file(file_path)


@router.post("/summarize/text", response_model=SummaryResponse)
async def summarize_text(text: str = Form(...), target_language: str = Form("en")):
    """Summarize directly provided text"""
    summary = generate_text_summary(text, target_language)
    return SummaryResponse(
        summary=summary, file_type=FileType.TEXT, file_name="direct_input.txt"
    )
