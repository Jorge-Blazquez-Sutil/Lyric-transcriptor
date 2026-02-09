import os
import requests
from bs4 import BeautifulSoup
import yt_dlp

def download_audio_from_url(url, output_dir):
    """
    Downloads audio from a given URL.
    Attempts to support muzon-club specifically, or falls back to generic extraction.
    """
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
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
            try:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                # After FFmpeg conversion, the extension might change to .mp3
                base, _ = os.path.splitext(filename)
                final_path = base + ".mp3"
                
                if os.path.exists(final_path):
                    return final_path
                
                return filename # Fallback if post-processing didn't happen as expected
                
            except Exception as e:
                # If yt-dlp fails, try manually scraping for direct MP3 link (specific to some sites)
                # For muzon-club, let's see if we can just find the mp3 link in the HTML
                print(f"yt-dlp failed, trying manual scrape: {e}")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Heuristic: Find first link ending in .mp3
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if href.endswith('.mp3'):
                            if not href.startswith('http'):
                                # Handle relative URLs if necessary (often they are absolute on file hosts)
                                pass 
                            
                            # Download the file
                            mp3_response = requests.get(href, headers=headers, stream=True)
                            if mp3_response.status_code == 200:
                                # Determine filename from URL or header
                                filename = os.path.basename(href)
                                save_path = os.path.join(output_dir, filename)
                                
                                with open(save_path, 'wb') as f:
                                    for chunk in mp3_response.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                return save_path
                                
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None
        
    return None
