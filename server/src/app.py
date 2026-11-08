from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import HTTPException
from mongoengine import connect
from views.auth_view import auth_blueprint
from views.home_view import home_blueprint
from views.dashboard_view import dashboard_blueprint
from utils.app_config import AppConfig
from utils.short_links import public_base_url

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.secret_key = AppConfig.secret_key
app.config["PUBLIC_BASE_URL"] = public_base_url(AppConfig.public_base_url)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["4 per minute"],
    storage_uri="memory://",
)
connect(db=AppConfig.db_name, host=AppConfig.db_host, port=AppConfig.db_port)
# connect(db=AppConfig.db_name, username=AppConfig.db_user,
#         password=AppConfig.db_password, host=AppConfig.db_host, port=AppConfig.db_port)

app.register_blueprint(auth_blueprint)
app.register_blueprint(home_blueprint)
app.register_blueprint(dashboard_blueprint)


@app.route("/health")
@limiter.exempt
def health():
    return {"status": "ok"}, 200


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def catch_all(error):
    if request.endpoint in API_ENDPOINTS:
        return jsonify(error="We couldn't complete your request. Please try again."), 500
    return render_template("500.html"), 500


API_ENDPOINTS = {
    "home_view.get_url", "home_view.short_it", "dashboard_view.stat",
    "dashboard_view.delete_url", "auth_view.logout",
}


@app.errorhandler(HTTPException)
def http_error(error):
    message = ("Too many requests. Please wait a minute and try again."
               if error.code == 429 else error.description)
    response = error.get_response()
    if request.endpoint in API_ENDPOINTS:
        response.data = app.json.dumps({"error": message})
        response.content_type = "application/json"
    elif error.code == 429:
        response.data = render_template("429.html")
        response.content_type = "text/html; charset=utf-8"
    else:
        response.data = render_template(
            "error.html", error_code=error.code,
            error_title=error.name, error_message=message)
        response.content_type = "text/html; charset=utf-8"
    return response
