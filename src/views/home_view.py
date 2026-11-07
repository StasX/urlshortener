from flask import Blueprint, request, render_template, session, redirect, jsonify, Response, current_app
import http.client
from utils.url_resolver import InvalidPublicURL, resolve_public_url
from utils.url_validation import validate_destination_url
from utils.auth import login_required
from utils.short_links import public_base_url
from secrets import choice
from string import ascii_letters, digits
from models.url_model import UrlModel
from models.user_model import UserModel
from mongoengine import NotUniqueError


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
    base_url = public_base_url(current_app.config.get("PUBLIC_BASE_URL", "http://localhost:5000"))
    for _ in range(10):
        short_string = ''.join(choice(chars) for _ in range(6))
        short_url = f"{base_url}/{short_string}"
        try:
            UrlModel(code=short_string, short_url=short_url,
                     full_url=full_url, user=user_model).save()
        except NotUniqueError:
            continue
        return jsonify({"url": short_url})
    return jsonify({"error": "Could not allocate a short URL. Please try again."}), 503


@home_blueprint.route("/<url_part>")
def redirect_to(url_part):
    if url_part == "favicon.ico":
        return Response(status=200)
    url_model = UrlModel.objects(code=url_part).modify(inc__enters=1, new=True)
    if url_model is None:
        return render_template("404.html"), 404
    return redirect(url_model.full_url)
