import os
import subprocess
import shutil

def separate_audio(audio_path, output_base_dir="separated_audio"):
    """
    Separates audio using Demucs.
    
    Args:
        audio_path (str): Path to the input audio file.
        output_base_dir (str): Base directory for Demucs output.
        
    Returns:
        str: Path to the isolated vocals file, or None if failed.
    """
    try:
        if not os.path.exists(audio_path):
            print(f"Audio file not found: {audio_path}")
            return None

        # Ensure output directory exists
        if not os.path.exists(output_base_dir):
            os.makedirs(output_base_dir)

        print(f"Separating audio with Demucs: {audio_path}")
        
        # Construct Demucs command
        # -n htdemucs: Use the hybrid transformer model (faster and good quality)
        # --mp3: Save as MP3 to avoid TorchCodec errors and save space
        command = [
            "demucs",
            "-n", "htdemucs",
            "--mp3",
            "--out", output_base_dir,
            audio_path
        ]
        
        # Run Demucs
        subprocess.run(command, check=True)
        
        # Construct expected path to vocals
        # Demucs output structure: output_dir/htdemucs/song_name/vocals.mp3
        filename = os.path.basename(audio_path)
        song_name = os.path.splitext(filename)[0]
        
        # Demucs might sanitize the song name in the output folder
        # We need to find the correct folder in htdemucs output
        model_output_dir = os.path.join(output_base_dir, "htdemucs")
        
        # Find the folder that sounds like our song
        # Simplest way is to look for the most recently created folder or match name
        # But Demucs naming can be tricky with special chars. 
        # For now, let's assume standard behavior or search.
        
        # Let's try to predict the name Demucs used
        # Demucs replaces spaces with similar chars or keeps them depending on version
        # It's safer to check the directory list in model_output_dir
        
        candidate_dirs = os.listdir(model_output_dir)
        # Filter for directories
        candidate_dirs = [d for d in candidate_dirs if os.path.isdir(os.path.join(model_output_dir, d))]
        
        # Find the best match (naive approach: checks if song_name is part of dir name?)
        # Better: Since we just ran it, it should be there.
        # Let's try direct path first.
        vocals_path = os.path.join(model_output_dir, song_name, "vocals.mp3")
        
        if os.path.exists(vocals_path):
             print(f"Vocals found at: {vocals_path}")
             return vocals_path
             
        # If not found directly, try finding the folder by matching sanitized name behavior?
        # Or just return None for now and debug if needed.
        # Actually, let's try to look for the track name in the output folder
        for d in candidate_dirs:
             # If the directory name is a "clean" version of song_name
             pass 

        # If direct path failed, maybe check recent modify time?
        # For now, sticking to simple path.
        
        print(f"Could not locate vocals file at expected path: {vocals_path}")
        # Try to look into subdirectories of model_output_dir to find 'vocals.wav'
        # and return the one matching our file?
        
        return None

    except subprocess.CalledProcessError as e:
        print(f"Demucs separation failed: {e}")
        return None
    except Exception as e:
        print(f"Error during separation: {e}")
        return None
