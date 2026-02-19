import pandas as pd
import os
import time
from downloader import download_audio_from_url
from transcriber import transcribe_audio
from audio_separator import separate_audio

def process_excel(file_path):
    output_dir = "results/processed_soundcloud"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Reading file: {file_path}")
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # Normalize column names
    df.columns = [c.upper() for c in df.columns]

    if 'URL' not in df.columns:
        print("Error: 'URL' column not found.")
        return

    rows = df.to_dict('records')
    print(f"Found {len(rows)} entries to process.")

    results_log = []

    for i, row in enumerate(rows):
        url = row.get('URL')
        if not url or pd.isna(url):
            continue
            
        platform = row.get('PLATAFORMA')
        if pd.isna(platform):
            platform = None
            
        print(f"\n[{i+1}/{len(rows)}] Processing: {url}")
        if platform:
            print(f"Platform: {platform}")
        
        # 1. Download
        audio_path = download_audio_from_url(url, output_dir, platform=platform)
        
        if not audio_path:
            print(f"FAILED: Download failed for {url}")
            results_log.append({'url': url, 'status': 'Download Failed', 'path': None})
            continue

        print(f"Downloaded: {audio_path}")
        
        # Separate Audio
        # Use a temp directory for separation to keep the output folder clean
        temp_demucs_dir = os.path.join(output_dir, f"temp_demucs_{i}")
        vocals_path = separate_audio(audio_path, output_base_dir=temp_demucs_dir)
        
        transcription_source = vocals_path if vocals_path else audio_path
        
        # Transcribe
        print(f"Transcribing: {transcription_source}")
        try: # The try block starts here to catch transcription and cleanup errors
            transcript = transcribe_audio(transcription_source, model_size='base')
            
            # Save transcript
            original_filename = os.path.basename(audio_path)
            txt_filename = os.path.splitext(original_filename)[0] + ".txt"
            txt_path = os.path.join(output_dir, txt_filename)
            
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(transcript)
                
            print(f"Transcription saved to: {txt_path}")
            
            # Cleanup Demucs temp files
            if os.path.exists(temp_demucs_dir):
                try:
                    shutil.rmtree(temp_demucs_dir)
                    print(f"Cleaned up temp directory: {temp_demucs_dir}")
                except Exception as e:
                    print(f"Error cleaning up temp directory: {e}")
            
            results_log.append({'url': url, 'status': 'Success', 'path': txt_path})
            
        except Exception as e:
            print(f"Transcription failed: {e}")
            results_log.append({'url': url, 'status': 'Transcription Failed', 'path': audio_path})

    print("\nProcessing complete.")
    for res in results_log:
        print(f"{res['url']} -> {res['status']}")

if __name__ == "__main__":
    process_excel("Soundcloud.xlsx")
