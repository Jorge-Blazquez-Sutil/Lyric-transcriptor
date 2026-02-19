import whisper
import os

# Global cache for the model
_model_cache = {}

def get_model(model_size):
    if model_size not in _model_cache:
        print(f"[DEBUG] Loading Whisper model '{model_size}'...")
        _model_cache[model_size] = whisper.load_model(model_size)
        print(f"[DEBUG] Model '{model_size}' loaded.")
    return _model_cache[model_size]

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
        print(f"[DEBUG] Starting transcription for: {os.path.basename(audio_path)}")
        model = get_model(model_size)
        result = model.transcribe(audio_path)
        print(f"[DEBUG] Transcription finished for: {os.path.basename(audio_path)}")
        return result['text']

    except Exception as e:
        print(f"[ERROR] Transcription failed: {e}")
        return f"Error transcribing audio: {str(e)}"
