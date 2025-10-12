# import socket module
from socket import *
import sys
import os
import mimetypes

serverSocket = socket(AF_INET, SOCK_STREAM)
CONTENT_DIR = os.path.abspath('.')  # always serve from current working dir

# Prepare a socket
serverPort = 1337
serverSocket.bind(('', serverPort))
serverSocket.listen(2)
print(f"Server is listening on port {serverPort}, Serving: {os.path.abspath(CONTENT_DIR)}")


def generate_directory_listing(dir_path, request_path):
    items = os.listdir(dir_path)
    body = [
        f"<html><head><title>Directory listing for {request_path}</title></head><body>",
        f"<h1>Directory listing for {request_path}</h1>",
        "<ul>",
    ]

    # Link to parent directory if not root
    if request_path != "/":
        parent = os.path.dirname(request_path.rstrip("/"))
        if not parent:
            parent = "/"
        body.append(f'<li><a href="{parent}">Parent Directory</a></li>')

    if not items:
        body.append("<li><em>(empty directory)</em></li>")
    else:
        for name in sorted(items):
            full_path = os.path.join(dir_path, name)
            display_name = name + "/" if os.path.isdir(full_path) else name
            href = os.path.join(request_path.rstrip("/"), name)
            if os.path.isdir(full_path):
                href += "/"
            body.append(f'<li><a href="{href}">{display_name}</a></li>')

    body.append("</ul></body></html>")
    return "\n".join(body)



while True:
    print('Ready to serve...')
    try:
        connectionSocket, addr = serverSocket.accept()
        raw_data = connectionSocket.recv(4096)

        try:
            message = raw_data.split(b"\r\n")[0].decode("utf-8", errors="ignore")
        except UnicodeDecodeError:
            message = ''

        print(f"Received message: {message}")

        if not message:
            connectionSocket.close()
            continue

        filename = message.split()[1]

        # Serve base directory on root request
        # if filename == '/':
        #     body = generate_directory_listing(CONTENT_DIR, '/')
        #     header = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
        #     connectionSocket.send(header.encode() + body.encode())
        #     connectionSocket.close()
        #     continue

        if filename == '/':
            dir_to_list = CONTENT_DIR
        else:
            dir_to_list = os.path.join(CONTENT_DIR, filename.strip("/"))
        file_path = os.path.join(CONTENT_DIR, filename.strip("/"))

        if os.path.isdir(file_path):
            body = generate_directory_listing(file_path, filename)
            header = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
            connectionSocket.send(header.encode() + body.encode())

        else:
            if not os.path.exists(file_path):
                raise IOError

            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = "application/octet-stream"

            with open(file_path, "rb") as f:
                file_data = f.read()

            header = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\n\r\n"
            connectionSocket.send(header.encode() + file_data)

        connectionSocket.close()

    except IOError:
        error_header = "HTTP/1.1 404 Not Found\r\n\r\n"
        error_message = "<html><body><h1>404 Not Found</h1></body></html>\r\n"
        connectionSocket.send(error_header.encode() + error_message.encode())
        connectionSocket.close()

    except Exception as e:
        print(f"Error: {e}")
        connectionSocket.close()
