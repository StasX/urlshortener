from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId
from flask import Flask
from flask_jwt_extended import create_access_token, decode_token

from utils import jwt_auth
from views.auth_view import auth_blueprint
from views.dashboard_view import dashboard_blueprint
from views.home_view import home_blueprint


def make_app(testcase, csrf=False):
    app = Flask(__name__, template_folder=str(Path(jwt_auth.__file__).resolve().parents[1] / "templates"))
    app.config.update(TESTING=True, SECRET_KEY="test-only-key-" * 4,
                      PUBLIC_BASE_URL="https://short.example", JWT_COOKIE_SECURE=False,
                      JWT_COOKIE_CSRF_PROTECT=csrf)
    jwt_auth.configure_jwt(app)
    app.add_url_rule("/", endpoint="spa", view_func=lambda: "SPA")
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(home_blueprint)
    app.register_blueprint(dashboard_blueprint)
    revoked = patch("utils.jwt_auth.RevokedToken.objects")
    testcase.revoked = revoked.start()
    testcase.revoked.return_value.first.return_value = None
    testcase.addCleanup(revoked.stop)
    user = SimpleNamespace(id=ObjectId("507f1f77bcf86cd799439012"),
                           first_name="Test", last_name="User", email="test@example.com")
    users = patch("utils.jwt_auth.UserModel.objects")
    testcase.users = users.start()
    testcase.users.return_value.first.return_value = user
    testcase.addCleanup(users.stop)
    return app, app.test_client(), user


def authenticate(app, client, identity, **options):
    with app.app_context():
        token = create_access_token(identity=str(identity), **options)
        csrf = decode_token(token, allow_expired=True).get("csrf", "")
    client.set_cookie("access_token_cookie", token, path="/api/")
    client.set_cookie("csrf_access_token", csrf)
    return {"X-CSRF-TOKEN": csrf}
