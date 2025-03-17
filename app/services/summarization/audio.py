import os
import shutil
import subprocess
import time
from app.config.logging_config import logger
from app.config.settings import TEMP_DIR
from app.services.summarization.text import generate_text_summary


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using Whisper"""
    try:
        # Create a dedicated temp directory if it doesn't exist
        os.makedirs(TEMP_DIR, exist_ok=True)

        # Get unique filename for this transcription
        file_basename = os.path.basename(audio_path)
        file_name, file_ext = os.path.splitext(file_basename)
        unique_id = f"{file_name}_{int(time.time())}"
        temp_wav_path = os.path.join(TEMP_DIR, f"{unique_id}.wav")

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
        raise


def summarize_audio(audio_path: str, target_language: str = "en") -> str:
    """Transcribe audio and generate a summary"""
    transcript = transcribe_audio(audio_path)
    return generate_text_summary(transcript, target_language)
