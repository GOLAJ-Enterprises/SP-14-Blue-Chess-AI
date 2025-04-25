import logging
import webbrowser
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

    # Open default browser
    try:
        webbrowser.open(f"http://{host}:{port}")
    except Exception:
        pass

    # Serve with Waitress on localhost only
    serve(app, host=host, port=port, threads=8, connection_limit=100)


if __name__ == "__main__":
    run_server()
