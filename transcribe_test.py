import os
import glob
from transcriber import transcribe_audio

import sys
# Force UTF-8 output for console
sys.stdout.reconfigure(encoding='utf-8')

# Path to the directory containing audio files
TEST_DIR = r"c:\Users\jorge\OneDrive\Documentos\Prácticas\Scripts\Lyric transcriptor\test_data\465 - أرحنا بالصلاة يا بلال"

def transcribe_folder():
    try:
        print(f"Scanning directory for audio files...")
    except Exception:
        print("Scanning directory...")
    
    # Recursively find .mp3 files
    audio_files = glob.glob(os.path.join(TEST_DIR, "**", "*.mp3"), recursive=True)
    
    if not audio_files:
        print("No audio files found!")
        return

    print(f"Found {len(audio_files)} audio files.")
    
    for audio_path in audio_files:
        print(f"\nProcessing: {os.path.basename(audio_path)}")
        try:
            # Transcribe
            text = transcribe_audio(audio_path, model_size='base') # Use base for speed in test
            
            # Save to text file
            txt_path = os.path.splitext(audio_path)[0] + ".txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
                
            print(f"Transcription saved to: {os.path.basename(txt_path)}")
            print("-" * 30)
            
        except Exception as e:
            print(f"Failed to transcribe {os.path.basename(audio_path)}: {e}")

if __name__ == "__main__":
    transcribe_folder()
