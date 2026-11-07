from flask import Blueprint, request, render_template, session, redirect, jsonify, Response
import requests
from models.url_model import UrlModel
from models.user_model import UserModel
from mongoengine import DoesNotExist
from random import randint
from utils.auth import login_required
from bson import ObjectId


dashboard_blueprint = Blueprint("dashboard_view", __name__)


@dashboard_blueprint.route("/dashboard")
@login_required()
def render():
    user = session["current_user"]
    urls_models = UrlModel.objects(user=user["id"])
    colors = []
    for i in range(len(urls_models)):
        colors.append([randint(0, 255), randint(0, 255), randint(0, 255)])
    return render_template("dashboard.html", urls_data=urls_models, colors=colors)


@dashboard_blueprint.route("/urls-stat")
@login_required(api=True)
def stat():
    user = session["current_user"]
    urls_models = UrlModel.objects(user=user["id"])
    data = [{
        "id": str(url_model.id),
        "shortUrl": url_model.short_url,
        "fullUrl": url_model.full_url,
        "visits": url_model.enters
    } for url_model in urls_models]
    return jsonify(data)


@dashboard_blueprint.route("/urls/<url_id>", methods=["DELETE"])
@login_required(api=True)
def delete_url(url_id):
    if not ObjectId.is_valid(url_id):
        return jsonify({"error": "Link not found."}), 404
    deleted = UrlModel.objects(id=url_id, user=session["current_user"]["id"]).delete()
    if not deleted:
        return jsonify({"error": "Link not found."}), 404
    return Response(status=204)
