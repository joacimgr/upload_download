from flask import Flask, request, send_file
import socket
app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part in the request', 400

    uploaded_file = request.files['file']

    if uploaded_file.filename == '':
        return 'No selected file', 400

    # Specify the destination directory and file name
    destination_path = "uploads/" + uploaded_file.filename

    # Save the uploaded file
    uploaded_file.save(destination_path)

    return 'File uploaded successfully\nTo download it post in terminal: \n\ncurl -OJ http://' + get_ip() + ':5000/download/' + uploaded_file.filename + '.txt', 200

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    # Specify the path to the file
    file_path = "uploads/" + filename

    # Send the file for download
    return send_file(file_path, as_attachment=True)

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
    print(get_ip())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) # Private network
    #app.run(debug=True) # Loacally

