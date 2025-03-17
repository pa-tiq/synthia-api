import os
import time
import asyncio
import shutil
from app.config.logging_config import logger
from app.config.settings import TEMP_DIR, TEMP_FILE_MAX_AGE, TEMP_CLEANUP_INTERVAL


def get_temp_dir():
    """Get or create the application's temp directory"""
    os.makedirs(TEMP_DIR, exist_ok=True)
    return TEMP_DIR


def create_temp_file_path(original_filename):
    """Create a unique filename for a temporary file"""
    import uuid

    unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
    file_extension = os.path.splitext(original_filename)[1]
    unique_filename = f"{unique_id}{file_extension}"
    return os.path.join(get_temp_dir(), unique_filename)


def cleanup_temp_files():
    """Clean up temporary files older than the max age"""
    temp_dir = get_temp_dir()
    try:
        current_time = time.time()
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getctime(file_path)
                if file_age > TEMP_FILE_MAX_AGE:
                    os.remove(file_path)
                    logger.info(f"Cleaned up old temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Error during temp file cleanup: {e}")


async def startup_cleanup():
    """Clean up any leftover temporary files at startup"""
    cleanup_temp_files()


async def periodic_cleanup():
    """Periodically clean up temporary files"""
    while True:
        try:
            cleanup_temp_files()
        except Exception as e:
            logger.warning(f"Error during periodic temp file cleanup: {e}")

        # Wait before next cleanup
        await asyncio.sleep(TEMP_CLEANUP_INTERVAL)


async def setup_periodic_cleanup():
    """Set up periodic cleanup of temporary files"""
    asyncio.create_task(periodic_cleanup())
