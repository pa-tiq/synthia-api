# app/services/summarization/audio.py
import os
import shutil
import requests
import time
from app.config.logging_config import logger
from app.config.settings import TEMP_DIR
from app.services.summarization.text import generate_text_summary
import whisper
from app.config.settings import CONVERSION_API_URL


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using Whisper"""
    try:
        # Create a dedicated temp directory if it doesn't exist
        os.makedirs(TEMP_DIR, exist_ok=True)

        # Get unique filename for this transcription
        file_basename = os.path.basename(audio_path)
        file_name, file_ext = os.path.splitext(file_basename)

        # Process the audio file - either convert or use as-is
        if file_ext.lower() != ".wav":
            # File needs conversion - send to conversion API
            logger.info(f"Sending file to conversion API: {audio_path}")

            # Send file to conversion API
            with open(audio_path, "rb") as file:
                files = {
                    "file": (file_basename, file, "audio/ogg")
                }  # Adjust content type as needed
                response = requests.post(f"{CONVERSION_API_URL}/convert/", files=files)

            if response.status_code != 200:
                logger.error(f"Conversion API error: {response.text}")
                raise Exception(
                    f"Conversion API returned error: {response.status_code}"
                )

            # Get job details
            job_data = response.json()
            job_id = job_data["job_id"]
            logger.info(f"Conversion job created with ID: {job_id}")

            # Poll for completion
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            while True:
                # Check if we've exceeded the wait time
                if time.time() - start_time > max_wait_time:
                    raise Exception(
                        f"Conversion timed out after {max_wait_time} seconds"
                    )

                # Check job status
                status_response = requests.get(f"{CONVERSION_API_URL}/status/{job_id}")
                if status_response.status_code != 200:
                    logger.error(
                        f"Error checking conversion status: {status_response.text}"
                    )
                    raise Exception("Failed to check conversion status")

                status_data = status_response.json()

                if status_data["status"] == "completed":
                    # Download the converted file
                    logger.info(f"Conversion completed, downloading WAV file")
                    download_response = requests.get(
                        f"{CONVERSION_API_URL}/download/{job_id}"
                    )

                    if download_response.status_code != 200:
                        logger.error(
                            f"Error downloading converted file: {download_response.text}"
                        )
                        raise Exception("Failed to download converted file")

                    # Save the downloaded file
                    unique_id = f"{file_name}_{int(time.time())}"
                    processed_audio_path = os.path.join(TEMP_DIR, f"{unique_id}.wav")
                    with open(processed_audio_path, "wb") as f:
                        f.write(download_response.content)

                    logger.info(f"Downloaded converted file to {processed_audio_path}")
                    break

                elif status_data["status"] == "failed":
                    logger.error(
                        f"Conversion failed: {status_data.get('error', 'Unknown error')}"
                    )
                    raise Exception(
                        f"Audio conversion failed: {status_data.get('error', 'Unknown error')}"
                    )

                # Wait before checking again
                time.sleep(2)
        else:
            # If it's already WAV, copy to temp dir
            unique_id = f"{file_name}_{int(time.time())}"
            processed_audio_path = os.path.join(TEMP_DIR, f"{unique_id}.wav")
            shutil.copy2(audio_path, processed_audio_path)
            logger.info(f"File is already WAV, copied to {processed_audio_path}")

        # Process with Whisper
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
        raise


def summarize_audio(audio_path: str, target_language: str = "en") -> str:
    """Transcribe audio and generate a summary"""
    transcript = transcribe_audio(audio_path)
    logger.info(f"#############################")
    logger.info(f"AUDIO TRANSCRIPT: {transcript}")
    logger.info(f"#############################")
    return generate_text_summary(transcript, target_language)
