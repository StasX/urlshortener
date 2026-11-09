from flask import Blueprint, request, render_template, g, redirect, jsonify, current_app
import http.client
from utils.url_resolver import InvalidPublicURL, resolve_public_url
from utils.url_validation import validate_destination_url
from datetime import datetime, timedelta, timezone
from utils.short_links import public_base_url
from secrets import choice
from string import ascii_letters, digits
from models.url_model import UrlModel
from utils.jwt_auth import login_required
from utils.realtime import notify_links_changed
from mongoengine import NotUniqueError, Q


home_blueprint = Blueprint("home_view", __name__)


@home_blueprint.route("/api/resolve", methods=["POST"])
def get_url():
    data = request.get_json()
    url = data.get("url") if isinstance(data, dict) else None
    try:
        return jsonify({"url": resolve_public_url(url)})
    except InvalidPublicURL as error:
        return jsonify({"error": str(error)}), 400
    except TimeoutError:
        return jsonify({"error": "Destination timed out."}), 504
    except (OSError, http.client.HTTPException, UnicodeError, ValueError):
        return jsonify({"error": "Could not retrieve the destination URL."}), 502


@home_blueprint.route("/api/links", methods=["POST"])
@login_required(optional=True)
def short_it():
    data = request.get_json()
    try:
        full_url = validate_destination_url(data.get("url") if isinstance(data, dict) else None)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    user_model = g.current_user
    expires_at = None if user_model else datetime.now(timezone.utc) + timedelta(hours=24)
    chars = ascii_letters+digits
    base_url = public_base_url(current_app.config.get("PUBLIC_BASE_URL", "http://localhost:5000"))
    for _ in range(10):
        short_string = ''.join(choice(chars) for _ in range(6))
        if short_string == "health":
            continue
        short_url = f"{base_url}/{short_string}"
        try:
            UrlModel(code=short_string, short_url=short_url,
                     full_url=full_url, user=user_model, expires_at=expires_at).save()
        except NotUniqueError:
            continue
        if user_model:
            notify_links_changed(user_model.id)
        return jsonify({"url": short_url})
    return jsonify({"error": "Could not allocate a short URL. Please try again."}), 503


@home_blueprint.route("/<url_part>")
def redirect_to(url_part):
    url_model = UrlModel.objects(code=url_part).filter(
        Q(expires_at=None) | Q(expires_at__gt=datetime.now(timezone.utc))
    ).modify(inc__enters=1, new=True)
    if url_model is None:
        return render_template("404.html"), 404
    notify_links_changed(url_model.to_mongo().get("user"))
    return redirect(url_model.full_url)
