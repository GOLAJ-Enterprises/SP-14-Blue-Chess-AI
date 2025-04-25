import threading
import logging

import webview
from waitress import serve
from app import create_app


def run_server():
    # Silence Waitress queue-depth warnings
    logging.getLogger("waitress.queue").setLevel(logging.ERROR)

    # Create Flask app in production mode
    app = create_app()
    app.config.update(
        DEBUG=False,
        TESTING=False,
    )

    host = "127.0.0.1"
    port = 5000

    print("Starting Chess Server (production mode)")
    print(f"Local access only: http://{host}:{port}")

    # Serve with Waitress on localhost only,
    # bump threads so it won't hit queue-depth warnings
    server_thread = threading.Thread(
        target=lambda: serve(
            app,
            host=host,
            port=port,
            threads=8,
            connection_limit=100,
        ),
        daemon=True,
    )
    server_thread.start()

    # Open in a native window
    webview.create_window(
        "Chess",
        f"http://{host}:{port}",
        resizable=True,
        width=1024,
        height=768,
        confirm_close=True,
    )
    webview.start()


if __name__ == "__main__":
    run_server()
