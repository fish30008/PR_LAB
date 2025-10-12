import sys
import os
import socket
from urllib.parse import urlparse
from html.parser import HTMLParser

BUFFER_SIZE = 4096

def http_get(host, port, path):

    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        clientSocket.connect((host, port))
    except socket.error as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
    clientSocket.send(request.encode())

    response = b""
    while True:
        chunk = clientSocket.recv(BUFFER_SIZE)
        if not chunk:
            break
        response += chunk

    clientSocket.close()
    return response


def save_file(data, save_path):
    """Save binary data to disk."""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(data)
    print(f"Saved: {save_path}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python client.py <FULL_URL> <SAVE_DIRECTORY>")
        sys.exit(1)

    url = sys.argv[1]
    save_dir = sys.argv[2]

    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or 1337
    path = parsed.path or "/"

    print(f"Connected {host}:{port}")
    response = http_get(host, port, path)

    header_data, _, body = response.partition(b"\r\n\r\n")
    headers = header_data.decode(errors="ignore")

    # Check for 404 or errors
    if "404 Not Found" in headers:
        print(f"File not found on {host}:{port}{path}")
        sys.exit(1)

    # Detect content type
    content_type = "application/octet-stream"
    for h in headers.split("\r\n"):
        if h.lower().startswith("content-type:"):
            content_type = h.split(":", 1)[1].strip()
            break

    # Derive filename and create save path
    filename = os.path.basename(path.rstrip("/")) or "downloaded_file"
    subdirs = os.path.dirname(path.lstrip("/"))
    final_dir = os.path.join(save_dir, subdirs)
    os.makedirs(final_dir, exist_ok=True)
    save_path = os.path.join(final_dir, filename)

    save_file(body, save_path)
    print(f"Saved: {save_path}")


if __name__ == "__main__":
    main()
