# server_threaded.py
from socket import *
import threading
import time
import os
import mimetypes
from collections import deque


CONTENT_DIR = os.path.abspath('.')
serverPort = 1337


REQUEST_COUNTS = {}


counter_lock = threading.Lock()


RATE_LIMIT = 5
TIME_WINDOW = 1
RATE_LIMIT_DATA = {}
rate_lock = threading.Lock()

def increment_hit(path, synchronized=False):
    if synchronized:
        with counter_lock:
            REQUEST_COUNTS[path] = REQUEST_COUNTS.get(path, 0) + 1
    else:
        REQUEST_COUNTS[path] = REQUEST_COUNTS.get(path, 0) + 1


def is_rate_limited(client_ip):

    now = time.time()
    with rate_lock:
        if client_ip not in RATE_LIMIT_DATA:
            RATE_LIMIT_DATA[client_ip] = deque()

        q = RATE_LIMIT_DATA[client_ip]
        # Remove timestamps older than TIME_WINDOW
        while q and now - q[0] > TIME_WINDOW:
            q.popleft()

        if len(q) >= RATE_LIMIT:
            # Still within the limit window — block request
            return True
        else:
            q.append(now)
            return False


def generate_directory_listing(dir_path, request_path, synchronized=False):
    items = os.listdir(dir_path)
    body = [
        f"<html><head><title>Directory listing for {request_path}</title></head><body>",
        f"<h1>Directory listing for {request_path}</h1>",
        "<table border='1' cellspacing='0' cellpadding='5'>",
        "<tr><th>File/Directory</th><th>Hits</th></tr>"
    ]

    # Link to parent directory if not root
    if request_path != "/":
        parent = os.path.dirname(request_path.rstrip("/")) or "/"
        hits = REQUEST_COUNTS.get(parent, 0)
        body.append(f"<tr><td><a href='{parent}'>Parent Directory</a></td><td>{hits}</td></tr>")

    if not items:
        body.append("<tr><td colspan='2'><em>(empty directory)</em></td></tr>")
    else:
        for name in sorted(items):
            full_path = os.path.join(dir_path, name)
            display_name = name + "/" if os.path.isdir(full_path) else name
            href = os.path.join(request_path.rstrip("/"), name)
            if os.path.isdir(full_path):
                href += "/"

            # Lookup hit count
            hits = REQUEST_COUNTS.get(href, 0)
            body.append(f"<tr><td><a href='{href}'>{display_name}</a></td><td>{hits}</td></tr>")

    body.append("</table></body></html>")
    return "\n".join(body)


def handle_client(connectionSocket, addr):
    """Handle a single client connection in a separate thread."""
    print(f"Handling connection from {addr}")
    try:
        raw_data = connectionSocket.recv(4096)
        try:
            message = raw_data.split(b"\r\n")[0].decode("utf-8", errors="ignore")
        except UnicodeDecodeError:
            message = ''

        if not message:
            connectionSocket.close()
            return

        filename = message.split()[1]
        file_path = os.path.join(CONTENT_DIR, filename.strip("/"))

        #threada save on of
        USE_SYNC = True
        #time.sleep(1)
        # change to False for naive version
        increment_hit(filename, synchronized=USE_SYNC)

        if os.path.isdir(file_path):
            body = generate_directory_listing(file_path, filename)
            header = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
            connectionSocket.sendall(header.encode() + body.encode())

        else:
            if not os.path.exists(file_path):
                raise IOError

            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = "application/octet-stream"

            with open(file_path, "rb") as f:
                file_data = f.read()

            header = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\n\r\n"
            connectionSocket.sendall(header.encode() + file_data)
    except IOError:
        error_header = "HTTP/1.1 404 Not Found\r\n\r\n"
        error_message = "<html><body><h1>404 Not Found</h1></body></html>\r\n"
        connectionSocket.sendall(error_header.encode() + error_message.encode())
    except Exception as e:
        print(f"Error handling {addr}: {e}")
    finally:
        connectionSocket.close()
        print(f"Closed connection from {addr}")


def main():
    with socket(AF_INET, SOCK_STREAM) as serverSocket:
        serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        serverSocket.bind(('', serverPort))
        serverSocket.listen(5)
        print(f"Threaded server running on port {serverPort}, Serving: {CONTENT_DIR}")

        while True:
            connectionSocket, addr = serverSocket.accept()
            client_ip = addr[0]
            print("Client IP: =========", client_ip)
            print(f"RATE_LIMIT_DATA:{RATE_LIMIT_DATA} -----------")

            if is_rate_limited(client_ip):
                print(f"[RATE-LIMIT] {client_ip} exceeded rate limit")
                header = "HTTP/1.1 429 Too Many Requests\r\nContent-Type: text/html\r\n\r\n"
                body = "<html><body><h1>429 Too Many Requests</h1><p>Slow down!</p></body></html>"
                connectionSocket.send(header.encode() + body.encode())
                connectionSocket.close()
                continue
            client_thread = threading.Thread(target=handle_client, args=(connectionSocket, addr))
            client_thread.daemon = True  # allows program to exit even if threads still alive
            client_thread.start()


if __name__ == "__main__":
    main()
