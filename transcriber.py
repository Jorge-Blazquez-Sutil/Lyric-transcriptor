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

def transcribe_audio(audio_path, model_size='base'):
    """
    Transcribes audio file to text using OpenAI Whisper.
    
    Args:
        audio_path (str): Path to audio file.
        model_size (str): Size of Whisper model ('tiny', 'base', 'small', 'medium', 'large').
        
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
