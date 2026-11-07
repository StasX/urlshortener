from flask import Blueprint, request, render_template, session, redirect, jsonify, Response
import http.client
from utils.url_resolver import InvalidPublicURL, resolve_public_url
from utils.url_validation import validate_destination_url
from utils.auth import login_required
from random import choice
from string import ascii_letters, digits
from models.url_model import UrlModel
from models.user_model import UserModel
from mongoengine import DoesNotExist


home_blueprint = Blueprint("home_view", __name__)


@home_blueprint.route("/")
@home_blueprint.route("/home")
def render():
    return render_template("home.html")


@home_blueprint.route("/geturl", methods=["POST"])
def get_url():
    url = request.form.get("url")
    try:
        return jsonify({"url": resolve_public_url(url)})
    except InvalidPublicURL as error:
        return jsonify({"error": str(error)}), 400
    except TimeoutError:
        return jsonify({"error": "Destination timed out."}), 504
    except (OSError, http.client.HTTPException, UnicodeError, ValueError):
        return jsonify({"error": "Could not retrieve the destination URL."}), 502


@home_blueprint.route("/short", methods=["POST"])
@login_required(api=True)
def short_it():
    try:
        full_url = validate_destination_url(request.form.get("url"))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    user_id = session["current_user"]["id"]
    user_model = UserModel.objects.get(id=user_id)
    chars = ascii_letters+digits
    short_url = None
    run_again = True
    while run_again:
        short_string = ''.join(choice(chars) for _ in range(6))
        short_url = f"http://{request.host}/{short_string}"
        if (len(UrlModel.objects(short_url=short_url)) == 0):
            url_model = UrlModel(short_url=short_url,
                                 full_url=full_url, user=user_model).save()
            run_again = False
    return jsonify({"url": short_url})


@home_blueprint.route("/<url_part>")
def redirect_to(url_part):
    try:
        if url_part != "favicon.ico":
            short_url = f"http://{request.host}/{url_part}"
            url_model = UrlModel.objects.get(short_url=short_url)
            UrlModel.objects(short_url=short_url).update_one(
                enters=url_model.enters+1)
            return redirect(url_model.full_url)
        return Response(status=200)
    except DoesNotExist:
        return render_template("404.html"), 404
