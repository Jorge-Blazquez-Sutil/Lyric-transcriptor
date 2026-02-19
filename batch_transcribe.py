#!/usr/bin/env python3
"""
Batch transcription script for processing all audio files in the uploads folder.
Uses Demucs for vocal separation before transcription for improved accuracy.
"""

import os
import shutil
from pathlib import Path
from transcriber import transcribe_audio


def batch_transcribe(uploads_dir='uploads', results_dir='results', use_separation=True):
    """
    Batch transcribes all audio files from uploads_dir and saves results to results_dir.

    Args:
        uploads_dir (str): Directory containing audio files to process.
        results_dir (str): Directory to save transcription results.
        use_separation (bool): Whether to use vocal separation before transcription (default True).
    """
    # Ensure results directory exists
    os.makedirs(results_dir, exist_ok=True)

    # Audio file extensions
    audio_extensions = ('.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg')

    # Get list of audio files
    audio_files = []
    for file in os.listdir(uploads_dir):
        if file.lower().endswith(audio_extensions):
            audio_files.append(file)

    audio_files.sort()
    total = len(audio_files)

    if total == 0:
        print("No audio files found in uploads directory.")
        return

    print(f"Found {total} audio files to transcribe")
    print(f"Using vocal separation: {use_separation}\n")

    # Process each audio file
    processed = 0
    failed = 0

    for i, filename in enumerate(audio_files, 1):
        filepath = os.path.join(uploads_dir, filename)
        audio_basename = Path(filename).stem

        print(f"[{i}/{total}] Transcribing: {filename}")

        try:
            # Create subdirectory for this audio file's results
            audio_result_dir = os.path.join(results_dir, audio_basename)
            os.makedirs(audio_result_dir, exist_ok=True)

            # Transcribe audio
            print(f"  → Separating vocals and transcribing...")
            transcript_text = transcribe_audio(filepath, model_size='large', use_separation=use_separation)

            # Check for errors
            if transcript_text.startswith("Error"):
                print(f"  ✗ Transcription error: {transcript_text}")
                failed += 1
                continue

            # Save transcription
            txt_filename = f"{audio_basename}.txt"
            txt_path = os.path.join(audio_result_dir, txt_filename)
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(transcript_text)

            print(f"  ✓ Transcription saved to {txt_path}")

            # Copy separated audio files if they exist
            if use_separation:
                separated_source_dir = os.path.join(uploads_dir, f"{audio_basename}_separated", audio_basename)

                if os.path.exists(separated_source_dir):
                    separated_dest_dir = os.path.join(audio_result_dir, "separated")

                    # Remove existing separated directory if present
                    if os.path.exists(separated_dest_dir):
                        shutil.rmtree(separated_dest_dir)

                    # Copy separated files
                    shutil.copytree(separated_source_dir, separated_dest_dir)
                    print(f"  ✓ Separated audio files saved to {separated_dest_dir}")

            processed += 1
            print()

        except Exception as e:
            print(f"  ✗ Error: {str(e)}\n")
            failed += 1

    # Print summary
    print("=" * 60)
    print(f"Batch transcription completed!")
    print(f"  Total files: {total}")
    print(f"  Successfully processed: {processed}")
    print(f"  Failed: {failed}")
    print(f"  Results saved to: {results_dir}/")
    print("=" * 60)


if __name__ == '__main__':
    import sys

    # Accept optional command line arguments
    uploads = sys.argv[1] if len(sys.argv) > 1 else 'uploads'
    results = sys.argv[2] if len(sys.argv) > 2 else 'results'
    separation = sys.argv[3].lower() != 'false' if len(sys.argv) > 3 else True

    batch_transcribe(uploads, results, separation)
