from flask import Flask


def create_app():
    app = Flask(__name__)

    from .routes import main

    app.register_blueprint(main)
    app.secret_key = "dev1234"  # CHANGE THIS WHEN FINISHED

    @app.template_filter("chr")
    def chr_filter(val):
        return chr(97 + val)

    return app
