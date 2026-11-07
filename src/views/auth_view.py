from flask import Blueprint, request, render_template, session, redirect, url_for,Response
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
        email = request.form.get("email")
        user = UserModel.objects(email=email)
        if len(user) > 0:
            return render_template("register.html", error="User with this email exists.")
        first_name = request.form.get("firstName")
        last_name = request.form.get("lastName")
        password = request.form.get("password")
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
    except Exception as err:
        return render_template("register.html", error=str(err))


@auth_blueprint.route("/logout",methods=["DELETE"])
def logout():
    session.clear()
    # return to client success
    return Response(status=200)
