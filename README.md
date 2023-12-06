# upload_download

## Pre: 
> pip install flask


## This Flask application has two endpoints:

    - /upload - Accepts a file upload via a POST request.
    - /download/<filename> - Allows downloading a file by specifying the filename in the URL.

Create an uploads directory in the same folder as flaskserver.py to store the uploaded files.

To run the server, execute the following command in the terminal:

> python app.py


## Upload file 
> curl -X POST -F "file=@/path/to/your/file.txt" http://127.0.0.1:5000/upload

## Donwload file will be message as a response
> curl -OJ http://127.0.0.1:5000/download/file.txt


