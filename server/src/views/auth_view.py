from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, set_access_cookies, unset_jwt_cookies
from mongoengine import NotUniqueError, ValidationError

from models.revoked_token_model import RevokedToken
from models.user_model import UserModel
from utils.jwt_auth import login_required, user_data
from utils.security import Security


auth_blueprint = Blueprint("auth_view", __name__, url_prefix="/api/auth")


def signed_in(user, status=200):
    response = jsonify(user=user_data(user))
    response.status_code = status
    set_access_cookies(response, create_access_token(identity=str(user.id)))
    return response


@auth_blueprint.post("/login")
def login():
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify(error="Provide your email and password."), 400
    email, password = data.get("email"), data.get("password")
    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify(error="Provide your email and password."), 400
    user = UserModel.objects(email=email.strip()).first()
    if not user or not Security.verify(user.password, password):
        return jsonify(error="Email or password is incorrect."), 401
    if Security.needs_rehash(user.password):
        user.password = Security.hash(password)
        user.save()
    return signed_in(user)


@auth_blueprint.post("/register")
def register():
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify(error="Provide your registration details."), 400
    values = {key: data.get(key, "") for key in ("firstName", "lastName", "email", "password", "repeatPassword")}
    if not all(isinstance(value, str) for value in values.values()):
        return jsonify(error="Registration fields must contain text."), 400
    first_name, last_name, email = (values[key].strip() for key in ("firstName", "lastName", "email"))
    errors = []
    for label, value, field_name in (("First name", first_name, "first_name"), ("Last name", last_name, "last_name")):
        field = UserModel._fields[field_name]
        if not field.min_length <= len(value) <= field.max_length:
            errors.append(f"{label} must be between {field.min_length} and {field.max_length} characters.")
    try:
        UserModel._fields["email"].validate(email)
    except ValidationError:
        errors.append("Enter a valid email address (5-64 characters).")
    if not values["password"]:
        errors.append("Enter a password.")
    elif values["password"] != values["repeatPassword"]:
        errors.append("Passwords must match.")
    if errors:
        return jsonify(error=" ".join(errors)), 400
    try:
        user = UserModel(first_name=first_name, last_name=last_name, email=email,
                         password=Security.hash(values["password"])).save()
    except NotUniqueError:
        return jsonify(error="User with this email exists."), 409
    return signed_in(user, 201)


@auth_blueprint.get("/me")
@login_required(optional=True)
def me():
    return jsonify(user=user_data(g.current_user) if g.current_user else None)


@auth_blueprint.post("/logout")
@login_required()
def logout():
    token = get_jwt()
    RevokedToken.objects(jti=token["jti"]).update_one(
        upsert=True, set__expires_at=datetime.fromtimestamp(token["exp"], timezone.utc))
    response = jsonify(message="Signed out.")
    unset_jwt_cookies(response)
    return response
