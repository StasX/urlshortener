from datetime import timedelta
from functools import wraps

from bson import ObjectId
from flask import current_app, g, jsonify, request
from flask_jwt_extended import JWTManager, get_jwt_identity, unset_jwt_cookies, verify_jwt_in_request

from models.revoked_token_model import RevokedToken
from models.user_model import UserModel


def configure_jwt(app):
    app.config.setdefault("JWT_SECRET_KEY", app.secret_key)
    app.config.setdefault("JWT_TOKEN_LOCATION", ["cookies"])
    app.config.setdefault("JWT_ACCESS_TOKEN_EXPIRES", timedelta(hours=1))
    app.config.setdefault("JWT_COOKIE_SECURE", app.config.get("PUBLIC_BASE_URL", "").startswith("https://"))
    app.config.setdefault("JWT_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("JWT_COOKIE_CSRF_PROTECT", True)
    app.config.setdefault("JWT_ACCESS_COOKIE_PATH", "/api/")
    jwt = JWTManager(app)

    def denied(message):
        response = jsonify(error=message)
        response.status_code = 401
        unset_jwt_cookies(response)
        return response

    jwt.unauthorized_loader(lambda reason: (jsonify(error="Authentication required."), 401))
    jwt.invalid_token_loader(lambda reason: denied("Your sign-in is invalid. Please sign in again."))
    jwt.expired_token_loader(lambda header, payload: denied("Your sign-in has expired. Please sign in again."))
    jwt.revoked_token_loader(lambda header, payload: denied("You have signed out. Please sign in again."))

    @jwt.token_in_blocklist_loader
    def is_revoked(header, payload):
        return RevokedToken.objects(jti=payload["jti"]).first() is not None

    # JWT cookies are protected by double-submit CSRF tokens. Check Origin as
    # well for login/registration, before any authenticated cookie exists.
    @app.before_request
    def check_origin():
        if request.path.startswith("/api/") and request.method not in ("GET", "HEAD", "OPTIONS"):
            origin = request.headers.get("Origin")
            allowed = {current_app.config["PUBLIC_BASE_URL"], current_app.config.get("SPA_DEV_ORIGIN", "")}
            if origin and origin.rstrip("/") not in allowed:
                return jsonify(error="This request came from an untrusted origin."), 403


def login_required(*, optional=False):
    def decorate(view):
        @wraps(view)
        def guarded(*args, **kwargs):
            verified = verify_jwt_in_request(optional=optional)
            identity = get_jwt_identity()
            g.current_user = None
            if verified is not None:
                if isinstance(identity, str) and ObjectId.is_valid(identity):
                    g.current_user = UserModel.objects(id=identity).first()
                if g.current_user is None:
                    return jsonify(error="Your account is no longer available. Please sign in again."), 401
            return view(*args, **kwargs)
        return guarded
    return decorate


def user_data(user):
    return {"id": str(user.id), "first_name": user.first_name,
            "last_name": user.last_name, "email": user.email}
