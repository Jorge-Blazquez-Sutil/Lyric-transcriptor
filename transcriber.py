import whisper

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
        model = whisper.load_model(model_size)
        result = model.transcribe(audio_path)
        return result['text']
        
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"
