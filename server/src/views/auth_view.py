from flask import Blueprint, request, render_template, session, redirect, url_for,Response, current_app
from mongoengine import ValidationError, NotUniqueError
from models.user_model import UserModel
from utils.security import Security


auth_blueprint = Blueprint("auth_view", __name__)


@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    # get html
    if request.method == "GET":
        return render_template("login.html")
    # login
    try:
        email = request.form["username"]
        password = request.form["password"]
        user = UserModel.objects(email=email).first()
        if user and Security.verify(user.password, password):
            if Security.needs_rehash(user.password):
                user.password = Security.hash(password)
                user.save()
            session["current_user"] = {
                "id": str(user.id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
            }
            return redirect(url_for("home_view.render"))
        return render_template("login.html", error="Wrong credentials")
    except Exception as err:
        print(err)
        return render_template("login.html", error=str(err))


@auth_blueprint.route("/register", methods=["GET", "POST"])
def register():

    # get html
    if request.method == "GET":
        return render_template("register.html")
    # login
    try:
        email = request.form.get("email", "").strip()
        first_name = request.form.get("firstName", "").strip()
        last_name = request.form.get("lastName", "").strip()
        password = request.form.get("password", "")
        repeat_password = request.form.get("repeatPassword", "")
        errors = []
        for label, value, field_name in (
            ("First name", first_name, "first_name"),
            ("Last name", last_name, "last_name"),
        ):
            field = UserModel._fields[field_name]
            if not field.min_length <= len(value) <= field.max_length:
                errors.append(f"{label} must be between {field.min_length} and {field.max_length} characters.")
        try:
            UserModel._fields["email"].validate(email)
        except ValidationError:
            errors.append("Enter a valid email address (5–64 characters).")
        if not password:
            errors.append("Enter a password.")
        elif password != repeat_password:
            errors.append("Passwords must match.")
        if errors:
            return render_template("register.html", error=" ".join(errors)), 400
        user = UserModel.objects(email=email)
        if len(user) > 0:
            return render_template("register.html", error="User with this email exists.")
        UserModel(first_name=first_name, last_name=last_name,
                  email=email, password=Security.hash(password)).save()
        user = UserModel.objects.get(email=email)
        if user:
            session["current_user"] = {
                "id": str(user.id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
            }
            return redirect(url_for("home_view.render"))
        return render_template("register.html", error="Something went wrong, and user haven't created.")
    except NotUniqueError:
        return render_template("register.html", error="User with this email exists."), 400
    except ValidationError:
        return render_template("register.html", error="Check your registration details and try again."), 400
    except Exception:
        current_app.logger.exception("Registration failed")
        return render_template("register.html", error="Could not create your account. Please try again."), 500


@auth_blueprint.route("/logout",methods=["DELETE"])
def logout():
    session.clear()
    # return to client success
    return Response(status=200)
