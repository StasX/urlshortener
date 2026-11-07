from flask import Flask, render_template
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


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def catch_all(error):
    return render_template("500.html"), 500
