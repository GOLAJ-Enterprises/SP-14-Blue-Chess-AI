import socket
import webbrowser
from app import create_app, state


def get_local_ip():
    """Returns the LAN IP address of the host machine."""
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)


def run_dev_server():
    app = create_app()
    local_ip = get_local_ip()
    port = 5000
    host = "0.0.0.0"

    # Print connection info
    print("Starting Chess LAN Server...")
    print(f"LAN access available at: http://{local_ip}:{port}")
    print(f"Local access via: http://localhost:{port}\n")

    # Start listener for LAN game discovery
    state.listen_for_games()

    # Open browser to the actual LAN IP
    try:
        webbrowser.open(f"http://{local_ip}:{port}")
    except Exception:
        pass  # Silent fail if browser can't open

    app.run(host=host, port=port, debug=True)


if __name__ == "__main__":
    run_dev_server()
