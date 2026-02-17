import whisper
import os
import shutil
import subprocess
from pathlib import Path

def separate_vocals(audio_path, output_dir):
    """
    Separates vocals from audio using Demucs CLI.

    Args:
        audio_path (str): Path to audio file.
        output_dir (str): Directory to save separated audio files.

    Returns:
        str: Path to the separated vocals file.
    """
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Get the audio filename without extension
        audio_filename = Path(audio_path).stem

        # Execute demucs CLI command
        # demucs outputs to: output_dir/htdemucs/audio_basename/
        cmd = ['demucs', '--out', output_dir, audio_path]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Construct path to vocals file
        # Structure: output_dir/htdemucs/audio_basename/vocals.wav
        vocals_path = os.path.join(output_dir, 'htdemucs', audio_filename, 'vocals.wav')

        if not os.path.exists(vocals_path):
            raise FileNotFoundError(f"Vocals file not found at {vocals_path}")

        return vocals_path

    except subprocess.CalledProcessError as e:
        raise Exception(f"Error running demucs: {e.stderr}")
    except Exception as e:
        raise Exception(f"Error separating vocals: {str(e)}")


def transcribe_audio(audio_path, model_size='large', use_separation=True):
    """
    Transcribes audio file to text using OpenAI Whisper.
    Optionally separates vocals first using Demucs CLI for better accuracy with music.

    Args:
        audio_path (str): Path to audio file.
        model_size (str): Size of Whisper model ('tiny', 'base', 'small', 'medium', 'large').
        use_separation (bool): Whether to separate vocals before transcribing (default True).

    Returns:
        str: Transcribed text.
    """
    try:
        transcription_audio_path = audio_path

        if use_separation:
            # Create temporary directory for separated audio
            audio_dir = os.path.dirname(audio_path) if os.path.dirname(audio_path) else '.'
            audio_filename = Path(audio_path).stem
            separation_dir = os.path.join(audio_dir, f"{audio_filename}_separated")

            # Separate vocals
            transcription_audio_path = separate_vocals(audio_path, separation_dir)

        # Transcribe
        model = whisper.load_model(model_size)
        result = model.transcribe(transcription_audio_path)
        return result['text']

    except Exception as e:
        return f"Error transcribing audio: {str(e)}"
