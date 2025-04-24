from app import create_app
import socket
import threading
import webview
import requests
import time

app = create_app()


def get_free_port():
    """Find an available port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def run_flask(port):
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)


def wait_for_server(url, timeout=10):
    for _ in range(timeout * 10):
        try:
            requests.get(url)
            return True
        except Exception:
            time.sleep(0.1)
    return False


if __name__ == "__main__":
    # Get your local IP
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    # Get a free port dynamically
    port = get_free_port()
    url = f"http://{local_ip}:{port}"

    # Run Flask in a thread
    flask_thread = threading.Thread(target=run_flask, args=(port,))
    flask_thread.daemon = True
    flask_thread.start()

    # Wait for server and show PyWebView
    if wait_for_server(url):
        webview.create_window("SP-14 Chess AI", url, width=1024, height=768)
        webview.start()
    else:
        print("Error: Flask server did not start in time.")
