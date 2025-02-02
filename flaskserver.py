from flask import Flask, request, send_file, render_template, jsonify
from flask_socketio import SocketIO, emit
import os
import random
import string
import sqlite3


app = Flask(__name__, static_folder="static", template_folder="templates")
socketio = SocketIO(app)  # Initialize SocketIO with your app
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

init_db()

def generate_pin():
    return ''.join(random.choices(string.digits, k=6))  # 6-digit PIN

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-files', methods=['POST'])
def get_files():
    data = request.json
    pins = data.get("pins", [])

    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()

    file_data = {}
    for pin in pins:
        cursor.execute("SELECT filename FROM file_pins WHERE pin=?", (pin,))
        results = cursor.fetchall()
        file_data[pin] = [{"filename": row[0], "download_url": f"/download/{row[0]}"} for row in results]

    conn.close()
    return jsonify({"files": file_data}), 200

@app.route('/move-file', methods=['POST'])
def move_file():
    data = request.json
    filename = data.get("filename")
    from_pin = data.get("from_pin")
    to_pin = data.get("to_pin")

    if not filename or not from_pin or not to_pin:
        return jsonify({"error": "Missing required data"}), 400

    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM file_pins WHERE pin=? AND filename=?", (from_pin, filename))
    cursor.execute("INSERT INTO file_pins (pin, filename) VALUES (?, ?)", (to_pin, filename))

    conn.commit()
    conn.close()
    emit('move_files', {'fromPin': from_pin, 'toPin': to_pin, 'filename': filename}, broadcast=True, namespace = "/")

    return jsonify({"message": "File moved successfully"}), 200

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(file_path, as_attachment=True)

@app.route('/remove-files', methods=['POST'])
def remove_files():
    data = request.json
    pin = data.get("pin")

    if not pin:
        return jsonify({"error": "Missing PIN"}), 400

    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()

    # Get all the files associated with the PIN
    cursor.execute("SELECT filename FROM file_pins WHERE pin=?", (pin,))
    files = cursor.fetchall()

    # Delete the files from the uploads directory
    for file in files:
        file_path = os.path.join(UPLOAD_FOLDER, file[0])
        if os.path.exists(file_path):
            os.remove(file_path)

    # Delete the records from the database
    cursor.execute("DELETE FROM file_pins WHERE pin=?", (pin,))

    conn.commit()
    conn.close()

    return jsonify({"message": "Files and PIN removed successfully"}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    uploaded_file = request.files['file']
    pin = request.form.get('pin')  # Get the PIN associated with the file

    # Debugging: Check if pin is None or empty
    if not pin:
        # Generate a new PIN if no PIN is provided in the form (for new viewers)
        pin = generate_pin()
        print("pin : ", pin)

    if uploaded_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    print("test see pin : ", pin)

    destination_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
    uploaded_file.save(destination_path)

    # Store the file info in the database
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO file_pins (pin, filename) VALUES (?, ?)", (pin, uploaded_file.filename))
    conn.commit()
    conn.close()

    # Emit WebSocket event to notify all clients (broadcasting)
    emit('new_file_upload', {'pin': pin, 'filename': uploaded_file.filename}, broadcast=True, namespace = "/")

    return jsonify({'message': 'File uploaded successfully', 'pin': pin}), 200


# WebSocket event handler for new file uploads
@socketio.on('new_file_upload')
def handle_new_file_upload(data):
    pin = data['pin']
    filename = data['filename']
    print("handle upload new file")
    # Notify all connected clients about the new file
    emit('file_uploaded', {'pin': pin, 'filename': filename})

# WebSocket event handler for move files between pin viewers
@socketio.on('move_files')
def handle_move_files(data):
    fromPin = data['fromPin']
    toPin = data['toPin']
    filename = data['filename']
    print("Move files from socketio...")
    app.logger.info("Debugging logger on handle new file upload")
    # Notify all connected clients about the move
    emit('file_moved', {'fromPin': fromPin, 'toPin': toPin, 'filename': filename})

if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
