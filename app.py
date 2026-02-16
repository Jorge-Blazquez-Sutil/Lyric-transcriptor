import os
import time
import json
import zipfile
import threading
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
            
        urls = df['URL'].dropna().tolist()
        total_urls = len(urls)
        
        if total_urls == 0:
            raise ValueError("No URLs found in the 'URL' column")
            
        jobs[job_id]['log'].append(f"Found {total_urls} URLs to process.")
        
        # Process each URL
        audio_files = []
        
        for i, url in enumerate(urls):
            try:
                # Update progress
                current_idx = i + 1
                progress = 10 + (current_idx / total_urls) * 70 # Allocating 70% of progress to processing
                jobs[job_id]['progress'] = progress
                jobs[job_id]['status'] = f"Processing {current_idx}/{total_urls}: {url}"
                jobs[job_id]['log'].append(f"Downloading: {url}")
                
                # 1. Download Audio
                audio_path = download_audio_from_url(url, job_dir)
                if not audio_path:
                    jobs[job_id]['log'].append(f"Failed to download: {url}")
                    continue
                    
                audio_files.append(audio_path)
                jobs[job_id]['log'].append(f"Downloaded: {os.path.basename(audio_path)}")
                
                # 2. Transcribe Audio
                jobs[job_id]['status'] = f"Transcribing {current_idx}/{total_urls}: {os.path.basename(audio_path)}"
                jobs[job_id]['log'].append(f"Transcribing...")
                

                print(f"[DEBUG] Calling transcribe_audio for {os.path.basename(audio_path)}")
                transcript_text = transcribe_audio(audio_path)
                print(f"[DEBUG] Returned from transcribe_audio")
                
                # Save transcription
                txt_filename = os.path.splitext(os.path.basename(audio_path))[0] + ".txt"
                txt_path = os.path.join(job_dir, txt_filename)
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(transcript_text)
                    
                jobs[job_id]['log'].append(f"Transcription saved.")
                
            except Exception as e:
                jobs[job_id]['log'].append(f"Error processing {url}: {str(e)}")
                
        # 3. Zip Results
        jobs[job_id]['status'] = "Creating ZIP archive..."
        jobs[job_id]['progress'] = 90
        
        zip_filename = f"{job_id}_results.zip"
        zip_path = os.path.join(app.config['RESULTS_FOLDER'], zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(job_dir):
                for file in files:
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
    app.run(debug=True, use_reloader=False)
