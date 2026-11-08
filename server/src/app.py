from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from mongoengine import connect
from werkzeug.exceptions import HTTPException

from utils.app_config import AppConfig
from utils.jwt_auth import configure_jwt
from utils.short_links import public_base_url
from views.auth_view import auth_blueprint
from views.dashboard_view import dashboard_blueprint
from views.home_view import home_blueprint

app = Flask(__name__)
app.secret_key = AppConfig.secret_key
app.config["PUBLIC_BASE_URL"] = public_base_url(AppConfig.public_base_url)
app.config["SPA_DEV_ORIGIN"] = AppConfig.spa_dev_origin
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
configure_jwt(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["60 per minute"], storage_uri="memory://")
connect(db=AppConfig.db_name, host=AppConfig.db_host, port=AppConfig.db_port)
app.register_blueprint(auth_blueprint)
app.register_blueprint(home_blueprint)
app.register_blueprint(dashboard_blueprint)
for endpoint in ("auth_view.login", "auth_view.register", "home_view.short_it", "home_view.get_url"):
    app.view_functions[endpoint] = limiter.limit("4 per minute")(app.view_functions[endpoint])

frontend_directory = Path(__file__).resolve().parent / "frontend"


@app.get("/health")
@limiter.exempt
def health():
    return {"status": "ok"}


@app.get("/")
@app.get("/home")
@app.get("/login")
@app.get("/register")
@app.get("/dashboard")
@limiter.exempt
def spa():
    return send_from_directory(frontend_directory, "index.html")


@app.get("/assets/<path:filename>")
@limiter.exempt
def frontend_asset(filename):
    return send_from_directory(frontend_directory / "assets", filename)


@app.after_request
def response_headers(response):
    if request.path.startswith("/api/") or request.endpoint == "spa":
        response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.errorhandler(HTTPException)
def http_error(error):
    response = error.get_response()
    message = "Too many requests. Please wait a minute and try again." if error.code == 429 else error.description
    if request.path.startswith("/api/"):
        response.data = app.json.dumps({"error": message})
        response.content_type = "application/json"
    else:
        response.data = render_template("error.html", error_code=error.code,
                                        error_title=error.name, error_message=message)
        response.content_type = "text/html; charset=utf-8"
    return response


@app.errorhandler(500)
def server_error(error):
    if request.path.startswith("/api/"):
        return jsonify(error="We couldn't complete your request. Please try again."), 500
    return render_template("500.html"), 500
