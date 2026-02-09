const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const progressContainer = document.getElementById('progress-container');
const resultContainer = document.getElementById('result-container');
const progressBarFill = document.getElementById('progress-bar');
const statusText = document.getElementById('status-text');
const percentageText = document.getElementById('percentage');
const logContainer = document.getElementById('log-container');
const downloadBtn = document.getElementById('download-btn');

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
});

dropZone.addEventListener('drop', handleDrop, false);
fileInput.addEventListener('change', handleFiles, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles({ target: { files: files } });
}

function handleFiles(e) {
    const files = e.target.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

function uploadFile(file) {
    // Basic validation
    const validExtensions = ['.xlsx', '.xls', '.csv'];
    const fileName = file.name.toLowerCase();
    
    if (!validExtensions.some(ext => fileName.endsWith(ext))) {
        alert('Please upload a valid Excel or CSV file.');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    // Swap UI to progress view
    dropZone.classList.add('hidden');
    progressContainer.classList.remove('hidden');
    
    // Clear logs
    logContainer.innerHTML = '';
    
    // Create EventSource for progress updates BEFORE starting upload
    // We'll use a unique ID for the session/task if possible, or just listen to global updates for this demo
    // For simplicity in this demo, we'll start the upload and then listen for SSE on a specific channel if the backend supports it,
    // OR we can just use the response from the upload if it's a long-polling request, 
    // BUT since we need real-time updates for a long process, we'll use a fetch to start, and an EventSource for updates.
    
    // Actually, a simpler way for a demo: POST returns a job ID, then we subscribe to SSE with that job ID.

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        const jobId = data.job_id;
        
        // Start listening for progress
        const eventSource = new EventSource(`/progress/${jobId}`);
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            // Update Progress Bar
            if (data.progress) {
                const percent = Math.round(data.progress);
                progressBarFill.style.width = percent + '%';
                percentageText.innerText = percent + '%';
            }
            
            // Update Status Text
            if (data.status) {
                statusText.innerText = data.status;
            }
            
            // Add Log
            if (data.log) {
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                logEntry.innerText = `> ${data.log}`;
                logContainer.appendChild(logEntry);
                logContainer.scrollTop = logContainer.scrollHeight;
            }
            
            // Handle Completion
            if (data.done) {
                eventSource.close();
                setTimeout(() => {
                    progressContainer.classList.add('hidden');
                    resultContainer.classList.remove('hidden');
                    if (data.download_url) {
                        downloadBtn.href = data.download_url;
                    }
                }, 1000);
            }
            
            // Handle Error
            if (data.error) {
                eventSource.close();
                statusText.innerText = "Error Occurred";
                statusText.style.color = "#ff7675";
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry log-error';
                logEntry.innerText = `ERROR: ${data.error}`;
                logContainer.appendChild(logEntry);
            }
        };
        
        eventSource.onerror = function() {
            // eventSource.close();
            // console.error("EventSource failed.");
        };
    })
    .catch(error => {
        console.error('Error:', error);
        statusText.innerText = "Upload Failed";
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry log-error';
        logEntry.innerText = `Network Error: ${error.message}`;
        logContainer.appendChild(logEntry);
    });
}
