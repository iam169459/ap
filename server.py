import os
from flask import Flask, request

app = Flask(__name__)
UPLOAD_FOLDER = "received_backups"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_chunk():
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    # Save the chunk directly into the upload folder
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    
    print(f"Received and saved chunk: {file.filename}")
    return "Chunk received successfully", 200

if __name__ == '__main__':
    # Listen on all interfaces so Tailscale can route traffic to it on port 5000
    app.run(host='0.0.0.0', port=5001)