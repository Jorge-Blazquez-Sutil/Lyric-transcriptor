import os
import time
import json
import zipfile
import threading
import shutil
import pandas as pd
from flask import Flask, request, jsonify, send_file, render_template, Response
import uuid

# Import helper functions (to be implemented)
from downloader import download_audio_from_url
from transcriber import transcribe_audio

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['SECRET_KEY'] = 'supersecretkey'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Store job progress in memory (for simplicity)
# Ideally use Redis or a database for production
jobs = {}

def process_file(job_id, file_path):
    """
    Background worker to process the uploaded file.
    """
    job_dir = os.path.join(app.config['RESULTS_FOLDER'], job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    try:
        jobs[job_id]['status'] = 'Reading file...'
        jobs[job_id]['progress'] = 5
        
        # Read Excel/CSV
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        # Standardize column names (case insensitive)
        df.columns = [c.upper() for c in df.columns]
        
        if 'URL' not in df.columns:
            raise ValueError("File must contain a column named 'URL'")
            
        rows = df.to_dict('records')
        total_urls = len(rows)
        
        if total_urls == 0:
            raise ValueError("No rows found")
            
        jobs[job_id]['log'].append(f"Found {total_urls} URLs to process.")
        
        # Process each URL
        audio_files = []
        
        # Helper for separation
        from audio_separator import separate_audio
        import shutil
        
        for i, row in enumerate(rows):
            url = row.get('URL')
            if not url or pd.isna(url):
                continue
                
            platform = row.get('PLATAFORMA')
            if pd.isna(platform):
                platform = None
                
            temp_demucs_dir = None
            try:
                # Update progress
                current_idx = i + 1
                progress = 10 + (current_idx / total_urls) * 70 
                jobs[job_id]['progress'] = progress
                jobs[job_id]['status'] = f"Processing {current_idx}/{total_urls}: {url}"
                
                log_msg = f"Downloading: {url}"
                if platform:
                    log_msg += f" (Platform: {platform})"
                jobs[job_id]['log'].append(log_msg)
                
                # 1. Download Audio
                audio_path = download_audio_from_url(url, job_dir, platform=platform)
                if not audio_path:
                    jobs[job_id]['log'].append(f"Failed to download: {url}")
                    continue
                    
                audio_files.append(audio_path)
                jobs[job_id]['log'].append(f"Downloaded: {os.path.basename(audio_path)}")
                
                # 2. Separate Vocals (Demucs)
                jobs[job_id]['status'] = f"Separating vocals {current_idx}/{total_urls}: {os.path.basename(audio_path)}"
                jobs[job_id]['log'].append(f"Separating vocals...")
                
                # Create a temp dir for this file's separation to keep main dir clean
                temp_demucs_dir = os.path.join(job_dir, f"temp_demucs_{i}")
                vocals_path = separate_audio(audio_path, output_base_dir=temp_demucs_dir)
                
                transcription_source = vocals_path if vocals_path else audio_path
                
                if vocals_path:
                    jobs[job_id]['log'].append(f"Vocals separated successfully.")
                else:
                    jobs[job_id]['log'].append(f"Vocal separation failed, using original audio.")

                # 3. Transcribe Audio
                jobs[job_id]['status'] = f"Transcribing {current_idx}/{total_urls}..."
                jobs[job_id]['log'].append(f"Transcribing...")
                
                print(f"[DEBUG] Calling transcribe_audio for {os.path.basename(transcription_source)}")
                transcript_text = transcribe_audio(transcription_source)
                print(f"[DEBUG] Returned from transcribe_audio")
                
                # Save transcription
                # Use original filename base for the txt file
                original_base = os.path.splitext(os.path.basename(audio_path))[0]
                txt_filename = original_base + ".txt"
                txt_path = os.path.join(job_dir, txt_filename)
                
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(transcript_text)

                # Copy separated audio files to job directory
                audio_basename = os.path.splitext(os.path.basename(audio_path))[0]
                separated_source_dir = os.path.join(os.path.dirname(audio_path), f"{audio_basename}_separated", 'htdemucs')

                if os.path.exists(separated_source_dir):
                    separated_dest_dir = os.path.join(job_dir, 'separated_audio', audio_basename)
                    if os.path.exists(separated_dest_dir):
                        shutil.rmtree(separated_dest_dir)
                    os.makedirs(os.path.dirname(separated_dest_dir), exist_ok=True)
                    shutil.copytree(separated_source_dir, separated_dest_dir)
                    jobs[job_id]['log'].append(f"Separated audio files saved.")

                jobs[job_id]['log'].append(f"Transcription completed.")
                
            except Exception as e:
                jobs[job_id]['log'].append(f"Error processing {url}: {str(e)}")
            finally:
                # Cleanup Demucs temp files for this track
                if temp_demucs_dir and os.path.exists(temp_demucs_dir):
                    try:
                        shutil.rmtree(temp_demucs_dir)
                    except Exception as e:
                        print(f"Failed to clean up temp dir {temp_demucs_dir}: {e}")
                
        # 3. Zip Results
        jobs[job_id]['status'] = "Creating ZIP archive..."
        jobs[job_id]['progress'] = 90
        
        zip_filename = f"{job_id}_results.zip"
        zip_path = os.path.join(app.config['RESULTS_FOLDER'], zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(job_dir):
                for file in files:
                    # Only include files that are not the zip itself (though zip is in RESULTS_FOLDER, not job_dir)
                    # And ensure we are not zipping any leftover temp folders if walk goes into them (though we tried to delete)
                    zipf.write(os.path.join(root, file), file)
                    
        jobs[job_id]['progress'] = 100
        jobs[job_id]['status'] = "Done!"
        jobs[job_id]['download_url'] = f"/download/{zip_filename}"
        jobs[job_id]['done'] = True
        
    except Exception as e:
        jobs[job_id]['error'] = str(e)
        jobs[job_id]['done'] = True
        jobs[job_id]['status'] = "Failed"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        job_id = str(uuid.uuid4())
        filename = f"{job_id}_{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Initialize job
        jobs[job_id] = {
            'status': 'Uploaded',
            'progress': 0,
            'log': [],
            'done': False
        }
        
        # Start processing in background thread
        thread = threading.Thread(target=process_file, args=(job_id, file_path))
        thread.start()
        
        return jsonify({'job_id': job_id})

@app.route('/progress/<job_id>')
def progress(job_id):
    def generate():
        while True:
            if job_id not in jobs:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break
                
            job = jobs[job_id]
            
            # Construct data payload
            data = {
                'status': job.get('status'),
                'progress': job.get('progress'),
                'log': job.get('log', [])[-1] if job.get('log') else None, # clear log to avoid sending history repeatedly? No, frontend handles append.
                # Actually, simpler to just send latest log line if it's new, but for simplicity let's rely on frontend logic
                'done': job.get('done'),
                'download_url': job.get('download_url'),
                'error': job.get('error')
            }
            
            yield f"data: {json.dumps(data)}\n\n"
            
            if job.get('done'):
                break
                
            time.sleep(1) # Poll interval
            
    return Response(generate(), mimetype='text/event-stream')

@app.route('/download/<filename>')
def download_result(filename):
    return send_file(os.path.join(app.config['RESULTS_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
