import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
import yt_dlp

def download_audio_from_url(url, output_dir):
    """
    Downloads audio from a given URL.
    Attempts to support muzon-club specifically, or falls back to generic extraction.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': url
    }
    
    # First, try muzon-club specific extraction (since yt-dlp doesn't support it)
    if 'muzon-club.com' in url:
        print(f"Detected muzon-club URL, using custom scraper")
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for CDN download link (cdn.muzon-club.com)
                download_link = None
                
                # Method 1: Find link with cdn.muzon-club.com in href
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if 'cdn.muzon-club.com' in href:
                        download_link = href
                        print(f"Found CDN link: {download_link[:100]}...")
                        break
                
                # Method 2: Look for download button class or similar
                if not download_link:
                    download_btn = soup.find('a', class_=re.compile(r'download|btn.*download', re.I))
                    if download_btn and download_btn.get('href'):
                        download_link = download_btn['href']
                        print(f"Found download button: {download_link[:100]}...")
                
                # Method 3: Look for any link with ?q= parameter (typical for CDN)
                if not download_link:
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if '?q=' in href and ('cdn' in href or 'download' in href.lower()):
                            download_link = href
                            print(f"Found encoded link: {download_link[:100]}...")
                            break
                
                if download_link:
                    # Make sure it's absolute
                    if not download_link.startswith('http'):
                        download_link = urljoin(url, download_link)
                    
                    # Download the file
                    print(f"Downloading from CDN...")
                    mp3_response = requests.get(download_link, headers=headers, stream=True, timeout=120)
                    
                    if mp3_response.status_code == 200:
                        # Try to get filename from Content-Disposition header
                        cd = mp3_response.headers.get('Content-Disposition', '')
                        filename = None
                        if 'filename=' in cd:
                            filename = re.findall(r'filename[^;=\n]*=["\']?([^"\'\n]*)', cd)
                            if filename:
                                filename = unquote(filename[0])
                        
                        # Fallback: extract from page title or URL
                        if not filename:
                            title_tag = soup.find('title')
                            if title_tag:
                                # Clean title for filename
                                filename = title_tag.text.strip()
                                filename = re.sub(r'[<>:"/\\|?*]', '', filename)
                                filename = filename[:100]  # Limit length
                                filename += '.mp3'
                            else:
                                filename = 'audio_' + os.path.basename(url).split('.')[0] + '.mp3'
                        
                        if not filename.endswith('.mp3'):
                            filename += '.mp3'
                        
                        save_path = os.path.join(output_dir, filename)
                        
                        with open(save_path, 'wb') as f:
                            for chunk in mp3_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        print(f"Downloaded: {save_path}")
                        return save_path
                    else:
                        print(f"CDN download failed with status: {mp3_response.status_code}")
                else:
                    print(f"No download link found on page")
            else:
                print(f"Failed to fetch page: {response.status_code}")
        except Exception as e:
            print(f"Muzon-club scraper error: {e}")
    
    # Fallback to yt-dlp for other sites
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
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(filename)
            final_path = base + ".mp3"
            
            if os.path.exists(final_path):
                return final_path
            
            return filename
            
    except Exception as e:
        print(f"yt-dlp failed: {e}")
        return None
        
    return None
