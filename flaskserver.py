from flask import Flask, request, send_file, render_template, jsonify
import os
import random
import string
import sqlite3

app = Flask(__name__, static_folder="static", template_folder="templates")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Database
def init_db():
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_pins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pin TEXT,
            filename TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()  # Ensure DB is initialized

def generate_pin():
    return ''.join(random.choices(string.digits, k=6))  # 6-digit PIN

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    uploaded_files = request.files.getlist("file")  # Allow multiple files
    pin = request.form.get("pin")  # Use existing PIN if provided, else generate a new one

    if not pin:
        pin = generate_pin()

    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()

    for uploaded_file in uploaded_files:
        if uploaded_file.filename == '':
            continue

        destination_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
        uploaded_file.save(destination_path)

        # Store the PIN and filename in SQLite
        cursor.execute("INSERT INTO file_pins (pin, filename) VALUES (?, ?)", (pin, uploaded_file.filename))

    conn.commit()
    conn.close()

    return jsonify({"message": "Files uploaded successfully", "pin": pin}), 200

@app.route('/get-files', methods=['POST'])
def get_files():
    data = request.json
    pin = data.get("pin")

    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM file_pins WHERE pin=?", (pin,))
    results = cursor.fetchall()
    conn.close()

    if results:
        filenames = [row[0] for row in results]
        file_links = [{"filename": f, "download_url": f"/download/{f}"} for f in filenames]
        return jsonify({"files": file_links}), 200
    else:
        return jsonify({"error": "Invalid PIN"}), 400

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
