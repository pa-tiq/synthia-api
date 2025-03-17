import os
import shutil
from fastapi import UploadFile, HTTPException
from app.config.logging_config import logger
from app.utils.temp_manager import create_temp_file_path


async def save_upload_file(file: UploadFile, file_name: str) -> str:
    """Save an uploaded file to a temporary location"""
    file_path = create_temp_file_path(file_name)

    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Saved uploaded file to: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")


def cleanup_file(file_path: str) -> bool:
    """Remove a temporary file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Removed temporary file: {file_path}")
            return True
    except Exception as e:
        logger.warning(f"Could not remove temporary file: {e}")
    return False
