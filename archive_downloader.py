import os
import yt_dlp

def download_archive(url, output_dir):
    """
    Downloads audio from an Archive.org URL using yt-dlp.
    
    Args:
        url (str): The Archive.org URL to download.
        output_dir (str): The directory to save the downloaded file.
        
    Returns:
        str: The path to the downloaded file on success, None on failure.
    """
    try:
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"Downloading from Archive.org: {url}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            # Use original filename if possible, otherwise title
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first to get filename
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Since we requested mp3 conversion, the final file will have .mp3 extension
            base, _ = os.path.splitext(filename)
            final_path = base + ".mp3"
            
            if os.path.exists(final_path):
                print(f"Archive.org download successful: {final_path}")
                return final_path
            
            # Fallback if the file post-processing didn't behave as expected
            if os.path.exists(filename):
                print(f"Archive.org download successful (original format): {filename}")
                return filename

            print(f"Archive.org download finished but file not found: {final_path}")
            return None
            
    except Exception as e:
        print(f"Archive.org download failed: {e}")
        return None
