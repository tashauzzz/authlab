# authlab/__init__.py

from flask import Flask, request, session
from werkzeug.exceptions import HTTPException

from authlab.core import SECRET_KEY, json_err, api_error, log_attempt
from authlab.api import api_bp
from authlab.web import web_bp

API_PREFIX = "/api/v1"


def create_app():
    """Flask application factory."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix=API_PREFIX)
    app.register_blueprint(web_bp)

    # --- Error handlers ---

    @app.errorhandler(404)
    def _h404(e):
        if request.path.startswith(API_PREFIX):
            return api_error("not_found")
        return e

    @app.errorhandler(405)
    def _h405(e):
        if request.path.startswith(API_PREFIX):
            return api_error("method_not_allowed")
        return e

    @app.errorhandler(Exception)
    def _h500(e):
        if request.path.startswith(API_PREFIX):
            # Normalize HTTPException into JSON error envelope
            if isinstance(e, HTTPException):
                code = e.code or 500
                if code == 401:
                    return api_error("unauthorized")
                if code == 404:
                    return api_error("not_found")
                if code == 405:
                    return api_error("method_not_allowed")
                return json_err(str(code), e.name or "Error", status=code)

            # Unexpected error 500 + log
            log_attempt(
                session.get("user"),
                bool(session.get("user")),
                "api_error",
                "server_error",
                route=request.path,
                meta={"type": type(e).__name__},
            )
            return api_error("server_error")
        raise e

    return app
