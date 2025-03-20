import os
import shutil
import subprocess
import time
from app.config.logging_config import logger
from app.config.settings import TEMP_DIR
from app.services.summarization.text import generate_text_summary
import ffmpeg
import whisper
from multiprocessing import Process, Queue
import signal


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
            ###########################################
            # Convert audio to WAV using ffmpeg-python
            # logger.info(
            #     f"Converting audio to WAV using ffmpeg-python: {audio_path} to {temp_wav_path}"
            # )
            # ffmpeg.input(audio_path).output(
            #     temp_wav_path,
            #     ar=16000,  # 16kHz sample rate (recommended for Whisper)
            #     ac=1,  # mono
            #     acodec="pcm_s16le",  # 16-bit PCM
            #     y=None,  # overwrite output file
            # ).run(capture_stdout=True, capture_stderr=True)
            # logger.info("Audio conversion successful")
            ###########################################

            ###########################################
            # Use subprocess to call ffmpeg directly
            # logger.info(
            #     f"Converting audio to WAV using subprocess: {audio_path} to {temp_wav_path}"
            # )
            # cmd = [
            #     ffmpeg_path,
            #     "-v",
            #     "quiet",
            #     "-i",
            #     audio_path,
            #     "-ar",
            #     "16000",
            #     "-ac",
            #     "1",
            #     "-c:a",
            #     "pcm_s16le",
            #     "-y",
            #     temp_wav_path,
            # ]
            # try:
            #     process = subprocess.run(
            #         cmd, capture_output=True, text=True, check=True, timeout=200
            #     )
            #     logger.info("Audio conversion successful")
            #     logger.debug(f"ffmpeg stdout: {process.stdout}")
            #     logger.debug(f"ffmpeg stderr: {process.stderr}")

            # except subprocess.TimeoutExpired as e:
            #     logger.error(f"ffmpeg conversion timed out after 300 seconds: {e}")
            #     raise Exception("ffmpeg conversion timed out")
            ###########################################
            ###########################################
            # Use Popen
            # logger.info(
            #     f"Converting audio to WAV using Popen: {audio_path} to {temp_wav_path}"
            # )
            # cmd = [
            #     ffmpeg_path,
            #     "-i",
            #     audio_path,
            #     "-ar",
            #     "16000",
            #     "-ac",
            #     "1",
            #     "-c:a",
            #     "pcm_s16le",
            #     "-y",
            #     temp_wav_path,
            # ]
            # process = subprocess.Popen(
            #     cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            # )
            # try:
            #     stdout, stderr = process.communicate(timeout=300)  # 5-minute timeout
            #     if process.returncode != 0:
            #         logger.error(f"ffmpeg error: {stderr}")
            #         raise Exception(
            #             f"ffmpeg conversion failed with code {process.returncode}"
            #         )
            #     logger.info("Audio conversion successful")
            # except subprocess.TimeoutExpired:
            #     process.kill()
            #     logger.error("ffmpeg conversion timed out after 300 seconds")
            #     raise Exception("ffmpeg conversion timed out")
            ###########################################
            ###########################################
            # Multiprocessing
            # logger.info(
            #     f"Converting audio to WAV using multiprocessing: {audio_path} to {temp_wav_path}"
            # )
            # cmd = [
            #     ffmpeg_path,
            #     "-i",
            #     audio_path,
            #     "-ar",
            #     "16000",
            #     "-ac",
            #     "1",
            #     "-c:a",
            #     "pcm_s16le",
            #     "-y",
            #     temp_wav_path,
            # ]
            # result_queue = Queue()
            # p = Process(target=run_ffmpeg, args=(cmd, result_queue))
            # p.start()
            # p.join(timeout=300)  # Wait for up to 5 minutes
            # if p.is_alive():
            #     p.terminate()
            #     p.join(5)  # Give it 5 seconds to terminate
            #     if p.is_alive():
            #         # Force kill if it doesn't terminate
            #         p.kill()
            #         p.join()
            #     raise Exception("ffmpeg conversion timed out")
            # if not result_queue.empty():
            #     status, stdout, stderr = result_queue.get()
            #     if status == "error":
            #         logger.error(f"ffmpeg error: {stdout}")
            #         raise Exception(f"ffmpeg conversion failed: {stdout}")
            #     logger.info("Audio conversion successful")
            # else:
            #     raise Exception("ffmpeg process ended without reporting status")
            ###########################################
            ###########################################
            # Simplified subprocess
            logger.info(
                f"Converting audio to WAV using simplified subprocess: {audio_path} to {temp_wav_path}"
            )
            with open(os.devnull, "w") as devnull:
                cmd = [
                    ffmpeg_path,
                    "-i",
                    audio_path,
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    "-c:a",
                    "pcm_s16le",
                    "-y",
                    temp_wav_path,
                ]

                process = subprocess.run(
                    cmd, stdout=devnull, stderr=devnull, check=True, timeout=60
                )
            if os.path.exists(temp_wav_path) and os.path.getsize(temp_wav_path) > 0:
                logger.info("Audio conversion successful")
            else:
                raise Exception(
                    "ffmpeg conversion failed: output file not created or empty"
                )

            ###########################################

            processed_audio_path = temp_wav_path
        else:
            # If it's already WAV, copy to temp dir
            processed_audio_path = temp_wav_path
            shutil.copy2(audio_path, processed_audio_path)

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
    except ffmpeg.Error as e:
        logger.error(f"ffmpeg-python error: {e.stderr.decode('utf8')}")
        logger.error(f"ffmpeg-python stdout: {e.stdout.decode('utf8')}")
        logger.error(f"ffmpeg-python error: {e.stderr.decode('utf8')}")
        raise Exception(f"ffmpeg-python conversion failed: {e.stderr.decode('utf8')}")
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise


def summarize_audio(audio_path: str, target_language: str = "en") -> str:
    """Transcribe audio and generate a summary"""
    transcript = transcribe_audio(audio_path)
    return generate_text_summary(transcript, target_language)


def run_ffmpeg(cmd, result_queue):
    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        result_queue.put(("success", process.stdout, process.stderr))
    except Exception as e:
        result_queue.put(("error", str(e), ""))
